"""
CarbonChain - Human Review Models for Governance Layer

This module defines the data contracts for human verification reviews.
Reviews are part of the trust layer that sits AFTER AI MRV verification
and BEFORE carbon credit minting.

GOVERNANCE FLOW:
1. AI_VERIFIED → Authority reviews claim
2. AUTHORITY_REVIEWED → Community reviews claim
3. COMMUNITY_REVIEWED → Eligible for minting (if both approved)

This ensures transparent, multi-stakeholder oversight of carbon claims.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ReviewRole(str, Enum):
    """
    Role of the reviewer in the governance process.
    
    AUTHORITY: Government regulator or certified auditor
    COMMUNITY: NGO, public observer, or transparency watchdog
    """
    AUTHORITY = "authority"
    COMMUNITY = "community"


class ReviewDecision(str, Enum):
    """
    Decision outcome of a review.
    
    APPROVE: Reviewer endorses the claim moving forward
    REJECT: Reviewer blocks the claim with stated concerns
    """
    APPROVE = "approve"
    REJECT = "reject"


class CreditStatus(str, Enum):
    """
    Lifecycle status of a minted carbon credit.
    
    ACTIVE: Credit is valid and fully intact
    AT_RISK: Credit has degradation warning but not yet burned
    PARTIALLY_BURNED: Credit has been partially burned due to degradation
    FULLY_BURNED: Credit has been fully burned due to severe degradation
    """
    ACTIVE = "active"
    AT_RISK = "at_risk"
    PARTIALLY_BURNED = "partially_burned"
    FULLY_BURNED = "fully_burned"


class ReviewSubmission(BaseModel):
    """
    Input model for submitting a review.
    
    This is what a reviewer provides when evaluating a claim.
    Does not include system-generated fields like ID or timestamps.
    """
    claim_id: UUID = Field(
        ...,
        description="ID of the claim being reviewed"
    )
    reviewer_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Identifier for the reviewer (name, org, or ID)"
    )
    decision: ReviewDecision = Field(
        ...,
        description="Reviewer's decision: approve or reject"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Reviewer's confidence in their decision (0-1 scale)"
    )
    positives: list[str] = Field(
        default_factory=list,
        description="Points in favor of the claim (supporting evidence, compliance, etc.)"
    )
    concerns: list[str] = Field(
        default_factory=list,
        description="Points against the claim (issues, gaps, risks)"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Additional notes or commentary from the reviewer"
    )


class ReviewRecord(ReviewSubmission):
    """
    Complete review record including system-generated fields.
    
    Extends ReviewSubmission with ID, role, and timestamp.
    This is the full review object stored and tracked by the system.
    """
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this review"
    )
    role: ReviewRole = Field(
        ...,
        description="Role of the reviewer (authority or community)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the review was submitted"
    )

    class Config:
        """Pydantic configuration for the ReviewRecord model."""
        json_schema_extra = {
            "example": {
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "reviewer_id": "Ministry of Environment - Inspector #42",
                "decision": "approve",
                "confidence_score": 0.85,
                "positives": [
                    "Satellite imagery confirms vegetation increase",
                    "Carbon estimates within reasonable range",
                    "Documentation is complete"
                ],
                "concerns": [
                    "Baseline period could be longer for accuracy"
                ],
                "notes": "Recommend continued monitoring for next verification cycle.",
                "role": "authority"
            }
        }


class MintedCredit(BaseModel):
    """
    Simulated carbon credit token (MVP placeholder).
    
    IMPORTANT: This is NOT a real blockchain token.
    This is a simulated representation for demonstration purposes only.
    Real implementation would use ERC-20 or similar standard on a blockchain.
    
    CREDIT LIFECYCLE:
    Credits start as ACTIVE with full amount. Post-mint monitoring can detect
    degradation and trigger partial or full burns based on NDVI changes.
    """
    token_id: UUID = Field(
        default_factory=uuid4,
        description="Simulated unique token identifier"
    )
    claim_id: UUID = Field(
        ...,
        description="ID of the verified claim this credit represents"
    )
    amount_tonnes_co2e: float = Field(
        ...,
        ge=0,
        description="Original amount of CO2e this credit represents (in tonnes) at mint time"
    )
    status: CreditStatus = Field(
        default=CreditStatus.ACTIVE,
        description="Current lifecycle status of the credit"
    )
    remaining_tonnes_co2e: float = Field(
        ...,
        ge=0,
        description="Remaining CO2e amount after any burns (in tonnes)"
    )
    baseline_ndvi: Optional[float] = Field(
        default=None,
        description="Baseline NDVI value recorded at mint time for monitoring"
    )
    minted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the credit was minted"
    )
    # Transparency: clearly label as simulated
    is_simulated: bool = Field(
        default=True,
        description="Flag indicating this is a simulated credit (MVP only)"
    )
    label: str = Field(
        default="Simulated ERC-20 carbon credit (MVP)",
        description="Human-readable label for transparency"
    )

    class Config:
        """Pydantic configuration for the MintedCredit model."""
        json_schema_extra = {
            "example": {
                "token_id": "660e8400-e29b-41d4-a716-446655440001",
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount_tonnes_co2e": 120.0,
                "status": "active",
                "remaining_tonnes_co2e": 120.0,
                "baseline_ndvi": 0.58,
                "minted_at": "2025-07-01T12:00:00Z",
                "is_simulated": True,
                "label": "Simulated ERC-20 carbon credit (MVP)"
            }
        }
"""
CarbonChain - Human Review Models for Governance Layer

This module defines the data contracts for human verification reviews.
Reviews are part of the trust layer that sits AFTER AI MRV verification
and BEFORE carbon credit minting.

GOVERNANCE FLOW:
1. AI_VERIFIED → Authority reviews claim
2. AUTHORITY_REVIEWED → Community reviews claim
3. COMMUNITY_REVIEWED → Eligible for minting (if both approved)

This ensures transparent, multi-stakeholder oversight of carbon claims.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ReviewRole(str, Enum):
    """
    Role of the reviewer in the governance process.
    
    AUTHORITY: Government regulator or certified auditor
    COMMUNITY: NGO, public observer, or transparency watchdog
    """
    AUTHORITY = "authority"
    COMMUNITY = "community"


class ReviewDecision(str, Enum):
    """
    Decision outcome of a review.
    
    APPROVE: Reviewer endorses the claim moving forward
    REJECT: Reviewer blocks the claim with stated concerns
    """
    APPROVE = "approve"
    REJECT = "reject"


class CreditStatus(str, Enum):
    """
    Lifecycle status of a minted carbon credit.
    
    ACTIVE: Credit is valid and fully intact
    AT_RISK: Credit has degradation warning but not yet burned
    PARTIALLY_BURNED: Credit has been partially burned due to degradation
    FULLY_BURNED: Credit has been fully burned due to severe degradation
    """
    ACTIVE = "active"
    AT_RISK = "at_risk"
    PARTIALLY_BURNED = "partially_burned"
    FULLY_BURNED = "fully_burned"


class ReviewSubmission(BaseModel):
    """
    Input model for submitting a review.
    
    This is what a reviewer provides when evaluating a claim.
    Does not include system-generated fields like ID or timestamps.
    """
    claim_id: UUID = Field(
        ...,
        description="ID of the claim being reviewed"
    )
    reviewer_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Identifier for the reviewer (name, org, or ID)"
    )
    decision: ReviewDecision = Field(
        ...,
        description="Reviewer's decision: approve or reject"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Reviewer's confidence in their decision (0-1 scale)"
    )
    positives: list[str] = Field(
        default_factory=list,
        description="Points in favor of the claim (supporting evidence, compliance, etc.)"
    )
    concerns: list[str] = Field(
        default_factory=list,
        description="Points against the claim (issues, gaps, risks)"
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Additional notes or commentary from the reviewer"
    )


class ReviewRecord(ReviewSubmission):
    """
    Complete review record including system-generated fields.
    
    Extends ReviewSubmission with ID, role, and timestamp.
    This is the full review object stored and tracked by the system.
    """
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this review"
    )
    role: ReviewRole = Field(
        ...,
        description="Role of the reviewer (authority or community)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the review was submitted"
    )

    class Config:
        """Pydantic configuration for the ReviewRecord model."""
        json_schema_extra = {
            "example": {
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "reviewer_id": "Ministry of Environment - Inspector #42",
                "decision": "approve",
                "confidence_score": 0.85,
                "positives": [
                    "Satellite imagery confirms vegetation increase",
                    "Carbon estimates within reasonable range",
                    "Documentation is complete"
                ],
                "concerns": [
                    "Baseline period could be longer for accuracy"
                ],
                "notes": "Recommend continued monitoring for next verification cycle.",
                "role": "authority"
            }
        }


class MintedCredit(BaseModel):
    """
    Simulated carbon credit token (MVP placeholder).
    
    IMPORTANT: This is NOT a real blockchain token.
    This is a simulated representation for demonstration purposes only.
    Real implementation would use ERC-20 or similar standard on a blockchain.
    
    CREDIT LIFECYCLE:
    Credits start as ACTIVE with full amount. Post-mint monitoring can detect
    degradation and trigger partial or full burns based on NDVI changes.
    """
    token_id: UUID = Field(
        default_factory=uuid4,
        description="Simulated unique token identifier"
    )
    claim_id: UUID = Field(
        ...,
        description="ID of the verified claim this credit represents"
    )
    amount_tonnes_co2e: float = Field(
        ...,
        ge=0,
        description="Original amount of CO2e this credit represents (in tonnes) at mint time"
    )
    status: CreditStatus = Field(
        default=CreditStatus.ACTIVE,
        description="Current lifecycle status of the credit"
    )
    remaining_tonnes_co2e: float = Field(
        ...,
        ge=0,
        description="Remaining CO2e amount after any burns (in tonnes)"
    )
    baseline_ndvi: Optional[float] = Field(
        default=None,
        description="Baseline NDVI value recorded at mint time for monitoring"
    )
    minted_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the credit was minted"
    )
    # Transparency: clearly label as simulated
    is_simulated: bool = Field(
        default=True,
        description="Flag indicating this is a simulated credit (MVP only)"
    )
    label: str = Field(
        default="Simulated ERC-20 carbon credit (MVP)",
        description="Human-readable label for transparency"
    )

    class Config:
        """Pydantic configuration for the MintedCredit model."""
        json_schema_extra = {
            "example": {
                "token_id": "660e8400-e29b-41d4-a716-446655440001",
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "amount_tonnes_co2e": 150.5,
                "minted_at": "2025-01-08T12:00:00Z",
                "is_simulated": True,
                "label": "Simulated ERC-20 carbon credit (MVP)"
            }
        }
