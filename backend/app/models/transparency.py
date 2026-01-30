"""
CarbonChain - Public Transparency Models

This module defines the data contracts for the public transparency view.
The transparency layer provides a read-only, canonical view of the claim lifecycle,
AI consistency verdicts, and credit health status.

DESIGN PRINCIPLES:
1. READ-ONLY: All data is derived from existing models, no mutations
2. AUDITABLE: Timeline events link back to immutable evidence records
3. CLEAR SEMANTICS: Explicit labels distinguish AI-derived vs human-verified data
4. TRUST-BUILDING: Public transparency enables community oversight
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """
    A single event in the claim lifecycle timeline.
    
    Events are derived from:
    - Claim creation
    - SYSTEM_AI evidence (MRV, consistency verdict, monitoring)
    - Authority review
    - Community review
    - Credit minting
    
    All events include timestamps and source attribution for auditability.
    """
    timestamp: datetime = Field(
        ...,
        description="When this event occurred"
    )
    event_type: str = Field(
        ...,
        description="Type of event (e.g., 'claim_submitted', 'ai_verified', 'authority_reviewed', 'credit_minted')"
    )
    title: str = Field(
        ...,
        description="Short title for this event"
    )
    description: str = Field(
        ...,
        description="Detailed description of what happened"
    )
    source: str = Field(
        ...,
        description="Source of this event: 'AI', 'Authority', 'Community', or 'System'"
    )

    class Config:
        """Pydantic configuration for the TimelineEvent model."""
        json_schema_extra = {
            "example": {
                "timestamp": "2025-01-15T10:30:00Z",
                "event_type": "ai_verified",
                "title": "AI MRV Analysis Complete",
                "description": "Satellite-based MRV analysis completed. Baseline NDVI: 0.45, Monitoring NDVI: 0.58, Delta: +0.13.",
                "source": "AI"
            }
        }


class AIVerdictSummary(BaseModel):
    """
    Summary of the AI consistency verdict for public transparency.
    
    This summary presents the AI's evaluation of how well the claim aligns
    with independent satellite-based MRV estimates.
    
    IMPORTANT: This verdict represents alignment confidence, NOT approval.
    Approval requires human governance (authority + community review).
    """
    verdict: str = Field(
        ...,
        description="Verdict category: 'strongly_supports', 'partially_supports', or 'contradicts'"
    )
    claimed_range: str = Field(
        ...,
        description="Formatted claim range (e.g., '150.0-300.0 tCO2e')"
    )
    ai_range: str = Field(
        ...,
        description="Formatted AI MRV estimate range (e.g., '135.0-270.0 tCO2e')"
    )
    deviation_percent: float = Field(
        ...,
        description="Percentage deviation between claim and AI estimate midpoints"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1) in the alignment evaluation"
    )
    explanation: str = Field(
        ...,
        description="Human-readable explanation of the verdict and reasoning"
    )

    class Config:
        """Pydantic configuration for the AIVerdictSummary model."""
        json_schema_extra = {
            "example": {
                "verdict": "strongly_supports",
                "claimed_range": "150.0-300.0 tCO2e",
                "ai_range": "135.0-270.0 tCO2e",
                "deviation_percent": -10.0,
                "confidence_score": 0.85,
                "explanation": "AI estimate range fully overlaps with claim range. Deviation of -10% indicates conservative AI estimate."
            }
        }


class CreditHealthStatus(BaseModel):
    """
    Computed credit health status for public transparency.
    
    Health status is DERIVED from credit lifecycle data, not manually set.
    Status indicates whether the underlying carbon sequestration remains valid
    based on post-mint monitoring.
    """
    status: str = Field(
        ...,
        description="Health status: 'HEALTHY', 'DEGRADED', or 'INVALIDATED'"
    )
    reason: str = Field(
        ...,
        description="Explanation of why this status was assigned"
    )

    class Config:
        """Pydantic configuration for the CreditHealthStatus model."""
        json_schema_extra = {
            "example": {
                "status": "HEALTHY",
                "reason": "Credit is active with no degradation detected. Monitoring is MVP placeholder - full monitoring logic will be implemented in production."
            }
        }


class TransparencyReport(BaseModel):
    """
    Complete public transparency report for a claim.
    
    This report provides a canonical, read-only view of:
    - Complete lifecycle timeline
    - AI consistency verdict summary
    - Credit health status (if credit exists)
    
    All data is derived from existing immutable records (evidence, reviews, credits).
    This view enables public auditability and trust verification.
    """
    claim_id: UUID = Field(
        ...,
        description="ID of the claim this report covers"
    )
    timeline: list[TimelineEvent] = Field(
        default_factory=list,
        description="Chronological timeline of all claim lifecycle events"
    )
    ai_verdict: Optional[AIVerdictSummary] = Field(
        default=None,
        description="AI consistency verdict summary (if AI analysis was performed)"
    )
    credit_health: Optional[CreditHealthStatus] = Field(
        default=None,
        description="Credit health status (if credit was minted)"
    )

    class Config:
        """Pydantic configuration for the TransparencyReport model."""
        json_schema_extra = {
            "example": {
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "timeline": [
                    {
                        "timestamp": "2025-01-15T08:00:00Z",
                        "event_type": "claim_submitted",
                        "title": "Claim Submitted",
                        "description": "Claim submitted by Green Delta Foundation",
                        "source": "System"
                    }
                ],
                "ai_verdict": {
                    "verdict": "strongly_supports",
                    "claimed_range": "150.0-300.0 tCO2e",
                    "ai_range": "135.0-270.0 tCO2e",
                    "deviation_percent": -10.0,
                    "confidence_score": 0.85,
                    "explanation": "AI estimate range fully overlaps with claim range."
                },
                "credit_health": {
                    "status": "HEALTHY",
                    "reason": "Credit is active with no degradation detected."
                }
            }
        }
"""
CarbonChain - Public Transparency Models

This module defines the data contracts for the public transparency view.
The transparency layer provides a read-only, canonical view of the claim lifecycle,
AI consistency verdicts, and credit health status.

DESIGN PRINCIPLES:
1. READ-ONLY: All data is derived from existing models, no mutations
2. AUDITABLE: Timeline events link back to immutable evidence records
3. CLEAR SEMANTICS: Explicit labels distinguish AI-derived vs human-verified data
4. TRUST-BUILDING: Public transparency enables community oversight
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TimelineEvent(BaseModel):
    """
    A single event in the claim lifecycle timeline.
    
    Events are derived from:
    - Claim creation
    - SYSTEM_AI evidence (MRV, consistency verdict, monitoring)
    - Authority review
    - Community review
    - Credit minting
    
    All events include timestamps and source attribution for auditability.
    """
    timestamp: datetime = Field(
        ...,
        description="When this event occurred"
    )
    event_type: str = Field(
        ...,
        description="Type of event (e.g., 'claim_submitted', 'ai_verified', 'authority_reviewed', 'credit_minted')"
    )
    title: str = Field(
        ...,
        description="Short title for this event"
    )
    description: str = Field(
        ...,
        description="Detailed description of what happened"
    )
    source: str = Field(
        ...,
        description="Source of this event: 'AI', 'Authority', 'Community', or 'System'"
    )

    class Config:
        """Pydantic configuration for the TimelineEvent model."""
        json_schema_extra = {
            "example": {
                "timestamp": "2025-01-15T10:30:00Z",
                "event_type": "ai_verified",
                "title": "AI MRV Analysis Complete",
                "description": "Satellite-based MRV analysis completed. Baseline NDVI: 0.45, Monitoring NDVI: 0.58, Delta: +0.13.",
                "source": "AI"
            }
        }


class AIVerdictSummary(BaseModel):
    """
    Summary of the AI consistency verdict for public transparency.
    
    This summary presents the AI's evaluation of how well the claim aligns
    with independent satellite-based MRV estimates.
    
    IMPORTANT: This verdict represents alignment confidence, NOT approval.
    Approval requires human governance (authority + community review).
    """
    verdict: str = Field(
        ...,
        description="Verdict category: 'strongly_supports', 'partially_supports', or 'contradicts'"
    )
    claimed_range: str = Field(
        ...,
        description="Formatted claim range (e.g., '150.0-300.0 tCO2e')"
    )
    ai_range: str = Field(
        ...,
        description="Formatted AI MRV estimate range (e.g., '135.0-270.0 tCO2e')"
    )
    deviation_percent: float = Field(
        ...,
        description="Percentage deviation between claim and AI estimate midpoints"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1) in the alignment evaluation"
    )
    explanation: str = Field(
        ...,
        description="Human-readable explanation of the verdict and reasoning"
    )

    class Config:
        """Pydantic configuration for the AIVerdictSummary model."""
        json_schema_extra = {
            "example": {
                "verdict": "strongly_supports",
                "claimed_range": "150.0-300.0 tCO2e",
                "ai_range": "135.0-270.0 tCO2e",
                "deviation_percent": -10.0,
                "confidence_score": 0.85,
                "explanation": "AI estimate range fully overlaps with claim range. Deviation of -10% indicates conservative AI estimate."
            }
        }


class CreditHealthStatus(BaseModel):
    """
    Computed credit health status for public transparency.
    
    Health status is DERIVED from credit lifecycle data, not manually set.
    Status indicates whether the underlying carbon sequestration remains valid
    based on post-mint monitoring.
    """
    status: str = Field(
        ...,
        description="Health status: 'HEALTHY', 'DEGRADED', or 'INVALIDATED'"
    )
    reason: str = Field(
        ...,
        description="Explanation of why this status was assigned"
    )

    class Config:
        """Pydantic configuration for the CreditHealthStatus model."""
        json_schema_extra = {
            "example": {
                "status": "HEALTHY",
                "reason": "Credit is active with no degradation detected. Monitoring is MVP placeholder - full monitoring logic will be implemented in production."
            }
        }


class TransparencyReport(BaseModel):
    """
    Complete public transparency report for a claim.
    
    This report provides a canonical, read-only view of:
    - Complete lifecycle timeline
    - AI consistency verdict summary
    - Credit health status (if credit exists)
    
    All data is derived from existing immutable records (evidence, reviews, credits).
    This view enables public auditability and trust verification.
    """
    claim_id: UUID = Field(
        ...,
        description="ID of the claim this report covers"
    )
    timeline: list[TimelineEvent] = Field(
        default_factory=list,
        description="Chronological timeline of all claim lifecycle events"
    )
    ai_verdict: Optional[AIVerdictSummary] = Field(
        default=None,
        description="AI consistency verdict summary (if AI analysis was performed)"
    )
    credit_health: Optional[CreditHealthStatus] = Field(
        default=None,
        description="Credit health status (if credit was minted)"
    )

    class Config:
        """Pydantic configuration for the TransparencyReport model."""
        json_schema_extra = {
            "example": {
                "claim_id": "550e8400-e29b-41d4-a716-446655440000",
                "timeline": [
                    {
                        "timestamp": "2025-01-15T08:00:00Z",
                        "event_type": "claim_submitted",
                        "title": "Claim Submitted",
                        "description": "Claim submitted by Green Delta Foundation",
                        "source": "System"
                    }
                ],
                "ai_verdict": {
                    "verdict": "strongly_supports",
                    "claimed_range": "150.0-300.0 tCO2e",
                    "ai_range": "135.0-270.0 tCO2e",
                    "deviation_percent": -10.0,
                    "confidence_score": 0.85,
                    "explanation": "AI estimate range fully overlaps with claim range."
                },
                "credit_health": {
                    "status": "HEALTHY",
                    "reason": "Credit is active with no degradation detected."
                }
            }
        }
