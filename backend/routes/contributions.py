from flask import request, jsonify
from datetime import datetime
import logging

import supabase
from . import contributions_bp
from models import Contribution
from services import get_supabase_client, BitnobService, InvoicePollingService
from services.bitnob import BitnobAPIError
from pydantic import ValidationError

logger = logging.getLogger(__name__)
supabase = get_supabase_client()
bitnob_service = BitnobService()
polling_service = InvoicePollingService()


@contributions_bp.route('', methods=['POST'])
def create_contribution():
    """Create a new contribution and generate payment invoice"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate campaign exists
        campaign_id = data.get('campaign_id')
        campaign_response = supabase.table('campaigns').select('*').eq(
            'id', campaign_id
        ).single().execute()
        
        if not campaign_response.data:
            return jsonify({'error': 'Campaign not found'}), 404
        
        campaign = campaign_response.data
        
        # Check if campaign is active
        if campaign.get('status') != 'active':
            return jsonify({'error': 'Campaign is not active'}), 400
        
        # Create contribution model
        contribution = Contribution(**data)
        contribution.created_at = datetime.now()
        contribution.payment_status = 'pending'
        
        # Create Bitnob payment
        try:
            # Generate unique reference
            import uuid
            reference = f"contrib_{uuid.uuid4().hex[:12]}"
            
            # Determine payment method based on currency
            if contribution.currency in ['BTC', 'SATS']:
                # Use Lightning Network for Bitcoin
                payment_data = bitnob_service.create_lightning_address_payment(
                    amount=contribution.amount if contribution.currency == 'SATS' else contribution.amount * 100000000,
                    description=f"Contribution to {campaign.get('title')}",
                    customer_email=contribution.contributor_email,
                    reference=reference
                )
                
                contribution.bitnob_payment_id = payment_data['payment_id']
                contribution.bitnob_payment_request = payment_data['lightning_invoice']
                contribution.bitnob_payment_hash = payment_data['payment_hash']
            else:
                # Use checkout for fiat currencies
                payment_data = bitnob_service.create_checkout(
                    amount=contribution.amount,
                    currency=contribution.currency,
                    description=f"Contribution to {campaign.get('title')}",
                    customer_email=contribution.contributor_email,
                    reference=reference
                )
                
                contribution.bitnob_payment_id = payment_data['checkout_id']
                contribution.bitnob_payment_request = payment_data['checkout_url']
            
            contribution.bitnob_reference = reference
            
        except BitnobAPIError as e:
            logger.error(f"Bitnob API error: {str(e)}")
            return jsonify({'error': 'Failed to create payment'}), 500
        
        # Insert contribution into database
        contrib_data = contribution.to_dict()
        contrib_data.pop('id', None)
        
        response = supabase.table('contributions').insert(contrib_data).execute()
        
        if not response.data:
            return jsonify({'error': 'Failed to create contribution'}), 500
        
        created_contribution = Contribution.from_dict(response.data[0])
        
        # Start polling for payment
        polling_service.start_polling(
            contribution_id=created_contribution.id,
            payment_id=created_contribution.bitnob_payment_id,
            campaign_id=campaign_id
        )
        
        logger.info(f"Contribution created: {created_contribution.id}")
        
        return jsonify({
            'message': 'Contribution created successfully',
            'contribution': created_contribution.dict(),
            'payment_request': created_contribution.bitnob_payment_request
        }), 201
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except Exception as e:
        logger.error(f"Error creating contribution: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@contributions_bp.route('/<contribution_id>', methods=['GET'])
def get_contribution(contribution_id):
    """Get a specific contribution by ID"""
    try:
        response = supabase.table('contributions').select('*').eq(
            'id', contribution_id
        ).single().execute()
        
        if not response.data:
            return jsonify({'error': 'Contribution not found'}), 404
        
        contribution = Contribution.from_dict(response.data)
        
        # Hide personal info if anonymous
        contrib_dict = contribution.dict()
        if contribution.is_anonymous:
            contrib_dict['contributor_name'] = 'Anonymous'
            contrib_dict['contributor_email'] = None
        
        return jsonify({'contribution': contrib_dict}), 200
        
    except Exception as e:
        logger.error(f"Error fetching contribution: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@contributions_bp.route('/<contribution_id>/status', methods=['GET'])
def check_contribution_status(contribution_id):
    """Check the payment status of a contribution"""
    try:
        response = supabase.table('contributions').select('*').eq(
            'id', contribution_id
        ).single().execute()
        
        if not response.data:
            return jsonify({'error': 'Contribution not found'}), 404
        
        contribution = Contribution.from_dict(response.data)
        
        # If pending and has payment ID, check with Bitnob
        if contribution.is_pending() and contribution.bitnob_reference:
            try:
                payment_status = bitnob_service.verify_payment(
                    contribution.bitnob_reference
                )
                
                # Update if status changed
                if payment_status['paid'] and not contribution.is_paid():
                    update_data = {
                        'payment_status': 'paid',
                        'paid_at': payment_status.get('paid_at'),
                        'transaction_id': payment_status.get('transaction_id'),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    supabase.table('contributions').update(update_data).eq(
                        'id', contribution_id
                    ).execute()
                    
                    contribution.payment_status = 'paid'
                    contribution.paid_at = payment_status.get('paid_at')
                    
            except BitnobAPIError as e:
                logger.error(f"Error checking Bitnob status: {str(e)}")
        
        return jsonify({
            'contribution_id': contribution_id,
            'payment_status': contribution.payment_status,
            'is_paid': contribution.is_paid(),
            'paid_at': contribution.paid_at.isoformat() if contribution.paid_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error checking contribution status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@contributions_bp.route('/<contribution_id>/cancel', methods=['POST'])
def cancel_contribution(contribution_id):
    """Cancel a pending contribution"""
    try:
        response = supabase.table('contributions').select('*').eq(
            'id', contribution_id
        ).single().execute()
        
        if not response.data:
            return jsonify({'error': 'Contribution not found'}), 404
        
        contribution = Contribution.from_dict(response.data)
        
        # Can only cancel pending contributions
        if not contribution.is_pending():
            return jsonify({
                'error': 'Can only cancel pending contributions'
            }), 400
        
        # Cancel Bitnob payment if exists (not all payment types support cancellation)
        if contribution.bitnob_payment_id:
            # Bitnob doesn't have a direct cancel endpoint for lightning payments
            logger.info(f"Payment will expire automatically: {contribution.bitnob_payment_id}")
        
        # Stop polling
        polling_service.stop_polling(contribution_id)
        
        # Update contribution status
        supabase.table('contributions').update({
            'payment_status': 'cancelled',
            'updated_at': datetime.now().isoformat()
        }).eq('id', contribution_id).execute()
        
        logger.info(f"Contribution cancelled: {contribution_id}")
        
        return jsonify({'message': 'Contribution cancelled successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error cancelling contribution: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@contributions_bp.route('', methods=['GET'])
def get_contributions():
    """Get all contributions with optional filtering"""
    try:
        # Get query parameters
        campaign_id = request.args.get('campaign_id')
        payment_status = request.args.get('payment_status')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = supabase.table('contributions').select('*')
        
        if campaign_id:
            query = query.eq('campaign_id', campaign_id)
        
        if payment_status:
            query = query.eq('payment_status', payment_status)
        
        # Execute query with pagination
        response = query.order('created_at', desc=True).range(
            offset, offset + limit - 1
        ).execute()
        
        contributions = response.data
        
        # Filter anonymous contributor info
        for contrib in contributions:
            if contrib.get('is_anonymous'):
                contrib['contributor_name'] = 'Anonymous'
                contrib['contributor_email'] = None
        
        return jsonify({
            'contributions': contributions,
            'count': len(contributions),
            'offset': offset,
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching contributions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@contributions_bp.route('/webhook', methods=['POST'])
def bitnob_webhook():
    """Webhook endpoint for Bitnob payment notifications"""
    try:
        # Get raw payload and signature
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-Bitnob-Signature', '')
        
        # Verify webhook signature
        if not bitnob_service.verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        event_type = data.get('event')
        payment_data = data.get('data', {})
        reference = payment_data.get('reference')
        
        if not reference:
            return jsonify({'error': 'Reference required'}), 400
        
        # Find contribution by reference
        response = supabase.table('contributions').select('*').eq(
            'bitnob_reference', reference
        ).execute()
        
        if not response.data:
            logger.warning(f"No contribution found for reference: {reference}")
            return jsonify({'message': 'Contribution not found'}), 404
        
        contribution_data = response.data[0]
        contribution_id = contribution_data['id']
        campaign_id = contribution_data['campaign_id']
        
        # Update contribution status based on event
        if event_type == 'charge:success' or payment_data.get('status') == 'success':
            update_data = {
                'payment_status': 'paid',
                'paid_at': payment_data.get('paidAt', datetime.now().isoformat()),
                'transaction_id': payment_data.get('transactionId'),
                'updated_at': datetime.now().isoformat()
            }
            
            supabase.table('contributions').update(update_data).eq(
                'id', contribution_id
            ).execute()
            
            # Update campaign amount
            amount = contribution_data['amount']
            campaign_response = supabase.table('campaigns').select(
                'current_amount'
            ).eq('id', campaign_id).single().execute()
            
            if campaign_response.data:
                current_amount = campaign_response.data['current_amount']
                new_amount = current_amount + amount
                
                supabase.table('campaigns').update({
                    'current_amount': new_amount,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', campaign_id).execute()
            
            # Stop polling
            polling_service.stop_polling(contribution_id)
            
            logger.info(f"Webhook: Payment confirmed for {contribution_id}")
        
        elif event_type == 'charge:failed' or payment_data.get('status') == 'failed':
            supabase.table('contributions').update({
                'payment_status': 'failed',
                'updated_at': datetime.now().isoformat()
            }).eq('id', contribution_id).execute()
            
            polling_service.stop_polling(contribution_id)
            logger.info(f"Webhook: Payment failed for {contribution_id}")
        
        return jsonify({'message': 'Webhook processed successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    