"""
Invoice Polling Service for LNbits Lightning Payments

This service polls LNbits to check payment status for pending invoices.
It runs in a background thread and updates contribution/campaign records
when payments are confirmed.

Alternative: LNbits webhooks can be used instead of polling for
real-time notifications (see /api/webhooks/lnbits endpoint).
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional

from .lnbits import LNbitsService, LNbitsAPIError
from .supabase_client import get_supabase_client
from config import Config

logger = logging.getLogger(__name__)


class InvoicePollingService:
    """Service for polling LNbits Lightning invoices and updating contributions"""

    def __init__(self):
        self.lnbits_service = LNbitsService()
        self.supabase = get_supabase_client()
        self.polling_threads: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, threading.Event] = {}

    def start_polling(
        self,
        contribution_id: str,
        payment_hash: str,
        campaign_id: str,
        callback: Optional[Callable] = None
    ):
        """
        Start polling for a specific contribution's payment status

        Args:
            contribution_id: The contribution ID in our database
            payment_hash: The LNbits payment_hash to poll
            campaign_id: The campaign ID to update on payment
            callback: Optional callback function on payment confirmation
        """
        if contribution_id in self.polling_threads:
            logger.warning(f"Polling already active for contribution {contribution_id}")
            return

        stop_flag = threading.Event()
        self.stop_flags[contribution_id] = stop_flag

        thread = threading.Thread(
            target=self._poll_payment,
            args=(contribution_id, payment_hash, campaign_id, stop_flag, callback),
            daemon=True
        )

        self.polling_threads[contribution_id] = thread
        thread.start()

        logger.info(f"Started polling for contribution {contribution_id} (payment_hash: {payment_hash})")

    def stop_polling(self, contribution_id: str):
        """Stop polling for a specific contribution"""
        if contribution_id in self.stop_flags:
            self.stop_flags[contribution_id].set()
            logger.info(f"Stopped polling for contribution {contribution_id}")

    def _poll_payment(
        self,
        contribution_id: str,
        payment_hash: str,
        campaign_id: str,
        stop_flag: threading.Event,
        callback: Optional[Callable]
    ):
        """
        Background thread that polls LNbits for payment status

        Polls at POLLING_INTERVAL until:
        - Payment is confirmed (paid=True)
        - Payment expires or fails
        - Timeout is reached (POLLING_TIMEOUT)
        - stop_polling() is called
        """
        start_time = datetime.utcnow()
        timeout = timedelta(seconds=Config.POLLING_TIMEOUT)
        interval = Config.POLLING_INTERVAL

        try:
            while not stop_flag.is_set():
                # Check for timeout
                if datetime.utcnow() - start_time > timeout:
                    logger.warning(f"Polling timeout for contribution {contribution_id}")
                    self._update_contribution_status_by_id(contribution_id, "expired")
                    break

                try:
                    # Check payment status with LNbits
                    status_data = self.lnbits_service.check_invoice_status(payment_hash)

                    if status_data["paid"]:
                        # Payment confirmed!
                        if self._already_paid(payment_hash):
                            logger.info("Contribution already marked as paid, skipping")
                            break

                        # Update contribution status
                        self._update_contribution_status_by_payment_hash(
                            payment_hash=payment_hash,
                            status="paid",
                            paid_at=datetime.utcnow().isoformat(),
                            preimage=status_data.get("preimage")
                        )

                        # Update campaign amount
                        self._update_campaign_amount(contribution_id, campaign_id)

                        # Execute callback if provided
                        if callback:
                            callback(contribution_id, status_data)

                        logger.info(f"Payment confirmed for contribution {contribution_id}")
                        break

                    elif status_data.get("status") in ["expired", "cancelled", "failed"]:
                        # Payment failed or expired
                        self._update_contribution_status_by_id(
                            contribution_id,
                            status_data["status"]
                        )
                        logger.info(f"Payment {status_data['status']} for contribution {contribution_id}")
                        break

                except LNbitsAPIError as e:
                    logger.error(f"LNbits polling error: {str(e)}")
                    # Continue polling on API errors (might be temporary)

                # Wait before next poll
                stop_flag.wait(interval)

        except Exception as e:
            logger.error(f"Unexpected polling error: {str(e)}")
            self._update_contribution_status_by_id(contribution_id, "failed")

        finally:
            # Cleanup
            self.polling_threads.pop(contribution_id, None)
            self.stop_flags.pop(contribution_id, None)

    def _already_paid(self, payment_hash: str) -> bool:
        """Check if contribution is already marked as paid"""
        response = (
            self.supabase.table("contributions")
            .select("payment_status")
            .eq("bitnob_payment_hash", payment_hash)  # Using legacy column name
            .single()
            .execute()
        )
        return response.data and response.data["payment_status"] == "paid"

    def _update_contribution_status_by_payment_hash(
        self,
        payment_hash: str,
        status: str,
        paid_at: Optional[str] = None,
        preimage: Optional[str] = None
    ):
        """Update contribution status by payment hash"""
        update_data = {
            "payment_status": status,
            "updated_at": datetime.utcnow().isoformat()
        }

        if paid_at:
            update_data["paid_at"] = paid_at

        if preimage:
            update_data["transaction_id"] = preimage  # Store preimage as proof of payment

        self.supabase.table("contributions") \
            .update(update_data) \
            .eq("bitnob_payment_hash", payment_hash) \
            .execute()

        logger.info(f"Contribution with payment_hash {payment_hash} marked as {status}")

    def _update_contribution_status_by_id(self, contribution_id: str, status: str):
        """Update contribution status by ID"""
        self.supabase.table("contributions") \
            .update({
                "payment_status": status,
                "updated_at": datetime.utcnow().isoformat()
            }) \
            .eq("id", contribution_id) \
            .execute()

        logger.info(f"Contribution {contribution_id} marked as {status}")

    def _update_campaign_amount(self, contribution_id: str, campaign_id: str):
        """Update campaign's current_amount when contribution is paid"""
        # Get contribution amount
        contrib = (
            self.supabase.table("contributions")
            .select("amount")
            .eq("id", contribution_id)
            .single()
            .execute()
        )

        if not contrib.data:
            logger.error(f"Contribution {contribution_id} not found")
            return

        # Get current campaign amount
        campaign = (
            self.supabase.table("campaigns")
            .select("current_amount")
            .eq("id", campaign_id)
            .single()
            .execute()
        )

        if not campaign.data:
            logger.error(f"Campaign {campaign_id} not found")
            return

        # Calculate platform fee and creator amount
        contribution_amount = contrib.data["amount"]
        platform_fee_percent = Config.PLATFORM_FEE_PERCENT / 100
        platform_fee = contribution_amount * platform_fee_percent
        creator_amount = contribution_amount - platform_fee

        # Update campaign with creator amount (after fee)
        new_amount = campaign.data["current_amount"] + creator_amount

        self.supabase.table("campaigns") \
            .update({
                "current_amount": new_amount,
                "updated_at": datetime.utcnow().isoformat()
            }) \
            .eq("id", campaign_id) \
            .execute()

        logger.info(
            f"Campaign {campaign_id} amount updated to {new_amount} "
            f"(+{creator_amount} sats after {platform_fee} sats fee)"
        )

    def get_active_polls(self) -> list:
        """Get list of contribution IDs currently being polled"""
        return list(self.polling_threads.keys())

    def stop_all_polling(self):
        """Stop all active polling threads"""
        for contribution_id in list(self.stop_flags.keys()):
            self.stop_polling(contribution_id)

    def handle_webhook_payment(
        self,
        payment_hash: str,
        campaign_id: Optional[str] = None
    ) -> bool:
        """
        Handle payment confirmation from LNbits webhook

        This is called when LNbits sends a webhook notification.
        It updates the contribution and campaign, then stops any active polling.

        Args:
            payment_hash: The payment hash from the webhook
            campaign_id: Optional campaign ID (looked up if not provided)

        Returns:
            True if payment was processed successfully
        """
        try:
            # Find contribution by payment hash
            response = (
                self.supabase.table("contributions")
                .select("id, campaign_id, amount, payment_status")
                .eq("bitnob_payment_hash", payment_hash)
                .single()
                .execute()
            )

            if not response.data:
                logger.warning(f"No contribution found for payment_hash: {payment_hash}")
                return False

            contribution = response.data
            contribution_id = contribution["id"]

            # Check if already paid
            if contribution["payment_status"] == "paid":
                logger.info(f"Contribution {contribution_id} already paid")
                return True

            # Update contribution status
            self._update_contribution_status_by_payment_hash(
                payment_hash=payment_hash,
                status="paid",
                paid_at=datetime.utcnow().isoformat()
            )

            # Update campaign amount
            self._update_campaign_amount(
                contribution_id,
                campaign_id or contribution["campaign_id"]
            )

            # Stop polling if active
            self.stop_polling(contribution_id)

            logger.info(f"Webhook payment processed for contribution {contribution_id}")
            return True

        except Exception as e:
            logger.error(f"Error handling webhook payment: {str(e)}")
            return False
