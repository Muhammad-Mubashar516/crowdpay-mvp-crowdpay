import requests
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from config import Config


logger = logging.getLogger(__name__)

class BitnobAPIError(Exception):
    """Custom exception for Bitnob API errors"""
    pass

class BitnobService:
    """Service for interacting with Bitnob API"""
    
    def __init__(self):
        self.api_url = Config.BITNOB_API_URL
        self.api_key = Config.BITNOB_API_KEY
        self.webhook_secret = Config.BITNOB_WEBHOOK_SECRET
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def create_lightning_address_payment(
        self, 
        amount: float,
        description: Optional[str] = None,
        customer_email: Optional[str] = None,
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Lightning Network payment request
        
        Args:
            amount: Payment amount in satoshis
            description: Payment description
            customer_email: Customer email for notifications
            reference: Unique reference for the payment
            
        Returns:
            Dictionary containing payment details including lightning invoice
            
        Raises:
            BitnobAPIError: If payment creation fails
        """
        try:
            payload = {
                'satoshis': int(amount),
                'description': description or f'Contribution of {amount} satoshis',
                'customerEmail': customer_email,
                'reference': reference
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            logger.info(f"Creating Bitnob Lightning payment for {amount} satoshis")
            
            response = self.session.post(
                f'{self.api_url}/api/v1/wallets/ln/createinvoice',
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            message = data.get('message', '').lower()

            if 'success' not in message and 'created' not in message:
                raise BitnobAPIError(f"API returned error: {data.get('message')}")

            
            payment_data = data.get('data', {})

            if not payment_data:
                raise BitnobAPIError("No payment data returned from API")
            logger.info(f"Lightning payment created: {payment_data.get('id')}")
            
            return {
            'payment_id': payment_data.get('id') or reference,
            'lightning_invoice': payment_data.get('request'),  # The actual invoice string
            'payment_request': payment_data.get('request'),  # Alias for compatibility
            'payment_hash': (
                payment_data.get('paymentHash') or payment_data.get('payment_hash')
            ),
            'amount': payment_data.get('tokens') or int(amount),
            'description': payment_data.get('description'),
            'reference': payment_data.get('reference') or reference,
            'status': 'pending',
            'expires_at': payment_data.get('expiresAt')   
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Bitnob API request failed: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise BitnobAPIError(f"Failed to create Lightning payment: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating Lightning payment: {str(e)}")
            raise BitnobAPIError(f"Unexpected error: {str(e)}")
    
    def create_checkout(
        self,
        amount: float,
        currency: str = "KSH",
        description: Optional[str] = None,
        customer_email: Optional[str] = None,
        reference: Optional[str] = None,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a hosted checkout page for payment
        
        Args:
            amount: Payment amount
            currency: Currency code (KSH, USD, NGN)
            description: Payment description
            customer_email: Customer email
            reference: Unique reference
            callback_url: Callback URL for payment notifications
            
        Returns:
            Dictionary containing checkout URL and payment details
            
        Raises:
            BitnobAPIError: If checkout creation fails
        """
        try:
            payload = {
                'amount': amount,
                'currency': currency,
                'description': description or f'Contribution of {amount} {currency}',
                'customerEmail': customer_email,
                'reference': reference,
                'callbackUrl': callback_url
            }
            
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}
            
            logger.info(f"Creating Bitnob checkout for {amount} {currency}")
            
            response = self.session.post(
                f'{self.api_url}/api/v1/checkout',
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                raise BitnobAPIError(f"API returned error: {data.get('message')}")
            
            checkout_data = data.get('data', {})
            
            logger.info(f"Checkout created: {checkout_data.get('id')}")
            
            return {
                'checkout_id': checkout_data.get('id'),
                'checkout_url': checkout_data.get('hostedUrl'),
                'reference': checkout_data.get('reference'),
                'amount': checkout_data.get('amount'),
                'currency': checkout_data.get('currency'),
                'status': checkout_data.get('status', 'pending')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Bitnob API request failed: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise BitnobAPIError(f"Failed to create checkout: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating checkout: {str(e)}")
            raise BitnobAPIError(f"Unexpected error: {str(e)}")
    
    def verify_payment(self, reference: str) -> Dict[str, Any]:
        """
        Verify payment status using reference
        
        Args:
            reference: Payment reference to verify
            
        Returns:
            Dictionary containing payment status and details
            
        Raises:
            BitnobAPIError: If verification fails
        """
        try:
            logger.info(f"Verifying payment: {reference}")
            
            response = self.session.get(
                f'{self.api_url}/api/v1/payments/verify/{reference}',
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                raise BitnobAPIError(f"Verification failed: {data.get('message')}")
            
            payment_data = data.get('data', {})
            
            return {
                'reference': payment_data.get('reference'),
                'status': payment_data.get('status'),
                'paid': payment_data.get('status') == 'success',
                'amount': payment_data.get('amount'),
                'currency': payment_data.get('currency'),
                'paid_at': payment_data.get('paidAt'),
                'payment_hasfh': payment_data.get('paymentHash') or payment_data.get('payment_hash'),
                'payment_method': payment_data.get('paymentMethod'),
                'transaction_id': payment_data.get('transactionId') or payment_data.get('transaction_id')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to verify payment: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise BitnobAPIError(f"Failed to verify payment: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error verifying payment: {str(e)}")
            raise BitnobAPIError(f"Unexpected error: {str(e)}")
    
    def get_lightning_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get Lightning payment status
        
        Args:
            payment_id: Lightning payment ID
            
        Returns:
            Dictionary containing payment status
            
        Raises:
            BitnobAPIError: If status check fails
        """
        try:
            logger.info(f"Checking Lightning payment status: {payment_id}")
            
            response = self.session.get(
                f'{self.api_url}/api/v1/wallets/ln/invoice/{payment_id}',
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get('data'):
                raise BitnobAPIError(f"API returned error: {data.get('message')}")
            
            payment_data = data.get('data', {})
            
            return {
                'payment_id': payment_data.get('id'),
                'status': payment_data.get('status'),
                'paid': payment_data.get('status') == 'paid',
                'amount': payment_data.get('satoshis'),
                'paid_at': payment_data.get('paidAt'),
                'payment_hash': payment_data.get('paymentHash'),
                'reference': payment_data.get('reference')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check payment status: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise BitnobAPIError(f"Failed to check payment status: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error checking status: {str(e)}")
            raise BitnobAPIError(f"Unexpected error: {str(e)}")
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature from Bitnob
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook headers
            
        Returns:
            True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return False
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance
        
        Returns:
            Dictionary containing balance information
            
        Raises:
            BitnobAPIError: If balance retrieval fails
        """
        try:
            response = self.session.get(
                f'{self.api_url}/api/v1/wallets/balance',
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                raise BitnobAPIError(f"API returned error: {data.get('message')}")
            
            balance_data = data.get('data', {})
            
            return {
                'balance': balance_data.get('availableBalance'),
                'currency': balance_data.get('currency'),
                'total_balance': balance_data.get('totalBalance'),
                'pending_balance': balance_data.get('pendingBalance')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get balance: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise BitnobAPIError(f"Failed to get balance: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting balance: {str(e)}")
            raise BitnobAPIError(f"Unexpected error: {str(e)}")
        