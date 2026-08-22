from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class RiskTier(str, Enum):
    ALLOW = "ALLOW"
    STEP_UP_OTP = "STEP_UP_OTP"
    BLOCK = "BLOCK"


class FastPathVerdict(str, Enum):
    CLEAN = "CLEAN"
    NEEDS_DEEP_EVALUATION = "NEEDS_DEEP_EVALUATION"


class TransactionPayload(BaseModel):
    transaction_id: str = Field(..., description="Unique payment gateway transaction reference")
    merchant_id: str = Field(..., description="Merchant account identifier")
    amount: float = Field(..., gt=0, description="Authorized transaction amount")
    currency: str = Field(default="INR", max_length=3)
    customer_email: EmailStr = Field(..., description="Customer email address")
    ip_address: str = Field(..., description="IPv4 or IPv6 originating address")
    device_fingerprint: str = Field(..., description="Canvas/hardware client hash")
    shipping_address: str = Field(..., description="Destination shipping address")
    billing_address: str = Field(..., description="Cardholder/source billing address")
    historical_order_count: int = Field(default=0, ge=0, description="Total successful historical orders")
    is_cod: bool = Field(default=False, description="Cash on Delivery order flag")


class FastPathResult(BaseModel):
    verdict: FastPathVerdict
    heuristics_triggered: List[str] = Field(default_factory=list)
    initial_score: int = Field(default=0, ge=0, le=100)


class RiskAssessmentResult(BaseModel):
    transaction_id: str
    risk_tier: RiskTier
    risk_score: int = Field(..., ge=0, le=100, description="Risk index between 0 (safe) and 100 (fraudulent)")
    detected_anomalies: List[str] = Field(default_factory=list)
    plain_text_reasoning: str = Field(..., description="Deterministic or LLM audit trail explaining the verdict")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Engine model confidence")


class RazorpayPaymentEntity(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    email: EmailStr
    contact: Optional[str] = None
    notes: Dict[str, Any] = Field(default_factory=dict)


class RazorpayWebhookEvent(BaseModel):
    entity: str
    account_id: str
    event: str
    payload: Dict[str, Any]
