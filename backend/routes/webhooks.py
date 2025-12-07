from flask import Blueprint, request, jsonify
from services.supabase_client import supabase
from services.minmo import verify_minmo_signature
from services.lightning import verify_ln_signature


webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('/minmo', methods=['POST'])
def minmo_webhook():
    """Handle Minmo webhook notifications for swap status updates"""
    payload = request.get_json() or {}
    sig = request.headers.get('X-Minmo-Signature','')
    
    # Verify webhook signature for security
    if not verify_minmo_signature(request.data, sig):
        return jsonify({'error': 'invalid signature'}), 400

    # Idempotency check using swap ID
    swap_id = payload.get('id') or payload.get('swap_id')
    if not swap_id:
        return jsonify({'error': 'no swap id in payload'}), 400

    existing = supabase.table('webhook_events').select('*').eq('provider', 'minmo').eq('payload->>id', str(swap_id)).execute()
    if existing.data and len(existing.data) > 0:
        return jsonify({'status': 'already_processed'})

    # Log webhook event for debugging and audit trail
    supabase.table('webhook_events').insert({
        'provider': 'minmo',
        'payload': payload,
        'event_type': payload.get('status', 'unknown')
    }).execute()

    # Process based on swap status
    swap_status = payload.get('status')
    metadata = payload.get('metadata') or {}
    contribution_id = metadata.get('contribution_id')
    
    if not contribution_id:
        print(f"Warning: Minmo webhook {swap_id} has no contribution_id in metadata")
        return jsonify({'status': 'ok', 'warning': 'no contribution_id'})

    # Update contribution based on swap status
    update_data = {}
    
    if swap_status == 'initiated':
        update_data = {'status': 'payment_initiated'}
    elif swap_status == 'agent_matched':
        update_data = {'status': 'agent_matched'}
    elif swap_status == 'payment_pending':
        update_data = {'status': 'payment_pending'}
    elif swap_status == 'payment_confirmed':
        update_data = {'status': 'payment_confirmed'}
    elif swap_status == 'escrow_releasing':
        update_data = {'status': 'processing'}
    elif swap_status == 'completed':
        update_data = {
            'status': 'completed',
            'amount_btc': payload.get('btc_amount') or payload.get('bitcoin_amount'),
            'completed_at': payload.get('completed_at')
        }
    elif swap_status == 'disputed':
        update_data = {'status': 'disputed'}
    elif swap_status == 'cancelled':
        update_data = {'status': 'cancelled'}
    else:
        print(f"Unknown Minmo swap status: {swap_status}")
        update_data = {'status': f'minmo_{swap_status}'}

    # Update contribution record
    if update_data:
        supabase.table('contributions').update(update_data).eq('id', contribution_id).execute()
        print(f"Updated contribution {contribution_id} with status: {update_data.get('status')}")

    return jsonify({'status': 'ok', 'processed_status': swap_status})


@webhooks_bp.route('/lightning', methods=['POST'])
def lightning_webhook():
    payload = request.get_json() or {}
    sig = request.headers.get('X-Lightning-Signature','')
    if not verify_ln_signature(request.data, sig):
        return jsonify({'error': 'invalid signature'}), 400

    event_id = payload.get('id')
    existing = supabase.table('webhook_events').select('*').eq('provider', 'lightning').eq('payload->>id', str(event_id)).execute()
    if existing.data and len(existing.data) > 0:
        return jsonify({'status': 'already_processed'})

    supabase.table('webhook_events').insert({'provider':'lightning','payload':payload}).execute()

    # find contribution
    metadata = payload.get('metadata') or {}
    contribution_id = metadata.get('contribution_id')
    settled = payload.get('status') == 'settled' or payload.get('settled') is True
    if contribution_id and settled:
        supabase.table('contributions').update({'status':'completed','amount_btc': payload.get('amount_btc')}).eq('id', contribution_id).execute()

    return jsonify({'status':'ok'})