from flask import Blueprint, request, jsonify, url_for
from services.supabase_client import supabase
from services.minmo import create_minmo_swap
from services.lightning import create_invoice
import uuid


contributions_bp = Blueprint('contributions', __name__)


@contributions_bp.route('/create', methods=['POST'])
def create_contribution():
    data = request.get_json() or {}
    required = ['link_id', 'amount_kes', 'payment_method']
    for f in required:
        if f not in data:
            return jsonify({'error': f'{f} required'}), 400

    contribution_id = str(uuid.uuid4())
    payment_method = data['payment_method']
    link_id = data['link_id']

    base_record = {
        'id': contribution_id,
        'link_id': link_id,
        'amount_kes': data['amount_kes'],
        'amount_btc': None,
        'payment_method': payment_method,
        'donor_name': data.get('donor_name'),
        'donor_email': data.get('donor_email'),
        'status': 'pending'
    }

    # insert base contribution
    try:
        res = supabase.table('contributions').insert(base_record).execute()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    if payment_method.lower() in ['mpesa', 'kes', 'bank_transfer']:
        callback_url = (request.url_root.rstrip('/') + url_for('webhooks.minmo_webhook'))
        try:
            swap = create_minmo_swap(
                amount_kes=float(data['amount_kes']), 
                callback_url=callback_url, 
                metadata={'contribution_id': contribution_id},
                payment_method=payment_method.lower()
            )
            # Store provider data including swap ID for tracking
            supabase.table('contributions').update({
                'provider_reference': swap.get('id'),  # Store swap ID specifically
                'provider_data': swap  # Store full response for debugging
            }).eq('id', contribution_id).execute()
            
            return jsonify({
                'contribution_id': contribution_id, 
                'minmo_swap': swap,
                'status': 'swap_created'
            })
        except Exception as e:
            # If swap creation fails, mark contribution as failed
            supabase.table('contributions').update({
                'status': 'failed',
                'error_message': str(e)
            }).eq('id', contribution_id).execute()
            return jsonify({'error': f'Failed to create payment: {str(e)}'}), 500

    if payment_method.lower() == 'lightning':
        # Validate amount
        amount_kes = float(data.get('amount_kes', 0))
        if amount_kes <= 0:
            return jsonify({'error': 'Invalid amount - must be greater than 0'}), 400
        
        # Convert KES to satoshis (Placeholder conversion rate of 1 KES = 650 sats)
        sats = int(amount_kes * 650)
        
        try:
            invoice = create_invoice(amount_sats=sats, memo=f"CrowdPay contribution {contribution_id}", metadata={'contribution_id': contribution_id})
            supabase.table('contributions').update({
                'provider_reference': invoice.get('id'),
                'provider_data': invoice
            }).eq('id', contribution_id).execute()
            return jsonify({
                'contribution_id': contribution_id, 
                'lightning_invoice': invoice,
                'status': 'invoice_created'
            })
        except Exception as e:
            supabase.table('contributions').update({
                'status': 'failed',
                'error_message': str(e)
            }).eq('id', contribution_id).execute()
            return jsonify({'error': f'Failed to create Lightning invoice: {str(e)}'}), 500

    return jsonify({'contribution_id': contribution_id})


@contributions_bp.route('/<contribution_id>', methods=['GET'])
def get_contribution(contribution_id):
    res = supabase.table('contributions').select('*').eq('id', contribution_id).limit(1).execute()
    if res.data and len(res.data) > 0:
        return jsonify(res.data[0])
    return jsonify({'error': 'not found'}), 404