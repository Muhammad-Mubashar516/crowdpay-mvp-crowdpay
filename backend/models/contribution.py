from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class Contribution(BaseModel):
    """
    Contribution model for campaign donations

    Lightning Payment Flow:
    1. User initiates contribution via POST /api/contributions
    2. Backend creates LNbits invoice and returns payment_request (BOLT11)
    3. Frontend displays QR code for user to scan/pay
    4. Backend polls LNbits OR receives webhook for payment confirmation
    5. On payment, contribution status updated to 'paid' and campaign amount incremented
    """

    id: Optional[str] = None
    campaign_id: str = Field(..., min_length=1)
    contributor_name: Optional[str] = Field(None, max_length=100)
    contributor_email: Optional[str] = None
    amount: float = Field(..., gt=0)  # Amount in satoshis
    currency: str = Field(default="SATS")  # Lightning-only: always SATS
    payment_status: str = Field(default="pending")

    # LNbits payment fields
    lnbits_payment_hash: Optional[str] = None  # Unique payment identifier from LNbits
    lnbits_payment_request: Optional[str] = None  # BOLT11 invoice string
    lnbits_checking_id: Optional[str] = None  # ID for checking payment status

    # Legacy field names for database compatibility (will be migrated)
    # These map to the old bitnob_* columns until DB migration is complete
    bitnob_payment_id: Optional[str] = None
    bitnob_payment_request: Optional[str] = None
    bitnob_payment_hash: Optional[str] = None
    bitnob_reference: Optional[str] = None

    transaction_id: Optional[str] = None  # Preimage (proof of payment)
    message: Optional[str] = Field(None, max_length=500)
    is_anonymous: bool = Field(default=False)
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    # Platform fee tracking
    platform_fee: Optional[float] = None  # Fee amount in satoshis
    creator_amount: Optional[float] = None  # Amount after fee deduction

    @validator('payment_status')
    def validate_payment_status(cls, v):
        allowed_statuses = ['pending', 'paid', 'failed', 'expired', 'cancelled']
        if v not in allowed_statuses:
            raise ValueError(f"Payment status must be one of {allowed_statuses}")
        return v

    @validator('currency')
    def validate_currency(cls, v):
        # Lightning-only: we only accept SATS
        # Keep BTC for display purposes (will be converted to SATS)
        allowed_currencies = ['SATS', 'BTC']
        if v not in allowed_currencies:
            raise ValueError(f"Currency must be one of {allowed_currencies}")
        return v

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database operations"""
        data = self.dict(exclude_none=True)

        # Convert datetime objects to ISO format strings
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.paid_at:
            data['paid_at'] = self.paid_at.isoformat()

        # Map new field names to legacy database columns (until migration)
        # This ensures compatibility with existing database schema
        if self.lnbits_payment_hash and 'bitnob_payment_hash' not in data:
            data['bitnob_payment_hash'] = self.lnbits_payment_hash
        if self.lnbits_payment_request and 'bitnob_payment_request' not in data:
            data['bitnob_payment_request'] = self.lnbits_payment_request
        if self.lnbits_checking_id and 'bitnob_payment_id' not in data:
            data['bitnob_payment_id'] = self.lnbits_checking_id

        # Remove new field names that don't exist in DB yet
        data.pop('lnbits_payment_hash', None)
        data.pop('lnbits_payment_request', None)
        data.pop('lnbits_checking_id', None)
        data.pop('platform_fee', None)
        data.pop('creator_amount', None)

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contribution':
        """Create Contribution instance from dictionary"""
        # Map legacy field names to new ones for internal use
        if 'bitnob_payment_hash' in data:
            data['lnbits_payment_hash'] = data.get('bitnob_payment_hash')
        if 'bitnob_payment_request' in data:
            data['lnbits_payment_request'] = data.get('bitnob_payment_request')
        if 'bitnob_payment_id' in data:
            data['lnbits_checking_id'] = data.get('bitnob_payment_id')

        return cls(**data)

    def is_paid(self) -> bool:
        """Check if contribution has been paid"""
        return self.payment_status == 'paid'

    def is_pending(self) -> bool:
        """Check if contribution is pending payment"""
        return self.payment_status == 'pending'

    def display_name(self) -> str:
        """Get display name for contributor"""
        if self.is_anonymous:
            return "Anonymous"
        return self.contributor_name or "Anonymous"

    def get_payment_hash(self) -> Optional[str]:
        """Get payment hash (supports both new and legacy field names)"""
        return self.lnbits_payment_hash or self.bitnob_payment_hash

    def get_payment_request(self) -> Optional[str]:
        """Get payment request/invoice (supports both new and legacy field names)"""
        return self.lnbits_payment_request or self.bitnob_payment_request

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
