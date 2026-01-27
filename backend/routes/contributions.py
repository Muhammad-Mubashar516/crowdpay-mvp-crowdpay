"""
Contribution Routes for CrowdPay

Handles Lightning-only payments via LNbits:
- Create contribution with LNbits invoice
- Check payment status
- Handle LNbits webhooks
- Cancel pending contributions

Payment Flow:
1. POST /api/contributions - Creates contribution + LNbits invoice
2. Frontend displays QR code with BOLT11 invoice
3. User pays with Lightning wallet
4. GET /api/contributions/<id>/status - Frontend polls for payment status
5. POST /api/webhooks/lnbits - LNbits notifies on payment (alternative to polling)
"""

from flask import request, jsonify
from datetime import datetime
import logging
import uuid

from services.auth import optional_auth, require_auth
from . import contributions_bp
from models import Contribution
from services import get_supabase_client, LNbitsService, InvoicePollingService
from services.lnbits import LNbitsAPIError
from pydantic import ValidationError
from config import Config

logger = logging.getLogger(__name__)
supabase = get_supabase_client()
lnbits_service = LNbitsService()
polling_service = InvoicePollingService()


def btc_to_sats(btc: float) -> int:
    """Convert BTC to satoshis"""
    return int(btc * 100_000_000)


@contributions_bp.route('', methods=['POST'])
@optional_auth
def create_contribution():
    """
    Create a new contribution and generate Lightning invoice

    Request Body:
    {
        "campaign_id": "uuid",
        "contributor_name": "John Doe" (optional),
        "contributor_email": "john@example.com" (optional),
        "amount": 1000,  // Amount in satoshis
        "currency": "SATS" or "BTC",
        "message": "Good luck!" (optional),
        "is_anonymous": false
    }

    Response:
    {
        "message": "Contribution created successfully",
        "contribution": {...},
        "payment_request": "lnbc...",  // BOLT11 invoice for QR code
        "payment_hash": "abc123..."    // For status checking
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate campaign exists and is active
        campaign_id = data.get('campaign_id')
        campaign_response = supabase.table('campaigns').select('*').eq(
            'id', campaign_id
        ).single().execute()

        if not campaign_response.data:
            return jsonify({'error': 'Campaign not found'}), 404

        campaign = campaign_response.data

        if campaign.get('status') != 'active':
            return jsonify({'error': 'Campaign is not active'}), 400

        # Convert BTC to SATS if needed
        amount = data.get('amount', 0)
        currency = data.get('currency', 'SATS').upper()

        if currency == 'BTC':
            amount = btc_to_sats(amount)
            currency = 'SATS'

        # Validate minimum amount (100 sats)
        if amount < 100:
            return jsonify({'error': 'Minimum contribution is 100 satoshis'}), 400

        data['amount'] = amount
        data['currency'] = currency

        # Create contribution model
        contribution = Contribution(**data)
        contribution.created_at = datetime.now()
        contribution.payment_status = 'pending'

        # Create LNbits Lightning invoice
        try:
            # Generate memo for the invoice
            memo = f"CrowdPay: {campaign.get('title')[:50]}"
            if contribution.contributor_name and not contribution.is_anonymous:
                memo += f" from {contribution.contributor_name}"

            # Create invoice via LNbits API
            payment_data = lnbits_service.create_invoice(
                amount=int(amount),
                memo=memo,
                expiry=3600  # 1 hour expiry
            )

            # Store payment data in contribution
            contribution.lnbits_payment_hash = payment_data['payment_hash']
            contribution.lnbits_payment_request = payment_data['payment_request']
            contribution.lnbits_checking_id = payment_data['checking_id']

            # Also store in legacy fields for DB compatibility
            contribution.bitnob_payment_hash = payment_data['payment_hash']
            contribution.bitnob_payment_request = payment_data['payment_request']
            contribution.bitnob_payment_id = payment_data['checking_id']
            contribution.bitnob_reference = f"contrib_{uuid.uuid4().hex[:12]}"

            # Handle anonymous contributions
            if contribution.is_anonymous:
                contribution.contributor_name = None
                contribution.contributor_email = None

            # Insert contribution into database
            contrib_data = contribution.to_dict()
            contrib_data.pop('id', None)

            response = supabase.table('contributions').insert(contrib_data).execute()
            if not response.data:
                return jsonify({'error': 'Failed to create contribution'}), 500

            created_contribution = Contribution.from_dict(response.data[0])

            # Start polling for payment confirmation
            polling_service.start_polling(
                contribution_id=created_contribution.id,
                payment_hash=payment_data['payment_hash'],
                campaign_id=campaign_id
            )

            logger.info(f"Contribution created: {created_contribution.id} with payment_hash: {payment_data['payment_hash']}")

            return jsonify({
                'message': 'Contribution created successfully',
                'contribution': created_contribution.dict(),
                'payment_request': payment_data['payment_request'],
                'payment_hash': payment_data['payment_hash']
            }), 201

        except LNbitsAPIError as e:
            logger.error(f"Error creating LNbits invoice: {str(e)}")
            return jsonify({'error': 'Payment processing error', 'details': str(e)}), 400

    except ValidationError as e:
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except Exception as e:
        logger.error(f"Error creating contribution: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@contributions_bp.route('/<contribution_id>', methods=['GET'])
@optional_auth
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
@optional_auth
def check_contribution_status(contribution_id):
    """
    Check the payment status of a contribution

    This endpoint is used by the frontend to poll for payment confirmation.
    It checks LNbits directly for the latest status.

    Response:
    {
        "contribution_id": "uuid",
        "payment_status": "pending|paid|failed|expired",
        "is_paid": true/false,
        "paid_at": "2024-01-01T00:00:00Z"
    }
    """
    try:
        response = supabase.table('contributions').select('*').eq(
            'id', contribution_id
        ).single().execute()

        if not response.data:
            return jsonify({'error': 'Contribution not found'}), 404

        contribution = Contribution.from_dict(response.data)

        # If pending and has payment hash, check with LNbits
        if contribution.is_pending() and contribution.get_payment_hash():
            try:
                payment_status = lnbits_service.check_invoice_status(
                    contribution.get_payment_hash()
                )

                # Update if payment confirmed
                if payment_status['paid'] and not contribution.is_paid():
                    update_data = {
                        'payment_status': 'paid',
                        'paid_at': datetime.now().isoformat(),
                        'transaction_id': payment_status.get('preimage'),
                        'updated_at': datetime.now().isoformat()
                    }

                    supabase.table('contributions').update(update_data).eq(
                        'id', contribution_id
                    ).execute()

                    # Update campaign amount
                    campaign_id = contribution.campaign_id
                    amount = contribution.amount
                    platform_fee = amount * (Config.PLATFORM_FEE_PERCENT / 100)
                    creator_amount = amount - platform_fee

                    campaign_response = supabase.table('campaigns').select(
                        'current_amount'
                    ).eq('id', campaign_id).single().execute()

                    if campaign_response.data:
                        new_amount = campaign_response.data['current_amount'] + creator_amount
                        supabase.table('campaigns').update({
                            'current_amount': new_amount,
                            'updated_at': datetime.now().isoformat()
                        }).eq('id', campaign_id).execute()

                    # Stop polling
                    polling_service.stop_polling(contribution_id)

                    contribution.payment_status = 'paid'
                    contribution.paid_at = datetime.now()

                    logger.info(f"Payment confirmed via status check: {contribution_id}")

            except LNbitsAPIError as e:
                logger.error(f"Error checking LNbits status: {str(e)}")

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
@require_auth
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

        # Lightning invoices expire automatically, just stop polling
        if contribution.get_payment_hash():
            logger.info(f"Invoice will expire automatically: {contribution.get_payment_hash()}")

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
@optional_auth
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
def lnbits_webhook():
    """
    Webhook endpoint for LNbits payment notifications

    LNbits sends a POST request when a payment is received.
    The webhook URL is set when creating the invoice.

    Expected payload from LNbits:
    {
        "payment_hash": "abc123...",
        "payment_request": "lnbc...",
        "amount": 1000,
        "memo": "...",
        "paid": true
    }
    """
    try:
        # Get raw payload for signature verification
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-LNbits-Signature', '')

        # Verify webhook signature (optional but recommended)
        if signature and not lnbits_service.verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature")
            # Continue anyway as signature verification is optional for LNbits

        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        payment_hash = data.get('payment_hash')
        is_paid = data.get('paid', False)

        if not payment_hash:
            return jsonify({'error': 'Payment hash required'}), 400

        # Only process if payment is confirmed
        if not is_paid:
            return jsonify({'message': 'Payment not yet confirmed'}), 200

        # Find contribution by payment hash
        response = supabase.table('contributions').select('*').eq(
            'bitnob_payment_hash', payment_hash
        ).execute()

        if not response.data:
            logger.warning(f"No contribution found for payment_hash: {payment_hash}")
            return jsonify({'message': 'Contribution not found'}), 404

        contribution_data = response.data[0]
        contribution_id = contribution_data['id']
        campaign_id = contribution_data['campaign_id']

        # Check if already paid
        if contribution_data['payment_status'] == 'paid':
            logger.info(f"Contribution {contribution_id} already marked as paid")
            return jsonify({'message': 'Already processed'}), 200

        # Update contribution status
        update_data = {
            'payment_status': 'paid',
            'paid_at': datetime.now().isoformat(),
            'transaction_id': data.get('preimage'),
            'updated_at': datetime.now().isoformat()
        }

        supabase.table('contributions').update(update_data).eq(
            'id', contribution_id
        ).execute()

        # Update campaign amount with fee deduction
        amount = contribution_data['amount']
        platform_fee = amount * (Config.PLATFORM_FEE_PERCENT / 100)
        creator_amount = amount - platform_fee

        campaign_response = supabase.table('campaigns').select(
            'current_amount'
        ).eq('id', campaign_id).single().execute()

        if campaign_response.data:
            new_amount = campaign_response.data['current_amount'] + creator_amount
            supabase.table('campaigns').update({
                'current_amount': new_amount,
                'updated_at': datetime.now().isoformat()
            }).eq('id', campaign_id).execute()

        # Stop polling
        polling_service.stop_polling(contribution_id)

        logger.info(f"Webhook: Payment confirmed for {contribution_id}")

        return jsonify({'message': 'Webhook processed successfully'}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
