"""
CarbonChain MVP - Transparency Service

Service layer for building public transparency reports.
This service provides READ-ONLY, derived views of claim lifecycle data.

DESIGN PRINCIPLES:
1. PURE FUNCTIONS: All functions are side-effect free, no mutations
2. DERIVED DATA: All output is computed from existing models
3. AUDITABLE: Timeline events link to immutable evidence records
4. TRUST-BUILDING: Clear labels distinguish AI-derived vs human-verified data

IMPORTANT:
- This layer does NOT modify existing workflows
- All data is DERIVED from in-memory stores
- No persistence, no side effects
"""

from typing import Optional
from uuid import UUID

from backend.app.models.claim import Claim
from backend.app.models.evidence import Evidence, EvidenceType
from backend.app.models.monitoring import MonitoringRun
from backend.app.models.review import CreditStatus, MintedCredit
from backend.app.models.transparency import (
    AIVerdictSummary,
    CreditHealthStatus,
    TimelineEvent,
    TransparencyReport,
)
from backend.app.services import (
    ai_consistency_service,
    claim_service,
    credit_monitoring_service,
    evidence_service,
    review_service,
)


def build_timeline(claim_id: UUID) -> list[TimelineEvent]:
    """
    Build chronological timeline of claim lifecycle events.
    
    Collects events from:
    - Claim creation (created_at)
    - SYSTEM_AI evidence (MRV, consistency verdict, monitoring)
    - Authority review
    - Community review
    - Minted credit
    
    All events are sorted by timestamp ascending.
    
    Args:
        claim_id: The UUID of the claim.
    
    Returns:
        List of TimelineEvent objects in chronological order.
    """
    timeline = []
    
    # Get claim
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        return timeline
    
    # Event 1: Claim submitted
    timeline.append(TimelineEvent(
        timestamp=claim.created_at,
        event_type="claim_submitted",
        title="Claim Submitted",
        description=f"Claim '{claim.title}' submitted by {claim.submitter_name}",
        source="System",
    ))
    
    # Get all evidence (includes SYSTEM_AI evidence)
    evidence_list = evidence_service.get_evidence_for_claim(claim_id)
    for evidence in evidence_list:
        if evidence.type == EvidenceType.SYSTEM_AI:
            # Determine event type from title
            if "MRV" in evidence.title or "Satellite-based" in evidence.title:
                timeline.append(TimelineEvent(
                    timestamp=evidence.created_at,
                    event_type="ai_mrv_analysis",
                    title="AI MRV Analysis Complete",
                    description=f"{evidence.title}. {evidence.description[:200]}...",
                    source="AI",
                ))
            elif "Consistency Verdict" in evidence.title:
                timeline.append(TimelineEvent(
                    timestamp=evidence.created_at,
                    event_type="ai_consistency_verdict",
                    title="AI Claim Consistency Verdict",
                    description=f"{evidence.description[:200]}...",
                    source="AI",
                ))
            elif "Monitoring" in evidence.title or "monitoring" in evidence.description:
                timeline.append(TimelineEvent(
                    timestamp=evidence.created_at,
                    event_type="credit_monitoring",
                    title="Credit Monitoring Run",
                    description=f"{evidence.description[:200]}...",
                    source="AI",
                ))
        else:
            # User-uploaded or other evidence
            timeline.append(TimelineEvent(
                timestamp=evidence.created_at,
                event_type="evidence_uploaded",
                title=f"Evidence Uploaded: {evidence.title}",
                description=evidence.description[:200] + "..." if len(evidence.description) > 200 else evidence.description,
                source="System",
            ))
    
    # Get authority review
    authority_reviews = review_service.get_reviews_by_claim(
        claim_id, role=review_service.ReviewRole.AUTHORITY
    )
    if authority_reviews:
        review = authority_reviews[0]
        timeline.append(TimelineEvent(
            timestamp=review.created_at,
            event_type="authority_reviewed",
            title="Authority Review Complete",
            description=f"Authority review by {review.reviewer_id}: {review.decision.value.upper()}",
            source="Authority",
        ))
    
    # Get community review
    community_reviews = review_service.get_reviews_by_claim(
        claim_id, role=review_service.ReviewRole.COMMUNITY
    )
    if community_reviews:
        review = community_reviews[0]
        timeline.append(TimelineEvent(
            timestamp=review.created_at,
            event_type="community_reviewed",
            title="Community Review Complete",
            description=f"Community review by {review.reviewer_id}: {review.decision.value.upper()}",
            source="Community",
        ))
    
    # Get minted credit
    minted_credit = review_service.get_minted_credit_by_claim(claim_id)
    if minted_credit:
        timeline.append(TimelineEvent(
            timestamp=minted_credit.minted_at,
            event_type="credit_minted",
            title="Carbon Credit Minted",
            description=f"Carbon credit minted: {minted_credit.amount_tonnes_co2e} tonnes CO₂e (Token ID: {minted_credit.token_id})",
            source="System",
        ))
    
    # Sort by timestamp ascending
    timeline.sort(key=lambda e: e.timestamp)
    
    return timeline


def build_ai_verdict_summary(claim_id: UUID) -> Optional[AIVerdictSummary]:
    """
    Build AI verdict summary from AIConsistencyResult.
    
    Reads the AI consistency result and formats it for public transparency.
    Returns None if no AI verdict exists.
    
    IMPORTANT: This verdict represents alignment confidence, NOT approval.
    Approval requires human governance (authority + community review).
    
    Args:
        claim_id: The UUID of the claim.
    
    Returns:
        AIVerdictSummary if AI verdict exists, None otherwise.
    """
    consistency_result = ai_consistency_service.get_consistency_result_by_claim_id(claim_id)
    if consistency_result is None:
        return None
    
    # Format ranges
    claimed_range = f"{consistency_result.claimed_min_co2e:.1f}-{consistency_result.claimed_max_co2e:.1f} tCO2e"
    ai_range = f"{consistency_result.estimated_min_co2e:.1f}-{consistency_result.estimated_max_co2e:.1f} tCO2e"
    
    return AIVerdictSummary(
        verdict=consistency_result.verdict.value,
        claimed_range=claimed_range,
        ai_range=ai_range,
        deviation_percent=consistency_result.deviation_percent,
        confidence_score=consistency_result.confidence_score,
        explanation=consistency_result.explanation,
    )


def compute_credit_health(claim_id: UUID) -> Optional[CreditHealthStatus]:
    """
    Compute credit health status from credit lifecycle data.
    
    Health status is DERIVED from credit data, not manually set.
    
    Rules:
    - No minted credit → return None
    - Credit fully burned → INVALIDATED
    - Credit partially burned → DEGRADED
    - Credit at risk → DEGRADED
    - Credit active → HEALTHY (with MVP monitoring note)
    
    Args:
        claim_id: The UUID of the claim.
    
    Returns:
        CreditHealthStatus if credit exists, None otherwise.
    """
    minted_credit = review_service.get_minted_credit_by_claim(claim_id)
    if minted_credit is None:
        return None
    
    # Check credit status
    if minted_credit.status == CreditStatus.FULLY_BURNED:
        return CreditHealthStatus(
            status="INVALIDATED",
            reason="Credit has been fully burned due to severe degradation detected in post-mint monitoring.",
        )
    
    elif minted_credit.status in (CreditStatus.PARTIALLY_BURNED, CreditStatus.AT_RISK):
        remaining_pct = (minted_credit.remaining_tonnes_co2e / minted_credit.amount_tonnes_co2e) * 100 if minted_credit.amount_tonnes_co2e > 0 else 0
        return CreditHealthStatus(
            status="DEGRADED",
            reason=f"Credit has been partially burned or is at risk. {remaining_pct:.1f}% of original amount remains ({minted_credit.remaining_tonnes_co2e:.2f}/{minted_credit.amount_tonnes_co2e:.2f} tonnes CO₂e).",
        )
    
    else:
        # ACTIVE status
        return CreditHealthStatus(
            status="HEALTHY",
            reason="Credit is active with no degradation detected. Monitoring is MVP placeholder - full monitoring logic will be implemented in production.",
        )


def build_transparency_report(claim_id: UUID) -> TransparencyReport:
    """
    Build complete transparency report for a claim.
    
    Assembles all transparency data:
    - Complete lifecycle timeline
    - AI consistency verdict summary (if available)
    - Credit health status (if credit exists)
    
    All data is derived from existing immutable records.
    This is a pure function with no side effects.
    
    Args:
        claim_id: The UUID of the claim.
    
    Returns:
        TransparencyReport with all available transparency data.
    
    Raises:
        ValueError: If claim not found.
    """
    # Validate claim exists
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        raise ValueError(f"Claim {claim_id} not found")
    
    # Build timeline
    timeline = build_timeline(claim_id)
    
    # Build AI verdict summary
    ai_verdict = build_ai_verdict_summary(claim_id)
    
    # Compute credit health
    credit_health = compute_credit_health(claim_id)
    
    return TransparencyReport(
        claim_id=claim_id,
        timeline=timeline,
        ai_verdict=ai_verdict,
        credit_health=credit_health,
    )
