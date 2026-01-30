"""
CarbonChain - Verification Result Models

This module defines the data contracts for claim verification.
Verification assesses the validity of a claim and provides an independent
carbon impact estimate with uncertainty quantification.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from backend.app.models.claim import EvidenceType


class VerificationStatus(str, Enum):
    """
    Status of the verification process.
    
    MVP assumption: Verification is a single-pass process.
    Production might have multiple review stages.
    """
    PENDING = "pending"          # Verification not yet started
    IN_PROGRESS = "in_progress"  # Verification underway
    COMPLETED = "completed"      # Verification finished (see outcome for result)
    FAILED = "failed"            # Verification process failed (technical issue)


class VerificationOutcome(str, Enum):
    """
    Result of a completed verification.
    
    MVP assumption: Simple pass/fail with a 'needs_review' option
    for edge cases requiring human judgment.
    """
    APPROVED = "approved"            # Claim verified and approved
    REJECTED = "rejected"            # Claim could not be verified
    NEEDS_REVIEW = "needs_review"    # Requires additional human review
    INCONCLUSIVE = "inconclusive"    # Insufficient data to determine


class ConfidenceLevel(str, Enum):
    """
    Qualitative confidence in the verification result.
    
    MVP assumption: Using qualitative levels rather than precise percentages
    because verification confidence is inherently subjective in MVP stage.
    """
    HIGH = "high"           # Strong evidence, high certainty (>80% confident)
    MEDIUM = "medium"       # Reasonable evidence, moderate certainty (50-80%)
    LOW = "low"             # Limited evidence, low certainty (20-50%)
    VERY_LOW = "very_low"   # Minimal evidence, very uncertain (<20%)


class DataQualityFlag(str, Enum):
    """
    Flags indicating data quality issues discovered during verification.
    
    These are first-class citizens in CarbonChain to ensure transparency
    about limitations in the verification process.
    """
    MISSING_EVIDENCE = "missing_evidence"           # Expected evidence not provided
    LOW_RESOLUTION_IMAGERY = "low_resolution_imagery"   # Satellite data quality issues
    TEMPORAL_GAP = "temporal_gap"                   # Gaps in time-series data
    LOCATION_UNCERTAINTY = "location_uncertainty"   # Imprecise coordinates
    METHODOLOGY_UNCLEAR = "methodology_unclear"     # Calculation method not clear
    CONFLICTING_DATA = "conflicting_data"           # Evidence sources disagree
    OUTDATED_DATA = "outdated_data"                 # Data is stale
    UNVERIFIED_SOURCE = "unverified_source"         # Evidence from untrusted source
    AREA_MISMATCH = "area_mismatch"                 # Claimed area doesn't match evidence
    BASELINE_UNKNOWN = "baseline_unknown"           # Pre-action state unclear


class VerifiedCarbonImpact(BaseModel):
    """
    Independently verified carbon impact estimate.
    
    CRITICAL: Like claims, verified impact is expressed as a RANGE.
    This range may differ from the claimant's estimate.
    All values are in metric tons of CO2 equivalent (tCO2e).
    
    SCIENTIFIC CORRECTNESS: Negative values are scientifically valid and represent:
    - Net carbon loss (degradation, deforestation)
    - No positive carbon sequestration detected
    - Vegetation decline (negative NDVI delta)
    
    Negative values do NOT indicate an error - they indicate the satellite data
    shows no positive carbon impact or shows degradation.
    """
    min_tonnes_co2e: float = Field(
        ...,
        description="Lower bound of verified carbon impact in tonnes CO2e (can be negative for degradation)"
    )
    max_tonnes_co2e: float = Field(
        ...,
        description="Upper bound of verified carbon impact in tonnes CO2e (can be negative for degradation)"
    )
    # Point estimate within the range (optional, for display purposes)
    point_estimate_tonnes_co2e: Optional[float] = Field(
        default=None,
        description="Best single estimate within the range (optional, can be negative for degradation)"
    )
    confidence: ConfidenceLevel = Field(
        ...,
        description="Qualitative confidence level in this estimate"
    )
    # How the verified estimate was calculated
    methodology_used: str = Field(
        ...,
        description="Methodology used to calculate verified impact"
    )
    # Comparison to original claim
    deviation_from_claim_percent: Optional[float] = Field(
        default=None,
        description="Percentage difference from claimant's estimate (positive = higher, negative = lower)"
    )

    @model_validator(mode="after")
    def validate_carbon_range(self) -> "VerifiedCarbonImpact":
        """Ensure min_tonnes_co2e does not exceed max_tonnes_co2e."""
        if self.min_tonnes_co2e > self.max_tonnes_co2e:
            raise ValueError(
                f"min_tonnes_co2e ({self.min_tonnes_co2e}) cannot be greater than "
                f"max_tonnes_co2e ({self.max_tonnes_co2e})"
            )
        return self


class VerificationAssumption(BaseModel):
    """
    An explicit assumption made during verification.
    
    Transparency requirement: All assumptions must be documented
    so stakeholders understand the basis of verification decisions.
    """
    assumption: str = Field(
        ...,
        description="The assumption that was made"
    )
    rationale: str = Field(
        ...,
        description="Why this assumption was necessary or reasonable"
    )
    impact_on_result: str = Field(
        default="unknown",
        description="How this assumption affects the verification result (e.g., 'conservative', 'optimistic', 'neutral')"
    )


class EvidenceAssessment(BaseModel):
    """
    Assessment of a single piece of evidence.
    
    MVP assumption: Simple assessment model. Production would include
    detailed analysis from satellite imagery, ML models, etc.
    """
    evidence_type: EvidenceType = Field(
        ...,
        description="Type of evidence assessed (satellite_image, ground_photo, sensor_data, report, other)"
    )
    is_valid: bool = Field(
        ...,
        description="Whether this evidence is considered valid"
    )
    assessment_notes: str = Field(
        ...,
        description="Notes on the evidence assessment"
    )
    # Confidence in this specific evidence
    confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description="Confidence in this evidence assessment"
    )


class VerificationRequest(BaseModel):
    """
    Input model for requesting verification of a claim.
    
    MVP assumption: Verification is triggered manually.
    Production might have automatic triggers.
    """
    claim_id: UUID = Field(
        ...,
        description="ID of the claim to verify"
    )
    # Optional: specific aspects to focus on
    focus_areas: list[str] = Field(
        default_factory=list,
        description="Specific aspects to focus verification on (optional)"
    )
    # Optional: additional context for verifier
    additional_context: Optional[str] = Field(
        default=None,
        description="Additional context or notes for the verification process"
    )


class VerificationResult(BaseModel):
    """
    Complete verification result for a climate action claim.
    
    This is the core output of the verification process, containing:
    - Verification outcome and status
    - Independently calculated carbon impact
    - All assumptions and data quality flags
    - Evidence assessments
    """
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for this verification"
    )
    claim_id: UUID = Field(
        ...,
        description="ID of the claim that was verified"
    )
    status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        description="Current status of the verification process"
    )
    outcome: Optional[VerificationOutcome] = Field(
        default=None,
        description="Final outcome (populated when status is COMPLETED)"
    )
    
    # Verified carbon impact (the key output)
    verified_impact: Optional[VerifiedCarbonImpact] = Field(
        default=None,
        description="Independently verified carbon impact estimate"
    )
    
    # Transparency: all assumptions made during verification
    assumptions: list[VerificationAssumption] = Field(
        default_factory=list,
        description="All assumptions made during verification"
    )
    
    # Data quality flags (first-class citizens for transparency)
    data_quality_flags: list[DataQualityFlag] = Field(
        default_factory=list,
        description="Data quality issues discovered during verification"
    )
    
    # Evidence assessments
    evidence_assessments: list[EvidenceAssessment] = Field(
        default_factory=list,
        description="Assessment of each piece of evidence"
    )
    
    # Overall confidence in the verification
    overall_confidence: ConfidenceLevel = Field(
        default=ConfidenceLevel.MEDIUM,
        description=(
            "Overall confidence in the verification methodology and result. "
            "This represents confidence in the verification process, not AI consistency confidence."
        )
    )
    
    # Human-readable summary
    summary: Optional[str] = Field(
        default=None,
        description="Human-readable summary of verification findings"
    )
    
    # Detailed notes (internal use)
    verification_notes: Optional[str] = Field(
        default=None,
        description="Detailed notes from the verification process"
    )
    
    # Recommendations for the claim
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommendations for improving the claim or addressing issues"
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When verification was initiated"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When verification was completed"
    )
    
    # MVP assumption: Single verifier identifier (string, not full user model)
    verifier_id: Optional[str] = Field(
        default=None,
        description="Identifier of the verifier (human or system)"
    )

    class Config:
        """Pydantic configuration for the VerificationResult model."""
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "outcome": "approved",
                "verified_impact": {
                    "min_tonnes_co2e": 120.0,
                    "max_tonnes_co2e": 250.0,
                    "point_estimate_tonnes_co2e": 180.0,
                    "confidence": "medium",
                    "methodology_used": "IPCC Tier 2 with regional emission factors",
                    "deviation_from_claim_percent": -15.0
                },
                "assumptions": [
                    {
                        "assumption": "Mangrove species composition is typical for the region",
                        "rationale": "No species survey provided; using regional defaults",
                        "impact_on_result": "conservative"
                    }
                ],
                "data_quality_flags": ["temporal_gap", "unverified_source"],
                "overall_confidence": "medium",
                "summary": "Claim verified with moderate confidence. Carbon impact estimate adjusted downward by 15% due to conservative assumptions about mangrove density."
            }
        }


class VerificationSummary(BaseModel):
    """
    Lightweight summary of a verification for list views.
    
    MVP assumption: Used for displaying verification status without
    loading the full verification result.
    """
    id: UUID = Field(
        ...,
        description="Verification ID"
    )
    claim_id: UUID = Field(
        ...,
        description="Associated claim ID"
    )
    status: VerificationStatus = Field(
        ...,
        description="Current verification status"
    )
    outcome: Optional[VerificationOutcome] = Field(
        default=None,
        description="Verification outcome (if completed)"
    )
    overall_confidence: ConfidenceLevel = Field(
        ...,
        description="Overall confidence level"
    )
    # Quick stats
    data_quality_flag_count: int = Field(
        default=0,
        ge=0,
        description="Number of data quality flags raised"
    )
    created_at: datetime = Field(
        ...,
        description="When verification started"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When verification completed"
    )
