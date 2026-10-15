from typing import List, Optional
from pydantic import BaseModel, Field


class OfferInfo(BaseModel):
    company_name: Optional[str] = None
    role: Optional[str] = None
    recruiter_email: Optional[str] = None
    company_website: Optional[str] = None
    contact_channel: Optional[str] = None  # email / whatsapp / telegram / other
    fee_requested: Optional[str] = None
    stipend_or_salary: Optional[str] = None
    urgency_language: bool = False


class RedFlag(BaseModel):
    flag: str
    severity: str  # low / medium / high
    evidence: str  # quote from offer, a URL, or a KB source file name


class RiskReport(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    verdict: str  # Likely Genuine / Suspicious / Likely Scam
    red_flags: List[RedFlag]
    reasoning: str
    reply_to_recruiter: str
    next_steps: List[str]


def verdict_for(score: int) -> str:
    if score <= 30:
        return "Likely Genuine"
    if score <= 65:
        return "Suspicious"
    return "Likely Scam"
