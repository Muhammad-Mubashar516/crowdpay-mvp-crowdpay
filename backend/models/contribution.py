from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator

class Contribution(BaseModel):
    """Contribution model for campaign donations"""
    
    id: Optional[str] = None
    campaign_id: str = Field(..., min_length=1)
    contributor_name: Optional[str] = Field(None, max_length=100)
    contributor_email: Optional[str] = None
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD")
    payment_status: str = Field(default="pending")
    bitnob_payment_id: Optional[str] = None
    bitnob_payment_request: Optional[str] = None
    bitnob_payment_hash: Optional[str] = None
    bitnob_reference: Optional[str] = None
    transaction_id: Optional[str] = None
    message: Optional[str] = Field(None, max_length=500)
    is_anonymous: bool = Field(default=False)
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    
    @validator('payment_status')
    def validate_payment_status(cls, v):
        allowed_statuses = ['pending', 'paid', 'failed', 'expired', 'cancelled']
        if v not in allowed_statuses:
            raise ValueError(f"Payment status must be one of {allowed_statuses}")
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        allowed_currencies = ['USD', 'BTC', 'SATS']
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
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Contribution':
        """Create Contribution instance from dictionary"""
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
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    