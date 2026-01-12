from flask import request, jsonify
from datetime import datetime
import logging
from . import campaigns_bp
from models import Campaign
from services import get_supabase_client
from pydantic import ValidationError

logger = logging.getLogger(__name__)
supabase = get_supabase_client()


@campaigns_bp.route('', methods=['POST'])
def create_campaign():
    """Create a new campaign"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate and create campaign model
        campaign = Campaign(**data)
        campaign.created_at = datetime.now()
        campaign.updated_at = datetime.now()
        
        # Insert into database
        campaign_data = campaign.to_dict()
        campaign_data.pop('id', None)
        
        response = supabase.table('campaigns').insert(campaign_data).execute()
        
        if not response.data:
            return jsonify({'error': 'Failed to create campaign'}), 500
        
        created_campaign = Campaign.from_dict(response.data[0])
        
        logger.info(f"Campaign created: {created_campaign.id}")
        
        return jsonify({
            'message': 'Campaign created successfully',
            'campaign': created_campaign.dict()
        }), 201
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except Exception as e:
        logger.error(f"Error creating campaign: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@campaigns_bp.route('', methods=['GET'])
def get_campaigns():
    """Get all campaigns with optional filtering"""
    try:
        # Get query parameters
        status = request.args.get('status')
        creator_id = request.args.get('creator_id')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = supabase.table('campaigns').select('*')
        
        if status:
            query = query.eq('status', status)
        
        if creator_id:
            query = query.eq('creator_id', creator_id)
        
        # Execute query with pagination
        response = query.order('created_at', desc=True).range(
            offset, offset + limit - 1
        ).execute()
        
        campaigns = [Campaign.from_dict(c).dict() for c in response.data]
        
        return jsonify({
            'campaigns': campaigns,
            'count': len(campaigns),
            'offset': offset,
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching campaigns: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@campaigns_bp.route('/<campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get a specific campaign by ID"""
    try:
        response = supabase.table('campaigns').select('*').eq(
            'id', campaign_id
        ).single().execute()
        
        if not response.data:
            return jsonify({'error': 'Campaign not found'}), 404
        
        campaign = Campaign.from_dict(response.data)
        
        # Get contribution statistics
        contrib_response = supabase.table('contributions').select(
            'id, amount, payment_status'
        ).eq('campaign_id', campaign_id).execute()
        
        total_contributions = len(contrib_response.data)
        paid_contributions = sum(
            1 for c in contrib_response.data if c['payment_status'] == 'paid'
        )
        
        return jsonify({
            'campaign': campaign.dict(),
            'statistics': {
                'progress_percentage': campaign.progress_percentage(),
                'remaining_amount': campaign.remaining_amount(),
                'total_contributions': total_contributions,
                'paid_contributions': paid_contributions,
                'is_goal_reached': campaign.is_goal_reached()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching campaign: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@campaigns_bp.route('/<campaign_id>', methods=['PUT'])
def update_campaign(campaign_id):
    """Update a campaign"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Check if campaign exists
        existing = supabase.table('campaigns').select('*').eq(
            'id', campaign_id
        ).single().execute()
        
        if not existing.data:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Update only allowed fields
        allowed_fields = [
            'title', 'description', 'target_amount', 'status', 'end_date'
        ]
        
        update_data = {
            k: v for k, v in data.items() if k in allowed_fields
        }
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Validate with pydantic
        campaign_data = {**existing.data, **update_data}
        Campaign(**campaign_data)  # Validation
        
        response = supabase.table('campaigns').update(update_data).eq(
            'id', campaign_id
        ).execute()
        
        updated_campaign = Campaign.from_dict(response.data[0])
        
        logger.info(f"Campaign updated: {campaign_id}")
        
        return jsonify({
            'message': 'Campaign updated successfully',
            'campaign': updated_campaign.dict()
        }), 200
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    except Exception as e:
        logger.error(f"Error updating campaign: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@campaigns_bp.route('/<campaign_id>', methods=['DELETE'])
def delete_campaign(campaign_id):
    """Delete a campaign (soft delete by changing status)"""
    try:
        # Check if campaign exists
        existing = supabase.table('campaigns').select('*').eq(
            'id', campaign_id
        ).single().execute()
        
        if not existing.data:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Soft delete by updating status
        supabase.table('campaigns').update({
            'status': 'cancelled',
            'updated_at': datetime.now().isoformat()
        }).eq('id', campaign_id).execute()
        
        logger.info(f"Campaign deleted (cancelled): {campaign_id}")
        
        return jsonify({'message': 'Campaign cancelled successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting campaign: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@campaigns_bp.route('/<campaign_id>/contributions', methods=['GET'])
def get_campaign_contributions(campaign_id):
    """Get all contributions for a campaign"""
    try:
        # Check if campaign exists
        campaign_exists = supabase.table('campaigns').select('id').eq(
            'id', campaign_id
        ).execute()
        
        if not campaign_exists.data:
            return jsonify({'error': 'Campaign not found'}), 404
        
        # Get contributions
        response = supabase.table('contributions').select('*').eq(
            'campaign_id', campaign_id
        ).order('created_at', desc=True).execute()
        
        contributions = response.data
        
        # Filter anonymous contributor info
        for contrib in contributions:
            if contrib.get('is_anonymous'):
                contrib['contributor_name'] = 'Anonymous'
                contrib['contributor_email'] = None
        
        return jsonify({
            'contributions': contributions,
            'count': len(contributions)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching contributions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    