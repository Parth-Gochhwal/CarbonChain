"""
CarbonChain - AI Claim Consistency Verdict Models

This module defines the data contracts for AI-derived MRV consistency evaluation.
The AI Consistency Engine compares AI-derived MRV results against claimant-declared
carbon estimates and produces an explainable, auditable verdict.

DESIGN PRINCIPLES:
1. DETERMINISTIC: All logic is rule-based, not ML-based. Results are reproducible.
2. EXPLAINABLE: Every verdict includes a clear explanation of the reasoning.
3. CONSERVATIVE: The system errs on the side of caution when evaluating claims.
4. TRANSPARENT: All assumptions and calculations are documented.

VERDICT CATEGORIES:
- STRONGLY_SUPPORTS: AI range fully overlaps claim range (high confidence alignment)
- PARTIALLY_SUPPORTS: AI range partially overlaps claim range (moderate alignment)
- CONTRADICTS: No overlap between AI and claim ranges (potential discrepancy)

TRUST BUILDING:
- Conservative logic prevents false positives (approving bad claims)
- Explainable verdicts enable human reviewers to understand AI reasoning
- Public transparency allows community oversight of AI decisions
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AIVerdict(str, Enum):
    """
    Verdict categories for AI claim consistency evaluation.
    
    These verdicts indicate how well the AI-derived MRV estimate aligns
    with the claimant's declared carbon impact estimate.
    
    STRONGLY_SUPPORTS:
        The AI estimate range fully overlaps with the claim range.
        This indicates high confidence that the claim is consistent with
        satellite-based observations. The claimant's estimate is well-supported
        by independent verification.
    
    PARTIALLY_SUPPORTS:
        The AI estimate range partially overlaps with the claim range.
        This indicates moderate alignment - there is some agreement but also
        some discrepancy. Human review may be needed to reconcile differences.
    
    CONTRADICTS:
        The AI estimate range does not overlap with the claim range.
        This indicates a significant discrepancy that requires investigation.
        The claim may be inaccurate, or there may be methodological differences
        that need to be addressed.
    """
    STRONGLY_SUPPORTS = "strongly_supports"
    PARTIALLY_SUPPORTS = "partially_supports"
    CONTRADICTS = "contradicts"


class AIConsistencyResult(BaseModel):
    """
    Result of AI claim consistency evaluation.
    
    This model captures the comparison between:
    - Claimant-declared carbon impact (claimed_min_co2e, claimed_max_co2e)
    - AI-derived MRV estimate (estimated_min_co2e, estimated_max_co2e)
    
    The evaluation produces:
    - A verdict (STRONGLY_SUPPORTS, PARTIALLY_SUPPORTS, or CONTRADICTS)
    - A deviation percentage (distance between range midpoints)
    - A confidence score (0-1) based on NDVI magnitude, area size, and overlap
    - An explanation of the reasoning
    
    CONSERVATIVE ASSUMPTIONS:
    - Overlap detection uses strict range boundaries (no fuzzy matching)
    - Confidence scores are conservative (lower bound estimates)
    - Deviations are calculated from midpoints to avoid edge case bias
    
    TRANSPARENCY:
    - All calculations are deterministic and reproducible
    - Explanations document the exact logic used
    - Confidence scores are derived from simple, documented heuristics
    """
    claim_id: UUID = Field(
        ...,
        description="ID of the claim being evaluated"
    )
    claimed_min_co2e: float = Field(
        ...,
        ge=0,
        description="Lower bound of claimant-declared carbon impact (tonnes CO2e)"
    )
    claimed_max_co2e: float = Field(
        ...,
        ge=0,
        description="Upper bound of claimant-declared carbon impact (tonnes CO2e)"
    )
    estimated_min_co2e: float = Field(
        ...,
        ge=0,
        description="Lower bound of AI-derived MRV estimate (tonnes CO2e)"
    )
    estimated_max_co2e: float = Field(
        ...,
        ge=0,
        description="Upper bound of AI-derived MRV estimate (tonnes CO2e)"
    )
    deviation_percent: float = Field(
        ...,
        description="Percentage deviation between claim and AI estimate midpoints"
    )
    verdict: AIVerdict = Field(
        ...,
        description="Consistency verdict (STRONGLY_SUPPORTS, PARTIALLY_SUPPORTS, CONTRADICTS)"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence score (0-1) in the alignment between AI MRV estimate and claim. "
            "This represents confidence in the consistency evaluation, not verification confidence."
        )
    )
    explanation: str = Field(
        ...,
        min_length=10,
        description="Human-readable explanation of the verdict and reasoning"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the consistency evaluation was performed"
    )

    class Config:
        """Pydantic configuration for the AIConsistencyResult model."""
        json_schema_extra = {
            "example": {
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "claimed_min_co2e": 150.0,
                "claimed_max_co2e": 300.0,
                "estimated_min_co2e": 135.0,
                "estimated_max_co2e": 270.0,
                "deviation_percent": -10.0,
                "verdict": "strongly_supports",
                "confidence_score": 0.85,
                "explanation": "AI estimate range (135-270 tCO2e) fully overlaps with claim range (150-300 tCO2e). Deviation of -10% indicates conservative AI estimate. High confidence due to strong NDVI signal and adequate area coverage.",
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
"""
CarbonChain - AI Claim Consistency Verdict Models

This module defines the data contracts for AI-derived MRV consistency evaluation.
The AI Consistency Engine compares AI-derived MRV results against claimant-declared
carbon estimates and produces an explainable, auditable verdict.

DESIGN PRINCIPLES:
1. DETERMINISTIC: All logic is rule-based, not ML-based. Results are reproducible.
2. EXPLAINABLE: Every verdict includes a clear explanation of the reasoning.
3. CONSERVATIVE: The system errs on the side of caution when evaluating claims.
4. TRANSPARENT: All assumptions and calculations are documented.

VERDICT CATEGORIES:
- STRONGLY_SUPPORTS: AI range fully overlaps claim range (high confidence alignment)
- PARTIALLY_SUPPORTS: AI range partially overlaps claim range (moderate alignment)
- CONTRADICTS: No overlap between AI and claim ranges (potential discrepancy)

TRUST BUILDING:
- Conservative logic prevents false positives (approving bad claims)
- Explainable verdicts enable human reviewers to understand AI reasoning
- Public transparency allows community oversight of AI decisions
"""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AIVerdict(str, Enum):
    """
    Verdict categories for AI claim consistency evaluation.
    
    These verdicts indicate how well the AI-derived MRV estimate aligns
    with the claimant's declared carbon impact estimate.
    
    STRONGLY_SUPPORTS:
        The AI estimate range fully overlaps with the claim range.
        This indicates high confidence that the claim is consistent with
        satellite-based observations. The claimant's estimate is well-supported
        by independent verification.
    
    PARTIALLY_SUPPORTS:
        The AI estimate range partially overlaps with the claim range.
        This indicates moderate alignment - there is some agreement but also
        some discrepancy. Human review may be needed to reconcile differences.
    
    CONTRADICTS:
        The AI estimate range does not overlap with the claim range.
        This indicates a significant discrepancy that requires investigation.
        The claim may be inaccurate, or there may be methodological differences
        that need to be addressed.
    """
    STRONGLY_SUPPORTS = "strongly_supports"
    PARTIALLY_SUPPORTS = "partially_supports"
    CONTRADICTS = "contradicts"


class AIConsistencyResult(BaseModel):
    """
    Result of AI claim consistency evaluation.
    
    This model captures the comparison between:
    - Claimant-declared carbon impact (claimed_min_co2e, claimed_max_co2e)
    - AI-derived MRV estimate (estimated_min_co2e, estimated_max_co2e)
    
    The evaluation produces:
    - A verdict (STRONGLY_SUPPORTS, PARTIALLY_SUPPORTS, or CONTRADICTS)
    - A deviation percentage (distance between range midpoints)
    - A confidence score (0-1) based on NDVI magnitude, area size, and overlap
    - An explanation of the reasoning
    
    CONSERVATIVE ASSUMPTIONS:
    - Overlap detection uses strict range boundaries (no fuzzy matching)
    - Confidence scores are conservative (lower bound estimates)
    - Deviations are calculated from midpoints to avoid edge case bias
    
    TRANSPARENCY:
    - All calculations are deterministic and reproducible
    - Explanations document the exact logic used
    - Confidence scores are derived from simple, documented heuristics
    """
    claim_id: UUID = Field(
        ...,
        description="ID of the claim being evaluated"
    )
    claimed_min_co2e: float = Field(
        ...,
        ge=0,
        description="Lower bound of claimant-declared carbon impact (tonnes CO2e)"
    )
    claimed_max_co2e: float = Field(
        ...,
        ge=0,
        description="Upper bound of claimant-declared carbon impact (tonnes CO2e)"
    )
    estimated_min_co2e: float = Field(
        ...,
        ge=0,
        description="Lower bound of AI-derived MRV estimate (tonnes CO2e)"
    )
    estimated_max_co2e: float = Field(
        ...,
        ge=0,
        description="Upper bound of AI-derived MRV estimate (tonnes CO2e)"
    )
    deviation_percent: float = Field(
        ...,
        description="Percentage deviation between claim and AI estimate midpoints"
    )
    verdict: AIVerdict = Field(
        ...,
        description="Consistency verdict (STRONGLY_SUPPORTS, PARTIALLY_SUPPORTS, CONTRADICTS)"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Confidence score (0-1) in the alignment between AI MRV estimate and claim. "
            "This represents confidence in the consistency evaluation, not verification confidence."
        )
    )
    explanation: str = Field(
        ...,
        min_length=10,
        description="Human-readable explanation of the verdict and reasoning"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the consistency evaluation was performed"
    )

    class Config:
        """Pydantic configuration for the AIConsistencyResult model."""
        json_schema_extra = {
            "example": {
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "claimed_min_co2e": 150.0,
                "claimed_max_co2e": 300.0,
                "estimated_min_co2e": 135.0,
                "estimated_max_co2e": 270.0,
                "deviation_percent": -10.0,
                "verdict": "strongly_supports",
                "confidence_score": 0.85,
                "explanation": "AI estimate range (135-270 tCO2e) fully overlaps with claim range (150-300 tCO2e). Deviation of -10% indicates conservative AI estimate. High confidence due to strong NDVI signal and adequate area coverage.",
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
