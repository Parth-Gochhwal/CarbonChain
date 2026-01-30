"""
CarbonChain MVP - Review Service

Service layer for human governance reviews.
Implements role-based workflow enforcement for the trust layer.

GOVERNANCE FLOW:
1. Claim must be AI_ANALYZED (or legacy AI_VERIFIED/VERIFIED) before authority can review
2. Claim must be AUTHORITY_REVIEWED before community can review
3. Both authority AND community must APPROVE for claim to be APPROVED
4. Rejection at any governance stage moves claim to REJECTED

This service ensures transparent, auditable decision flow.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from backend.app.models.claim import ClaimStatus
from backend.app.models.review import (
    CreditStatus,
    MintedCredit,
    ReviewDecision,
    ReviewRecord,
    ReviewRole,
    ReviewSubmission,
)
from backend.app.services import claim_service, evidence_service
from backend.app.storage import atomic_write_json, read_json, uuid_to_str, str_to_uuid

# -----------------------------------------------------------------------------
# JSON file storage
# -----------------------------------------------------------------------------
STORAGE_DIR = Path("backend/app/storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
REVIEWS_FILE = STORAGE_DIR / "reviews.json"
CREDITS_FILE = STORAGE_DIR / "credits.json"

reviews_db: dict[UUID, ReviewRecord] = {}
minted_credits_db: dict[UUID, MintedCredit] = {}


def _load_reviews() -> None:
    """Load reviews from disk on startup."""
    if not REVIEWS_FILE.exists():
        print(f"[REVIEW_SERVICE] {REVIEWS_FILE} does not exist. Starting with empty database.")
        return
    
    try:
        loaded_data = read_json(REVIEWS_FILE, default={})
        
        reviews_db.clear()
        for review_id_str, review_data in loaded_data.items():
            try:
                review_id = UUID(review_id_str)
                review_data = str_to_uuid(review_data, ['id', 'claim_id'])
                review = ReviewRecord(**review_data)
                reviews_db[review_id] = review
            except Exception as e:
                print(f"[REVIEW_SERVICE WARNING] Failed to load review {review_id_str}: {e}")
        
        print(f"[REVIEW_SERVICE] Loaded {len(reviews_db)} reviews from {REVIEWS_FILE}")
    except Exception as e:
        print(f"[REVIEW_SERVICE ERROR] Failed to load reviews: {e}")


def _save_reviews() -> None:
    """Save reviews to disk."""
    try:
        serializable_data = {}
        for review_id, review in reviews_db.items():
            review_dict = review.model_dump()
            serializable_data[str(review_id)] = uuid_to_str(review_dict)
        
        atomic_write_json(REVIEWS_FILE, serializable_data)
    except Exception as e:
        print(f"[REVIEW_SERVICE ERROR] Failed to save reviews: {e}")


def _load_credits() -> None:
    """Load minted credits from disk on startup."""
    if not CREDITS_FILE.exists():
        print(f"[REVIEW_SERVICE] {CREDITS_FILE} does not exist. Starting with empty database.")
        return
    
    try:
        loaded_data = read_json(CREDITS_FILE, default={})
        
        minted_credits_db.clear()
        for credit_id_str, credit_data in loaded_data.items():
            try:
                credit_id = UUID(credit_id_str)
                credit_data = str_to_uuid(credit_data, ['token_id', 'claim_id'])
                credit = MintedCredit(**credit_data)
                minted_credits_db[credit_id] = credit
            except Exception as e:
                print(f"[REVIEW_SERVICE WARNING] Failed to load credit {credit_id_str}: {e}")
        
        print(f"[REVIEW_SERVICE] Loaded {len(minted_credits_db)} credits from {CREDITS_FILE}")
    except Exception as e:
        print(f"[REVIEW_SERVICE ERROR] Failed to load credits: {e}")


def _save_credits() -> None:
    """Save minted credits to disk."""
    try:
        serializable_data = {}
        for credit_id, credit in minted_credits_db.items():
            credit_dict = credit.model_dump()
            serializable_data[str(credit_id)] = uuid_to_str(credit_dict)
        
        atomic_write_json(CREDITS_FILE, serializable_data)
    except Exception as e:
        print(f"[REVIEW_SERVICE ERROR] Failed to save credits: {e}")


# Load on import
_load_reviews()
_load_credits()


class ReviewError(Exception):
    """Custom exception for review workflow errors."""
    pass


def submit_authority_review(submission: ReviewSubmission) -> ReviewRecord:
    """
    Submit an authority (government/regulator) review for a claim.
    
    PRECONDITION: Claim must be in AI_ANALYZED status (or legacy AI_VERIFIED/VERIFIED).
    
    On APPROVE: Claim moves to AUTHORITY_REVIEWED
    On REJECT: Claim moves to REJECTED
    
    Args:
        submission: The review submission data.
        
    Returns:
        The created ReviewRecord.
        
    Raises:
        ReviewError: If claim not found or not in correct status.
    """
    claim = claim_service.get_claim_by_id(submission.claim_id)
    if claim is None:
        raise ReviewError(f"Claim {submission.claim_id} not found")
    
    # Enforce workflow: authority review requires AI_ANALYZED status
    # Also accept legacy statuses for backwards compatibility
    if claim.status not in (ClaimStatus.AI_ANALYZED, ClaimStatus.AI_VERIFIED, ClaimStatus.VERIFIED):
        raise ReviewError(
            f"Authority review requires claim status AI_ANALYZED (or legacy AI_VERIFIED/VERIFIED). "
            f"Current status: {claim.status.value}"
        )
    
    # Check if authority review already exists
    existing = get_reviews_by_claim(submission.claim_id, role=ReviewRole.AUTHORITY)
    if existing:
        raise ReviewError(
            f"Authority review already exists for claim {submission.claim_id}"
        )
    
    # Create review record
    review = ReviewRecord(
        **submission.model_dump(),
        role=ReviewRole.AUTHORITY,
    )
    reviews_db[review.id] = review
    _save_reviews()
    
    # Update claim status based on decision
    if submission.decision == ReviewDecision.APPROVE:
        claim.status = ClaimStatus.AUTHORITY_REVIEWED
    else:
        claim.status = ClaimStatus.REJECTED
    
    claim.updated_at = datetime.utcnow()
    # Persist claim update
    from backend.app.services.claim_service import _save_claims
    _save_claims()
    
    return review


def submit_community_review(submission: ReviewSubmission) -> ReviewRecord:
    """
    Submit a community (NGO/public) review for a claim.
    
    PRECONDITION: Claim must be in AUTHORITY_REVIEWED status.
    
    On APPROVE: Claim moves to COMMUNITY_REVIEWED
    On REJECT: Claim moves to REJECTED
    
    Args:
        submission: The review submission data.
        
    Returns:
        The created ReviewRecord.
        
    Raises:
        ReviewError: If claim not found or not in correct status.
    """
    claim = claim_service.get_claim_by_id(submission.claim_id)
    if claim is None:
        raise ReviewError(f"Claim {submission.claim_id} not found")
    
    # Enforce workflow: community review requires AUTHORITY_REVIEWED status
    if claim.status != ClaimStatus.AUTHORITY_REVIEWED:
        raise ReviewError(
            f"Community review requires claim status AUTHORITY_REVIEWED. "
            f"Current status: {claim.status.value}"
        )
    
    # Check if community review already exists
    existing = get_reviews_by_claim(submission.claim_id, role=ReviewRole.COMMUNITY)
    if existing:
        raise ReviewError(
            f"Community review already exists for claim {submission.claim_id}"
        )
    
    # Create review record
    review = ReviewRecord(
        **submission.model_dump(),
        role=ReviewRole.COMMUNITY,
    )
    reviews_db[review.id] = review
    _save_reviews()
    
    # Update claim status based on decision
    if submission.decision == ReviewDecision.APPROVE:
        claim.status = ClaimStatus.COMMUNITY_REVIEWED
    else:
        claim.status = ClaimStatus.REJECTED
    
    claim.updated_at = datetime.utcnow()
    # Persist claim update
    from backend.app.services.claim_service import _save_claims
    _save_claims()
    
    return review


def get_reviews_by_claim(
    claim_id: UUID,
    role: Optional[ReviewRole] = None,
) -> list[ReviewRecord]:
    """
    Get all reviews for a specific claim, optionally filtered by role.
    
    Args:
        claim_id: The UUID of the claim.
        role: Optional filter by reviewer role.
        
    Returns:
        List of ReviewRecord objects for the claim.
    """
    reviews = [r for r in reviews_db.values() if r.claim_id == claim_id]
    if role is not None:
        reviews = [r for r in reviews if r.role == role]
    return reviews


def get_review_by_id(review_id: UUID) -> Optional[ReviewRecord]:
    """
    Retrieve a review by its unique ID.
    
    Args:
        review_id: The UUID of the review.
        
    Returns:
        The ReviewRecord if found, None otherwise.
    """
    return reviews_db.get(review_id)


def can_mint_credits(claim_id: UUID) -> tuple[bool, str]:
    """
    Check if a claim is eligible for credit minting.
    
    REQUIREMENTS:
    1. Claim status must be COMMUNITY_REVIEWED
    2. Authority review must exist with APPROVE decision
    3. Community review must exist with APPROVE decision
    
    Args:
        claim_id: The UUID of the claim.
        
    Returns:
        Tuple of (is_eligible, reason_message)
    """
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        return False, "Claim not found"
    
    if claim.status != ClaimStatus.COMMUNITY_REVIEWED:
        return False, f"Claim status must be COMMUNITY_REVIEWED. Current: {claim.status.value}"
    
    authority_reviews = get_reviews_by_claim(claim_id, role=ReviewRole.AUTHORITY)
    if not authority_reviews:
        return False, "No authority review found"
    
    authority_approved = any(r.decision == ReviewDecision.APPROVE for r in authority_reviews)
    if not authority_approved:
        return False, "Authority review did not approve"
    
    community_reviews = get_reviews_by_claim(claim_id, role=ReviewRole.COMMUNITY)
    if not community_reviews:
        return False, "No community review found"
    
    community_approved = any(r.decision == ReviewDecision.APPROVE for r in community_reviews)
    if not community_approved:
        return False, "Community review did not approve"
    
    return True, "Eligible for minting"


def mint_credits(claim_id: UUID, amount_tonnes_co2e: float) -> MintedCredit:
    """
    Mint simulated carbon credits for a verified claim.
    
    IMPORTANT: This is a SIMULATED mint operation for MVP demonstration.
    Real implementation would interact with a blockchain.
    
    PRECONDITIONS:
    - Claim must pass can_mint_credits() check
    - Credits must not already be minted for this claim
    
    Args:
        claim_id: The UUID of the claim.
        amount_tonnes_co2e: Amount of CO2e to mint (from verified impact).
        
    Returns:
        The created MintedCredit object.
        
    Raises:
        ReviewError: If minting preconditions not met.
    """
    # Check eligibility
    is_eligible, reason = can_mint_credits(claim_id)
    if not is_eligible:
        raise ReviewError(f"Cannot mint credits: {reason}")
    
    # Check if already minted
    existing = get_minted_credit_by_claim(claim_id)
    if existing:
        raise ReviewError(f"Credits already minted for claim {claim_id}")
    
    # Get baseline NDVI from most recent MRV evidence
    # This represents the NDVI at mint time for future monitoring
    baseline_ndvi = _get_baseline_ndvi_for_mint(claim_id)
    
    # Create simulated credit with initial status
    credit = MintedCredit(
        claim_id=claim_id,
        amount_tonnes_co2e=amount_tonnes_co2e,
        status=CreditStatus.ACTIVE,
        remaining_tonnes_co2e=amount_tonnes_co2e,
        baseline_ndvi=baseline_ndvi,
    )
    minted_credits_db[credit.token_id] = credit
    _save_credits()
    
    # Update claim status to MINTED
    claim = claim_service.get_claim_by_id(claim_id)
    if claim:
        claim.status = ClaimStatus.MINTED
        claim.updated_at = datetime.utcnow()
        # Persist claim update
        from backend.app.services.claim_service import _save_claims
        _save_claims()
    
    return credit


def get_minted_credit_by_claim(claim_id: UUID) -> Optional[MintedCredit]:
    """
    Get minted credit for a specific claim.
    
    Args:
        claim_id: The UUID of the claim.
        
    Returns:
        The MintedCredit if found, None otherwise.
    """
    for credit in minted_credits_db.values():
        if credit.claim_id == claim_id:
            return credit
    return None


def get_minted_credit_by_id(token_id: UUID) -> Optional[MintedCredit]:
    """
    Retrieve a minted credit by its token ID.
    
    Args:
        token_id: The UUID of the token.
        
    Returns:
        The MintedCredit if found, None otherwise.
    """
    return minted_credits_db.get(token_id)


def _get_baseline_ndvi_for_mint(claim_id: UUID) -> Optional[float]:
    """
    Get baseline NDVI value from most recent MRV evidence for mint time baseline.
    
    For MVP, we use the monitoring NDVI from the most recent MRV evidence
    as the baseline for future post-mint monitoring.
    
    Args:
        claim_id: The UUID of the claim.
        
    Returns:
        Baseline NDVI value if found, None otherwise.
    """
    # Get all evidence for the claim
    evidence_list = evidence_service.get_evidence_for_claim(claim_id)
    
    # Find MRV evidence (contains NDVI data)
    # Look for evidence with "Satellite-based MRV" in title
    mrv_evidence = None
    for ev in reversed(evidence_list):  # Most recent first
        if "MRV" in ev.title or "NDVI" in ev.description:
            mrv_evidence = ev
            break
    
    if mrv_evidence is None:
        return None
    
    # Extract monitoring NDVI from description
    # Format: "Monitoring NDVI: 0.58" or similar
    import re
    monitoring_match = re.search(r"Monitoring[=\s]+([\d.]+)", mrv_evidence.description)
    if monitoring_match:
        try:
            return float(monitoring_match.group(1))
        except ValueError:
            pass
    
    # Fallback: return None if we can't extract
    return None
