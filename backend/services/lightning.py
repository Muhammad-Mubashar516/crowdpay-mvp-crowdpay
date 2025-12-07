import os
import hmac
import hashlib
import base64
from dotenv import load_dotenv
import requests


load_dotenv()

LIGHTNING_API_KEY = os.getenv('LIGHTNING_API_KEY')
LIGHTNING_BASE = os.getenv('LIGHTNING_BASE')
LIGHTNING_SIGNATURE_METHOD = os.getenv('LIGHTNING_SIGNATURE_METHOD', 'hmac-sha256')
LIGHTNING_WEBHOOK_SECRET = os.getenv('LIGHTNING_WEBHOOK_SECRET')  #HMAC verification


def create_invoice(amount_sats: int, memo: str, metadata: dict):
    if not LIGHTNING_API_KEY:
        raise RuntimeError('LIGHTNING_API_KEY is not set in environment')
    if not LIGHTNING_BASE:
        raise RuntimeError('LIGHTNING_BASE is not set in environment')

    headers = {
        'Authorization': f'Bearer {LIGHTNING_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {'amount': amount_sats, 'memo': memo, 'metadata': metadata}
    r = requests.post(f'{LIGHTNING_BASE.rstrip("/")}/invoices', json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


def verify_ln_signature(payload_bytes: bytes, signature: str) -> bool:
    """
    Verify a webhook/payload signature according to configured provider method.

    Current supported methods:
    - "hmac-sha256" (default): uses LIGHTNING_WEBHOOK_SECRET to compute HMAC-SHA256.
      Accepts signatures in these common forms:
        * hex digest (e.g. "a3f4...")
        * "sha256=<hex>"
        * base64 of the raw digest
    """
    if not signature:
        return False

    method = (LIGHTNING_SIGNATURE_METHOD or 'hmac-sha256').lower()

    sig = signature.strip()
    if sig.startswith('sha256='):
        sig = sig.split('=', 1)[1]

    if method == 'hmac-sha256':
        if not LIGHTNING_WEBHOOK_SECRET:
            return False
        secret = LIGHTNING_WEBHOOK_SECRET.encode('utf-8')
        mac = hmac.new(secret, payload_bytes, hashlib.sha256)
        expected_hex = mac.hexdigest()
        expected_b64 = base64.b64encode(mac.digest()).decode('ascii')

        # constant-time compare; accept either hex or base64 forms
        return hmac.compare_digest(sig, expected_hex) or hmac.compare_digest(sig, expected_b64)

    # Provider specific verification not implem ented
    raise NotImplementedError(f'Unsupported signature verification method: {LIGHTNING_SIGNATURE_METHOD}')