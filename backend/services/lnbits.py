"""
LNbits Service Module for CrowdPay

This module handles all Lightning Network payment operations via LNbits API.
LNbits is a free and open-source lightning wallet/accounts system.

Lightning Payment Flow:
1. Create invoice (bolt11) using invoice key (read-only)
2. Display QR code to user
3. Poll payment status OR receive webhook notification
4. Update contribution status on payment confirmation

API Reference: https://demo.lnbits.com/docs
"""

import requests
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from config import Config


logger = logging.getLogger(__name__)


class LNbitsAPIError(Exception):
    """Custom exception for LNbits API errors"""
    pass


class LNbitsService:
    """
    Service for interacting with LNbits API

    LNbits uses two types of API keys:
    - Admin Key: Full access (create invoices, pay invoices, get balance)
    - Invoice/Read Key: Limited access (create invoices, check status)

    For security, we primarily use the Invoice Key for creating invoices
    and checking status. Admin Key is only used for paying invoices (if needed).
    """

    def __init__(self):
        self.api_url = Config.LNBITS_URL.rstrip('/')
        self.admin_key = Config.LNBITS_ADMIN_KEY
        self.invoice_key = Config.LNBITS_INVOICE_KEY
        self.wallet_id = Config.LNBITS_WALLET_ID
        self.webhook_url = Config.LNBITS_WEBHOOK_URL

        self.session = requests.Session()
        # Default headers use invoice key (safer for most operations)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _get_headers(self, use_admin_key: bool = False) -> Dict[str, str]:
        """
        Get headers with appropriate API key

        Args:
            use_admin_key: If True, use admin key (required for paying invoices)
                          If False, use invoice key (safer for creating/checking)
        """
        key = self.admin_key if use_admin_key else self.invoice_key
        return {
            'X-Api-Key': key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def get_wallet_details(self) -> Dict[str, Any]:
        """
        Get wallet details including balance

        Endpoint: GET /api/v1/wallet
        Header: X-Api-Key = invoice/read key

        Returns:
            Dictionary containing wallet info:
            - id: Wallet ID
            - name: Wallet name
            - balance: Balance in millisatoshis (divide by 1000 for sats)

        Raises:
            LNbitsAPIError: If API call fails
        """
        try:
            logger.info("Fetching LNbits wallet details")

            response = self.session.get(
                f'{self.api_url}/api/v1/wallet',
                headers=self._get_headers(use_admin_key=False),
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            # LNbits returns balance in millisatoshis
            balance_msats = data.get('balance', 0)
            balance_sats = balance_msats / 1000

            logger.info(f"Wallet balance: {balance_sats} sats")

            return {
                'id': data.get('id'),
                'name': data.get('name'),
                'balance_msats': balance_msats,
                'balance_sats': balance_sats,
                'balance_btc': balance_sats / 100_000_000
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"LNbits API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise LNbitsAPIError(f"Failed to get wallet details: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting wallet details: {str(e)}")
            raise LNbitsAPIError(f"Unexpected error: {str(e)}")

    def create_invoice(
        self,
        amount: int,
        memo: str = "",
        expiry: int = 3600,
        webhook: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Lightning invoice (incoming payment request)

        Endpoint: POST /api/v1/payments
        Header: X-Api-Key = invoice/read key
        Body: {"out": false, "amount": <int>, "memo": <string>, "expiry": <int>, "webhook": <url>}

        Args:
            amount: Amount in satoshis (NOT millisatoshis)
            memo: Description for the invoice
            expiry: Invoice expiry time in seconds (default 1 hour)
            webhook: Optional webhook URL for payment notifications

        Returns:
            Dictionary containing:
            - payment_hash: Unique identifier for this payment
            - payment_request: BOLT11 invoice string (for QR code)
            - checking_id: ID for checking payment status
            - amount: Amount in satoshis
            - memo: Invoice description
            - expiry: Expiry time

        Raises:
            LNbitsAPIError: If invoice creation fails
        """
        try:
            payload = {
                'out': False,  # False = incoming payment (invoice)
                'amount': int(amount),
                'memo': memo or f'CrowdPay contribution of {amount} sats',
                'expiry': expiry
            }

            # Add webhook URL if provided or use default
            webhook_url = webhook or self.webhook_url
            if webhook_url:
                payload['webhook'] = webhook_url

            logger.info(f"Creating LNbits invoice for {amount} sats")

            response = self.session.post(
                f'{self.api_url}/api/v1/payments',
                headers=self._get_headers(use_admin_key=False),
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            payment_hash = data.get('payment_hash')
            payment_request = data.get('payment_request')

            if not payment_hash or not payment_request:
                raise LNbitsAPIError("Invalid response: missing payment_hash or payment_request")

            logger.info(f"Invoice created with payment_hash: {payment_hash}")

            return {
                'payment_hash': payment_hash,
                'payment_request': payment_request,
                'checking_id': data.get('checking_id', payment_hash),
                'amount': amount,
                'memo': memo,
                'expiry': expiry,
                'status': 'pending'
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"LNbits API request failed: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise LNbitsAPIError(f"Failed to create invoice: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating invoice: {str(e)}")
            raise LNbitsAPIError(f"Unexpected error: {str(e)}")

    def check_invoice_status(self, payment_hash: str) -> Dict[str, Any]:
        """
        Check the payment status of an invoice

        Endpoint: GET /api/v1/payments/{payment_hash}
        Header: X-Api-Key = invoice/read key

        Args:
            payment_hash: The payment_hash from create_invoice

        Returns:
            Dictionary containing:
            - paid: Boolean indicating if payment is complete
            - status: 'pending', 'paid', 'expired', or 'failed'
            - payment_hash: The payment hash
            - amount: Amount in satoshis
            - fee: Fee paid (if outgoing)
            - preimage: Payment preimage (proof of payment, if paid)

        Raises:
            LNbitsAPIError: If status check fails
        """
        try:
            logger.info(f"Checking payment status for: {payment_hash}")

            response = self.session.get(
                f'{self.api_url}/api/v1/payments/{payment_hash}',
                headers=self._get_headers(use_admin_key=False),
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            # LNbits returns 'paid' as a boolean
            is_paid = data.get('paid', False)

            # Determine status based on paid flag and other fields
            if is_paid:
                status = 'paid'
            elif data.get('pending', True):
                status = 'pending'
            else:
                # Check if expired based on expiry field
                status = 'expired' if data.get('expired') else 'pending'

            logger.info(f"Payment {payment_hash} status: {status}")

            return {
                'payment_hash': payment_hash,
                'paid': is_paid,
                'status': status,
                'amount': data.get('amount', 0),
                'fee': data.get('fee', 0),
                'preimage': data.get('preimage'),
                'memo': data.get('memo'),
                'time': data.get('time'),
                'pending': data.get('pending', not is_paid)
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check payment status: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise LNbitsAPIError(f"Failed to check payment status: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error checking status: {str(e)}")
            raise LNbitsAPIError(f"Unexpected error: {str(e)}")

    def decode_invoice(self, bolt11: str) -> Dict[str, Any]:
        """
        Decode a BOLT11 Lightning invoice

        Endpoint: POST /api/v1/payments/decode
        Body: {"data": <bolt11_string>}

        Args:
            bolt11: BOLT11 invoice string to decode

        Returns:
            Dictionary containing decoded invoice details:
            - payment_hash: Payment hash
            - amount: Amount in millisatoshis
            - description: Invoice description
            - expiry: Expiry time
            - timestamp: Creation timestamp

        Raises:
            LNbitsAPIError: If decode fails
        """
        try:
            logger.info("Decoding BOLT11 invoice")

            response = self.session.post(
                f'{self.api_url}/api/v1/payments/decode',
                headers=self._get_headers(use_admin_key=False),
                json={'data': bolt11},
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            return {
                'payment_hash': data.get('payment_hash'),
                'amount_msat': data.get('amount_msat', 0),
                'amount_sat': data.get('amount_msat', 0) / 1000,
                'description': data.get('description'),
                'expiry': data.get('expiry'),
                'timestamp': data.get('timestamp'),
                'payee': data.get('payee'),
                'date': data.get('date')
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to decode invoice: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise LNbitsAPIError(f"Failed to decode invoice: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error decoding invoice: {str(e)}")
            raise LNbitsAPIError(f"Unexpected error: {str(e)}")

    def pay_invoice(self, bolt11: str) -> Dict[str, Any]:
        """
        Pay a Lightning invoice (outgoing payment)

        WARNING: This requires the ADMIN KEY and will deduct from wallet balance.
        Only use this for platform payouts to creators.

        Endpoint: POST /api/v1/payments
        Header: X-Api-Key = ADMIN key (required for outgoing payments)
        Body: {"out": true, "bolt11": <invoice_string>}

        Args:
            bolt11: BOLT11 invoice string to pay

        Returns:
            Dictionary containing:
            - payment_hash: Payment hash
            - checking_id: ID for checking status
            - fee: Fee paid in millisatoshis

        Raises:
            LNbitsAPIError: If payment fails
        """
        try:
            logger.info("Paying Lightning invoice")

            payload = {
                'out': True,  # True = outgoing payment
                'bolt11': bolt11
            }

            response = self.session.post(
                f'{self.api_url}/api/v1/payments',
                headers=self._get_headers(use_admin_key=True),  # ADMIN KEY required
                json=payload,
                timeout=60  # Longer timeout for payments
            )

            response.raise_for_status()
            data = response.json()

            payment_hash = data.get('payment_hash')
            logger.info(f"Payment sent with hash: {payment_hash}")

            return {
                'payment_hash': payment_hash,
                'checking_id': data.get('checking_id'),
                'fee': data.get('fee', 0),
                'status': 'complete'
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to pay invoice: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise LNbitsAPIError(f"Failed to pay invoice: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error paying invoice: {str(e)}")
            raise LNbitsAPIError(f"Unexpected error: {str(e)}")

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature from LNbits

        Note: LNbits webhook signature verification depends on your setup.
        This implementation uses HMAC-SHA256 with the admin key as secret.

        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers

        Returns:
            True if signature is valid, False otherwise
        """
        if not signature:
            logger.warning("No webhook signature provided")
            return False

        try:
            # LNbits uses the admin key for webhook signatures
            expected_signature = hmac.new(
                self.admin_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature)

        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False

    def get_payments(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get list of recent payments

        Endpoint: GET /api/v1/payments
        Header: X-Api-Key = invoice/read key

        Args:
            limit: Maximum number of payments to return

        Returns:
            Dictionary containing list of payments

        Raises:
            LNbitsAPIError: If API call fails
        """
        try:
            logger.info(f"Fetching last {limit} payments")

            response = self.session.get(
                f'{self.api_url}/api/v1/payments',
                headers=self._get_headers(use_admin_key=False),
                params={'limit': limit},
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            return {
                'payments': data if isinstance(data, list) else [],
                'count': len(data) if isinstance(data, list) else 0
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get payments: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise LNbitsAPIError(f"Failed to get payments: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting payments: {str(e)}")
            raise LNbitsAPIError(f"Unexpected error: {str(e)}")


# Utility functions for satoshi conversions
def btc_to_sats(btc: float) -> int:
    """Convert BTC to satoshis"""
    return int(btc * 100_000_000)


def sats_to_btc(sats: int) -> float:
    """Convert satoshis to BTC"""
    return sats / 100_000_000


def msats_to_sats(msats: int) -> int:
    """Convert millisatoshis to satoshis"""
    return msats // 1000


def sats_to_msats(sats: int) -> int:
    """Convert satoshis to millisatoshis"""
    return sats * 1000
