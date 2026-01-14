import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional

from .bitnob import BitnobService, BitnobAPIError
from .supabase_client import get_supabase_client
from config import Config

logger = logging.getLogger(__name__)


class InvoicePollingService:
    """Service for polling Bitnob Lightning invoices and updating contributions"""

    def __init__(self):
        self.bitnob_service = BitnobService()
        self.supabase = get_supabase_client()
        self.polling_threads: Dict[str, threading.Thread] = {}
        self.stop_flags: Dict[str, threading.Event] = {}

    def start_polling(
        self,
        contribution_id: str,
        payment_id: str,
        campaign_id: str,
        callback: Optional[Callable] = None
    ):
        if contribution_id in self.polling_threads:
            logger.warning(f"Polling already active for contribution {contribution_id}")
            return

        stop_flag = threading.Event()
        self.stop_flags[contribution_id] = stop_flag

        thread = threading.Thread(
            target=self._poll_payment,
            args=(contribution_id, payment_id, campaign_id, stop_flag, callback),
            daemon=True
        )

        self.polling_threads[contribution_id] = thread
        thread.start()

        logger.info(f"Started polling for contribution {contribution_id}")

    def stop_polling(self, contribution_id: str):
        if contribution_id in self.stop_flags:
            self.stop_flags[contribution_id].set()
            logger.info(f"Stopped polling for contribution {contribution_id}")

    def _poll_payment(
        self,
        contribution_id: str,
        payment_id: str,
        campaign_id: str,
        stop_flag: threading.Event,
        callback: Optional[Callable]
    ):
        start_time = datetime.utcnow()
        timeout = timedelta(seconds=Config.POLLING_TIMEOUT)
        interval = Config.POLLING_INTERVAL

        try:
            while not stop_flag.is_set():
                if datetime.utcnow() - start_time > timeout:
                    logger.warning(f"Polling timeout for contribution {contribution_id}")
                    self._update_contribution_status_by_id(contribution_id, "expired")
                    break

                try:
                    status_data = self.bitnob_service.get_lightning_payment_status(payment_id)

                    if status_data["paid"]:
                        reference = status_data["reference"]

                        if self._already_paid(reference):
                            logger.info("Contribution already marked as paid, skipping")
                            break

                        self._update_contribution_status_by_reference(
                            reference=reference,
                            status="paid",
                            paid_at=status_data.get("paid_at"),
                            transaction_id=status_data.get("transaction_id")
                        )

                        self._update_campaign_amount(contribution_id, campaign_id)

                        if callback:
                            callback(contribution_id, status_data)

                        break

                    elif status_data["status"] in ["expired", "cancelled", "failed"]:
                        self._update_contribution_status_by_id(
                            contribution_id,
                            status_data["status"]
                        )
                        break

                except BitnobAPIError as e:
                    logger.error(f"Bitnob polling error: {str(e)}")

                stop_flag.wait(interval)

        except Exception as e:
            logger.error(f"Unexpected polling error: {str(e)}")
            self._update_contribution_status_by_id(contribution_id, "failed")

        finally:
            self.polling_threads.pop(contribution_id, None)
            self.stop_flags.pop(contribution_id, None)

    def _already_paid(self, reference: str) -> bool:
        response = (
            self.supabase.table("contributions")
            .select("payment_status")
            .eq("bitnob_reference", reference)
            .single()
            .execute()
        )
        return response.data and response.data["payment_status"] == "paid"

    def _update_contribution_status_by_reference(
        self,
        reference: str,
        status: str,
        paid_at: Optional[str] = None,
        transaction_id: Optional[str] = None
    ):
        update_data = {
            "payment_status": status,
            "updated_at": datetime.utcnow().isoformat()
        }

        if paid_at:
            update_data["paid_at"] = paid_at

        if transaction_id:
            update_data["transaction_id"] = transaction_id

        self.supabase.table("contributions") \
            .update(update_data) \
            .eq("bitnob_reference", reference) \
            .execute()

        logger.info(f"Contribution {reference} marked as {status}")

    def _update_contribution_status_by_id(self, contribution_id: str, status: str):
        self.supabase.table("contributions") \
            .update({
                "payment_status": status,
                "updated_at": datetime.utcnow().isoformat()
            }) \
            .eq("id", contribution_id) \
            .execute()

        logger.info(f"Contribution {contribution_id} marked as {status}")

    def _update_campaign_amount(self, contribution_id: str, campaign_id: str):
        contrib = (
            self.supabase.table("contributions")
            .select("amount")
            .eq("id", contribution_id)
            .single()
            .execute()
        )

        campaign = (
            self.supabase.table("campaigns")
            .select("current_amount")
            .eq("id", campaign_id)
            .single()
            .execute()
        )

        new_amount = campaign.data["current_amount"] + contrib.data["amount"]

        self.supabase.table("campaigns") \
            .update({
                "current_amount": new_amount,
                "updated_at": datetime.utcnow().isoformat()
            }) \
            .eq("id", campaign_id) \
            .execute()

        logger.info(f"Campaign {campaign_id} amount updated to {new_amount}")

    def get_active_polls(self) -> list:
        return list(self.polling_threads.keys())

    def stop_all_polling(self):
        for contribution_id in list(self.stop_flags.keys()):
            self.stop_polling(contribution_id)
