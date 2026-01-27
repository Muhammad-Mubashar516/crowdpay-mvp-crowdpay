"""
Payment Routes for CrowdPay

Provides direct LNbits invoice/wallet operations:
- POST /api/invoice/create - Create Lightning invoice
- GET /api/invoice/status/<payment_hash> - Check invoice status
- GET /api/wallet/balance - Get platform wallet balance
- POST /api/webhooks/lnbits - LNbits webhook endpoint

These routes complement the contribution routes by providing
direct access to Lightning payment functionality.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from services.auth import optional_auth, require_auth
from services import get_supabase_client, LNbitsService, InvoicePollingService
from services.lnbits import LNbitsAPIError
from config import Config

logger = logging.getLogger(__name__)

# Create blueprint
payments_bp = Blueprint('payments', __name__)

# Initialize services
lnbits_service = LNbitsService()
supabase = get_supabase_client()
polling_service = InvoicePollingService()


@payments_bp.route('/invoice/create', methods=['POST'])
@optional_auth
def create_invoice():
    """
    Create a standalone Lightning invoice

    This endpoint creates an invoice without a contribution record.
    Useful for testing or custom payment flows.

    Request Body:
    {
        "amount": 1000,  // Amount in satoshis
        "memo": "Payment description",
        "expiry": 3600  // Optional, default 1 hour
    }

    Response:
    {
        "payment_hash": "abc123...",
        "payment_request": "lnbc...",
        "amount": 1000,
        "memo": "...",
        "expiry": 3600
    }
    """
    try:
        data = request.get_json() or {}

        amount = data.get('amount')
        memo = data.get('memo', 'CrowdPay Payment')
        expiry = data.get('expiry', 3600)

        if not amount or amount < 1:
            return jsonify({'error': 'Amount must be at least 1 satoshi'}), 400

        if amount > 10_000_000:  # 0.1 BTC max
            return jsonify({'error': 'Amount exceeds maximum (10,000,000 sats)'}), 400

        invoice_data = lnbits_service.create_invoice(
            amount=int(amount),
            memo=memo,
            expiry=expiry
        )

        logger.info(f"Invoice created: {invoice_data['payment_hash']}")

        return jsonify({
            'payment_hash': invoice_data['payment_hash'],
            'payment_request': invoice_data['payment_request'],
            'amount': amount,
            'memo': memo,
            'expiry': expiry
        }), 201

    except LNbitsAPIError as e:
        logger.error(f"Error creating invoice: {str(e)}")
        return jsonify({'error': 'Failed to create invoice', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error creating invoice: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@payments_bp.route('/invoice/status/<payment_hash>', methods=['GET'])
@optional_auth
def check_invoice_status(payment_hash):
    """
    Check the status of a Lightning invoice

    Response:
    {
        "payment_hash": "abc123...",
        "paid": true/false,
        "status": "pending|paid|expired",
        "amount": 1000,
        "preimage": "..." (if paid)
    }
    """
    try:
        if not payment_hash:
            return jsonify({'error': 'Payment hash required'}), 400

        status_data = lnbits_service.check_invoice_status(payment_hash)

        return jsonify({
            'payment_hash': payment_hash,
            'paid': status_data['paid'],
            'status': status_data['status'],
            'amount': status_data.get('amount'),
            'preimage': status_data.get('preimage'),
            'pending': status_data.get('pending', not status_data['paid'])
        }), 200

    except LNbitsAPIError as e:
        logger.error(f"Error checking invoice status: {str(e)}")
        return jsonify({'error': 'Failed to check status', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error checking invoice status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@payments_bp.route('/invoice/decode', methods=['POST'])
@optional_auth
def decode_invoice():
    """
    Decode a BOLT11 Lightning invoice

    Request Body:
    {
        "bolt11": "lnbc..."
    }

    Response:
    {
        "payment_hash": "abc123...",
        "amount_sat": 1000,
        "description": "...",
        "expiry": 3600
    }
    """
    try:
        data = request.get_json() or {}
        bolt11 = data.get('bolt11')

        if not bolt11:
            return jsonify({'error': 'BOLT11 invoice required'}), 400

        decoded = lnbits_service.decode_invoice(bolt11)

        return jsonify({
            'payment_hash': decoded.get('payment_hash'),
            'amount_sat': decoded.get('amount_sat'),
            'amount_msat': decoded.get('amount_msat'),
            'description': decoded.get('description'),
            'expiry': decoded.get('expiry'),
            'timestamp': decoded.get('timestamp')
        }), 200

    except LNbitsAPIError as e:
        logger.error(f"Error decoding invoice: {str(e)}")
        return jsonify({'error': 'Failed to decode invoice', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error decoding invoice: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@payments_bp.route('/wallet/balance', methods=['GET'])
@require_auth
def get_wallet_balance():
    """
    Get the platform LNbits wallet balance

    This endpoint requires authentication (admin only in production).

    Response:
    {
        "balance_sats": 100000,
        "balance_btc": 0.001,
        "wallet_id": "..."
    }
    """
    try:
        wallet_data = lnbits_service.get_wallet_details()

        return jsonify({
            'balance_sats': wallet_data['balance_sats'],
            'balance_btc': wallet_data['balance_btc'],
            'balance_msats': wallet_data['balance_msats'],
            'wallet_id': wallet_data.get('id'),
            'wallet_name': wallet_data.get('name')
        }), 200

    except LNbitsAPIError as e:
        logger.error(f"Error getting wallet balance: {str(e)}")
        return jsonify({'error': 'Failed to get balance', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error getting wallet balance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@payments_bp.route('/wallet/payments', methods=['GET'])
@require_auth
def get_wallet_payments():
    """
    Get recent payments from the LNbits wallet

    Query params:
    - limit: Number of payments to return (default 20)

    Response:
    {
        "payments": [...],
        "count": 20
    }
    """
    try:
        limit = request.args.get('limit', 20, type=int)

        if limit > 100:
            limit = 100

        payments_data = lnbits_service.get_payments(limit=limit)

        return jsonify({
            'payments': payments_data['payments'],
            'count': payments_data['count']
        }), 200

    except LNbitsAPIError as e:
        logger.error(f"Error getting payments: {str(e)}")
        return jsonify({'error': 'Failed to get payments', 'details': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error getting payments: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@payments_bp.route('/webhooks/lnbits', methods=['POST'])
def lnbits_webhook():
    """
    Webhook endpoint for LNbits payment notifications

    This is an alternative endpoint to /api/contributions/webhook
    that can be used with LNbits webhook configuration.

    LNbits sends a POST when payment is received:
    {
        "payment_hash": "abc123...",
        "payment_request": "lnbc...",
        "amount": 1000,
        "memo": "...",
        "paid": true
    }
    """
    try:
        payload = request.get_data(as_text=True)
        signature = request.headers.get('X-LNbits-Signature', '')

        # Verify signature if provided
        if signature and not lnbits_service.verify_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature (continuing anyway)")

        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        payment_hash = data.get('payment_hash')
        is_paid = data.get('paid', False)

        if not payment_hash:
            return jsonify({'error': 'Payment hash required'}), 400

        if not is_paid:
            return jsonify({'message': 'Payment not confirmed'}), 200

        # Use polling service to handle the payment
        success = polling_service.handle_webhook_payment(payment_hash)

        if success:
            logger.info(f"Webhook payment processed: {payment_hash}")
            return jsonify({'message': 'Payment processed'}), 200
        else:
            return jsonify({'message': 'Payment not found or already processed'}), 200

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@payments_bp.route('/health', methods=['GET'])
def payments_health():
    """
    Health check for the payments service

    Verifies LNbits connectivity.
    """
    try:
        # Try to get wallet details
        wallet_data = lnbits_service.get_wallet_details()

        return jsonify({
            'status': 'healthy',
            'lnbits_connected': True,
            'wallet_id': wallet_data.get('id'),
            'balance_sats': wallet_data['balance_sats']
        }), 200

    except LNbitsAPIError as e:
        logger.error(f"LNbits health check failed: {str(e)}")
        return jsonify({
            'status': 'degraded',
            'lnbits_connected': False,
            'error': str(e)
        }), 503
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
