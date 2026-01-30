"""
CarbonChain MVP - AI Claim Consistency Service

Service layer for evaluating consistency between AI-derived MRV results
and claimant-declared carbon estimates.

DESIGN PRINCIPLES:
1. DETERMINISTIC: All logic is rule-based and reproducible. No ML models.
2. EXPLAINABLE: Every verdict includes clear reasoning that reviewers can understand.
3. CONSERVATIVE: The system errs on the side of caution to prevent false positives.
4. TRANSPARENT: All assumptions and heuristics are documented.

CONSISTENCY EVALUATION RULES:
- Full overlap (AI range fully contains or is fully contained within claim range):
  → STRONGLY_SUPPORTS
- Partial overlap (ranges intersect but neither fully contains the other):
  → PARTIALLY_SUPPORTS
- No overlap (ranges do not intersect):
  → CONTRADICTS

DEVIATION CALCULATION:
- Deviation % = ((AI_midpoint - Claim_midpoint) / Claim_midpoint) * 100
- Positive deviation = AI estimate is higher than claim
- Negative deviation = AI estimate is lower than claim

CONFIDENCE SCORE HEURISTICS:
The confidence score (0-1) is derived from three factors:
1. NDVI magnitude (0-0.4 weight): Higher NDVI delta → higher confidence
2. Area size (0-0.3 weight): Larger areas → higher confidence (more data points)
3. Overlap ratio (0-0.3 weight): Better overlap → higher confidence

WHY THIS IS CONSERVATIVE:
- Strict range boundaries (no fuzzy matching)
- Lower confidence scores for edge cases
- CONTRADICTS verdict when ranges don't overlap (even if close)
- Confidence heuristics use conservative thresholds

WHY THIS BUILDS TRUST:
- Transparent, explainable logic that reviewers can verify
- Conservative approach prevents false approvals
- Public access to verdicts enables community oversight
- Deterministic results ensure reproducibility
"""

from typing import Optional
from uuid import UUID

from backend.app.models.ai_verdict import AIConsistencyResult, AIVerdict
from backend.app.models.claim import Claim

# -----------------------------------------------------------------------------
# In-memory storage (MVP only - not for production)
# -----------------------------------------------------------------------------
consistency_results_db: dict[UUID, AIConsistencyResult] = {}


def evaluate_claim_consistency(
    claim: Claim,
    ai_estimate_min: float,
    ai_estimate_max: float,
    ndvi_delta: Optional[float] = None,
    area_hectares: Optional[float] = None,
) -> AIConsistencyResult:
    """
    Evaluate consistency between a claim and AI-derived MRV estimate.
    
    This function implements deterministic, rule-based logic to compare:
    - Claimant-declared carbon impact range (claim.carbon_impact_estimate)
    - AI-derived MRV estimate range (ai_estimate_min, ai_estimate_max)
    
    The evaluation produces a verdict, deviation percentage, confidence score,
    and explanation that can be used by authority and community reviewers.
    
    Args:
        claim: The Claim object with claimant-declared carbon impact.
        ai_estimate_min: Lower bound of AI-derived MRV estimate (tonnes CO2e).
        ai_estimate_max: Upper bound of AI-derived MRV estimate (tonnes CO2e).
        ndvi_delta: Optional NDVI delta value for confidence calculation.
        area_hectares: Optional area in hectares for confidence calculation.
    
    Returns:
        AIConsistencyResult with verdict, deviation, confidence, and explanation.
    
    ASSUMPTIONS:
    - All CO2e values are in tonnes
    - Ranges are valid (min <= max)
    - Overlap detection uses strict boundaries (no fuzzy matching)
    - Confidence calculation uses conservative heuristics
    
    CONSERVATIVE LOGIC:
    - Full overlap requires one range to be fully contained within the other
    - Partial overlap requires any intersection
    - No overlap triggers CONTRADICTS verdict (even if ranges are close)
    - Confidence scores are conservative (lower bound estimates)
    """
    # Extract claim range
    claimed_min = claim.carbon_impact_estimate.min_tonnes_co2e
    claimed_max = claim.carbon_impact_estimate.max_tonnes_co2e
    
    # Validate ranges
    if claimed_min > claimed_max:
        raise ValueError(f"Invalid claim range: min ({claimed_min}) > max ({claimed_max})")
    if ai_estimate_min > ai_estimate_max:
        raise ValueError(f"Invalid AI estimate range: min ({ai_estimate_min}) > max ({ai_estimate_max})")
    
    # Calculate midpoints for deviation calculation
    claim_midpoint = (claimed_min + claimed_max) / 2.0
    ai_midpoint = (ai_estimate_min + ai_estimate_max) / 2.0
    
    # Calculate deviation percentage
    if claim_midpoint > 0:
        deviation_percent = ((ai_midpoint - claim_midpoint) / claim_midpoint) * 100.0
    else:
        deviation_percent = 0.0  # Edge case: zero claim midpoint
    
    # Determine overlap type and verdict
    verdict, overlap_ratio = _determine_verdict(
        claimed_min, claimed_max, ai_estimate_min, ai_estimate_max
    )
    
    # Calculate confidence score
    confidence_score = _calculate_confidence_score(
        ndvi_delta=ndvi_delta,
        area_hectares=area_hectares,
        overlap_ratio=overlap_ratio,
    )
    
    # Generate explanation
    explanation = _generate_explanation(
        claimed_min, claimed_max, ai_estimate_min, ai_estimate_max,
        deviation_percent, verdict, confidence_score, overlap_ratio
    )
    
    result = AIConsistencyResult(
        claim_id=claim.id,
        claimed_min_co2e=claimed_min,
        claimed_max_co2e=claimed_max,
        estimated_min_co2e=ai_estimate_min,
        estimated_max_co2e=ai_estimate_max,
        deviation_percent=deviation_percent,
        verdict=verdict,
        confidence_score=confidence_score,
        explanation=explanation,
    )
    
    # Store result for later retrieval
    consistency_results_db[claim.id] = result
    
    return result


def _determine_verdict(
    claimed_min: float,
    claimed_max: float,
    ai_min: float,
    ai_max: float,
) -> tuple[AIVerdict, float]:
    """
    Determine verdict based on range overlap.
    
    Returns:
        Tuple of (verdict, overlap_ratio)
        overlap_ratio: 0.0 (no overlap) to 1.0 (full overlap)
    """
    # Check for full overlap (one range fully contains the other)
    ai_fully_contains_claim = (ai_min <= claimed_min) and (ai_max >= claimed_max)
    claim_fully_contains_ai = (claimed_min <= ai_min) and (claimed_max >= ai_max)
    
    if ai_fully_contains_claim or claim_fully_contains_ai:
        # Calculate overlap ratio (intersection / union)
        intersection_min = max(claimed_min, ai_min)
        intersection_max = min(claimed_max, ai_max)
        intersection_size = max(0, intersection_max - intersection_min)
        
        union_min = min(claimed_min, ai_min)
        union_max = max(claimed_max, ai_max)
        union_size = union_max - union_min
        
        overlap_ratio = intersection_size / union_size if union_size > 0 else 0.0
        return (AIVerdict.STRONGLY_SUPPORTS, overlap_ratio)
    
    # Check for partial overlap (ranges intersect but neither fully contains the other)
    has_overlap = not (ai_max < claimed_min or ai_min > claimed_max)
    
    if has_overlap:
        # Calculate overlap ratio
        intersection_min = max(claimed_min, ai_min)
        intersection_max = min(claimed_max, ai_max)
        intersection_size = max(0, intersection_max - intersection_min)
        
        union_min = min(claimed_min, ai_min)
        union_max = max(claimed_max, ai_max)
        union_size = union_max - union_min
        
        overlap_ratio = intersection_size / union_size if union_size > 0 else 0.0
        return (AIVerdict.PARTIALLY_SUPPORTS, overlap_ratio)
    
    # No overlap
    return (AIVerdict.CONTRADICTS, 0.0)


def _calculate_confidence_score(
    ndvi_delta: Optional[float],
    area_hectares: Optional[float],
    overlap_ratio: float,
) -> float:
    """
    Calculate confidence score (0-1) using conservative heuristics.
    
    CONFIDENCE FACTORS:
    1. NDVI magnitude (0-0.4 weight):
       - NDVI delta > 0.15: high confidence (0.4)
       - NDVI delta 0.10-0.15: medium confidence (0.3)
       - NDVI delta 0.05-0.10: low confidence (0.2)
       - NDVI delta < 0.05: very low confidence (0.1)
       - NDVI delta None: neutral (0.2)
    
    2. Area size (0-0.3 weight):
       - Area > 100 ha: high confidence (0.3)
       - Area 50-100 ha: medium confidence (0.2)
       - Area 10-50 ha: low confidence (0.1)
       - Area < 10 ha: very low confidence (0.05)
       - Area None: neutral (0.15)
    
    3. Overlap ratio (0-0.3 weight):
       - Overlap > 0.8: high confidence (0.3)
       - Overlap 0.5-0.8: medium confidence (0.2)
       - Overlap 0.2-0.5: low confidence (0.1)
       - Overlap < 0.2: very low confidence (0.05)
    
    CONSERVATIVE APPROACH:
    - Uses lower bounds for each factor
    - Requires strong signals for high confidence
    - Defaults to medium-low confidence when data is missing
    
    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Factor 1: NDVI magnitude (0-0.4)
    if ndvi_delta is not None:
        if ndvi_delta > 0.15:
            ndvi_score = 0.4
        elif ndvi_delta >= 0.10:
            ndvi_score = 0.3
        elif ndvi_delta >= 0.05:
            ndvi_score = 0.2
        else:
            ndvi_score = 0.1
    else:
        ndvi_score = 0.2  # Neutral when NDVI not available
    
    # Factor 2: Area size (0-0.3)
    if area_hectares is not None:
        if area_hectares > 100.0:
            area_score = 0.3
        elif area_hectares >= 50.0:
            area_score = 0.2
        elif area_hectares >= 10.0:
            area_score = 0.1
        else:
            area_score = 0.05
    else:
        area_score = 0.15  # Neutral when area not available
    
    # Factor 3: Overlap ratio (0-0.3)
    if overlap_ratio > 0.8:
        overlap_score = 0.3
    elif overlap_ratio >= 0.5:
        overlap_score = 0.2
    elif overlap_ratio >= 0.2:
        overlap_score = 0.1
    else:
        overlap_score = 0.05
    
    # Sum all factors (total max = 1.0)
    total_confidence = ndvi_score + area_score + overlap_score
    
    # Ensure result is in [0, 1] range
    return max(0.0, min(1.0, total_confidence))


def _generate_explanation(
    claimed_min: float,
    claimed_max: float,
    ai_min: float,
    ai_max: float,
    deviation_percent: float,
    verdict: AIVerdict,
    confidence_score: float,
    overlap_ratio: float,
) -> str:
    """
    Generate human-readable explanation of the consistency evaluation.
    
    The explanation includes:
    - Verdict category
    - Range comparison
    - Deviation percentage
    - Confidence score
    - Reasoning for the verdict
    
    This explanation is designed for authority and community reviewers
    to understand the AI's reasoning without technical expertise.
    """
    # Format ranges
    claim_range_str = f"{claimed_min:.1f}-{claimed_max:.1f}"
    ai_range_str = f"{ai_min:.1f}-{ai_max:.1f}"
    
    # Format deviation
    if deviation_percent > 0:
        deviation_str = f"{deviation_percent:.1f}% higher"
    elif deviation_percent < 0:
        deviation_str = f"{abs(deviation_percent):.1f}% lower"
    else:
        deviation_str = "0% (identical midpoints)"
    
    # Verdict-specific explanations
    if verdict == AIVerdict.STRONGLY_SUPPORTS:
        verdict_explanation = (
            f"AI estimate range ({ai_range_str} tCO2e) fully overlaps with "
            f"claim range ({claim_range_str} tCO2e). "
            f"The claimant's estimate is well-supported by independent satellite-based verification. "
            f"Deviation of {deviation_str} indicates "
        )
        if deviation_percent < -5:
            verdict_explanation += "a conservative AI estimate (AI is lower than claim)."
        elif deviation_percent > 5:
            verdict_explanation += "an optimistic claim (claim is lower than AI)."
        else:
            verdict_explanation += "close alignment between claim and AI estimate."
    
    elif verdict == AIVerdict.PARTIALLY_SUPPORTS:
        verdict_explanation = (
            f"AI estimate range ({ai_range_str} tCO2e) partially overlaps with "
            f"claim range ({claim_range_str} tCO2e). "
            f"There is some agreement but also discrepancy. "
            f"Deviation of {deviation_str} suggests "
        )
        if abs(deviation_percent) > 20:
            verdict_explanation += "significant methodological differences that may require reconciliation."
        else:
            verdict_explanation += "moderate differences that may be due to estimation methodology."
    
    else:  # CONTRADICTS
        verdict_explanation = (
            f"AI estimate range ({ai_range_str} tCO2e) does not overlap with "
            f"claim range ({claim_range_str} tCO2e). "
            f"Deviation of {deviation_str} indicates a significant discrepancy. "
            f"This requires investigation to determine whether: "
            f"(1) the claim is inaccurate, (2) there are methodological differences, "
            f"or (3) there are data quality issues affecting the AI estimate."
        )
    
    # Add confidence information
    if confidence_score >= 0.7:
        confidence_str = "High"
    elif confidence_score >= 0.4:
        confidence_str = "Medium"
    else:
        confidence_str = "Low"
    
    explanation = (
        f"{verdict_explanation} "
        f"Confidence score: {confidence_score:.2f} ({confidence_str}). "
        f"Overlap ratio: {overlap_ratio:.2f}. "
        f"This evaluation uses deterministic, rule-based logic for transparency and auditability."
    )
    
    return explanation


def get_consistency_result_by_claim_id(claim_id: UUID) -> Optional[AIConsistencyResult]:
    """
    Retrieve an AI consistency result by claim ID.
    
    Args:
        claim_id: The UUID of the claim.
    
    Returns:
        The AIConsistencyResult object if found, None otherwise.
    """
    return consistency_results_db.get(claim_id)
