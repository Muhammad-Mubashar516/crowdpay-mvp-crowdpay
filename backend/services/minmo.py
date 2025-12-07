import os
import requests
from dotenv import load_dotenv
import hmac
import hashlib
import base64


load_dotenv()

MINMO_API_KEY = os.getenv('MINMO_API_KEY')
MINMO_BASE = os.getenv('MINMO_BASE_URL') 


def create_minmo_swap(amount_kes: float, callback_url: str, metadata: dict = None, payment_method: str = 'mpesa'):
    """
    Create a fiat-to-Bitcoin on-ramp swap using Minmo API
    
    Args:
        amount_kes: Amount in Kenyan Shillings
        callback_url: Webhook URL for status updates
        metadata: Additional data to include with the swap
        payment_method: Payment method (default: 'mpesa')
    
    Returns:
        dict: Minmo swap response containing swap ID and payment details
    """
    if not MINMO_API_KEY:
        raise RuntimeError('MINMO_API_KEY not set in environment (.env)')

    headers = {
        'Authorization': f'Bearer {MINMO_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Minmo API payload structure based on documentation
    payload = {
        'direction': 'on-ramp',
        'amount': amount_kes,
        'currency': 'KES',
        'payment_method': payment_method,
        'webhook_url': callback_url,  # Some APIs use webhook_url instead of callback_url
        'metadata': metadata or {}
    }

    try:
        r = requests.post(f'{MINMO_BASE}/swaps', json=payload, headers=headers, timeout=15)
        r.raise_for_status()
        response = r.json()
        
        print(f"Minmo swap created successfully: {response.get('id', 'unknown')}")
        return response
        
    except requests.RequestException as exc:
        # error handling with detailed logging
        error_msg = f'Failed to create Minmo swap: {exc}'
        if hasattr(exc, 'response') and exc.response is not None:
            try:
                error_details = exc.response.json()
                error_msg += f' - API Error: {error_details}'
            except:
                error_msg += f' - HTTP {exc.response.status_code}'
        
        print(f"Minmo API Error: {error_msg}")
        raise RuntimeError(error_msg) from exc


def verify_minmo_signature(payload_bytes: bytes, signature: str) -> bool:
    """
    Verifies webhook payload using HMAC-SHA256 and a secret loaded from .env.
    Accepts hex or base64 encoded signatures and a possible "sha256=" prefix.
    
    Args:
        payload_bytes: Raw webhook payload bytes
        signature: Signature from X-Minmo-Signature header
    
    Returns:
        bool: True if signature is valid, False otherwise
    """
    secret = os.getenv('MINMO_WEBHOOK_SECRET')
    if not secret:
        print("Warning: MINMO_WEBHOOK_SECRET not configured - failing signature verification")
        return False

    # Normalize incoming signature
    sig = signature.strip()
    if sig.startswith('sha256='):
        sig = sig.split('=', 1)[1]

    # Generate expected signature
    mac = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256).digest()
    hex_sig = mac.hex()
    b64_sig = base64.b64encode(mac).decode()

    # Use compare_digest for timing-safe comparison
    is_valid = hmac.compare_digest(sig, hex_sig) or hmac.compare_digest(sig, b64_sig)
    
    if not is_valid:
        print(f"Invalid Minmo signature. Expected: {hex_sig}, Got: {sig}")
    
    return is_valid


def get_minmo_exchange_rates():
    """
    Get current exchange rates from Minmo API
    
    Returns:
        dict: Exchange rates for supported currencies
    """
    if not MINMO_API_KEY:
        raise RuntimeError('MINMO_API_KEY not set in environment')

    headers = {
        'Authorization': f'Bearer {MINMO_API_KEY}',
        'Content-Type': 'application/json'
    }

    try:
        r = requests.get(f'{MINMO_BASE}/rates', headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        print(f"Failed to get Minmo exchange rates: {exc}")
        raise RuntimeError(f'Failed to get exchange rates: {exc}') from exc


def get_minmo_swap_status(swap_id: str):
    """
    Get the current status of a Minmo swap
    
    Args:
        swap_id: The ID of the swap to check
    
    Returns:
        dict: Swap status information
    """
    if not MINMO_API_KEY:
        raise RuntimeError('MINMO_API_KEY not set in environment')

    headers = {
        'Authorization': f'Bearer {MINMO_API_KEY}',
        'Content-Type': 'application/json'
    }

    try:
        r = requests.get(f'{MINMO_BASE}/swaps/{swap_id}', headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        print(f"Failed to get swap status for {swap_id}: {exc}")
        raise RuntimeError(f'Failed to get swap status: {exc}') from exc