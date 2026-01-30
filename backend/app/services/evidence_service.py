"""
CarbonChain MVP - Evidence Service

Service layer for evidence creation and retrieval.
Implements the immutability and provenance guarantees of the evidence system.

IMMUTABILITY GUARANTEE:
This service enforces that evidence records cannot be modified or deleted
once created. This is critical for:
1. Regulatory compliance - audit trails must be tamper-evident
2. Trust - stakeholders must be confident data hasn't been altered
3. Transparency - public verification requires consistent data

DESIGN DECISIONS:
- No update_evidence() function exists by design
- No delete_evidence() function exists by design
- Hash is computed automatically at creation time
- created_at timestamp is set at creation and never modified

FUTURE CONSIDERATIONS:
- Evidence could be anchored to a blockchain for additional integrity
- Distributed storage (IPFS) could be used for data_ref
- Digital signatures could be added for non-repudiation
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import UUID

from backend.app.models.evidence import (
    Evidence,
    EvidenceSubmission,
    EvidenceSummary,
    EvidenceType,
)
from backend.app.storage import atomic_write_json, read_json, uuid_to_str, str_to_uuid

# -----------------------------------------------------------------------------
# JSON file storage
# -----------------------------------------------------------------------------
STORAGE_DIR = Path("backend/app/storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_FILE = STORAGE_DIR / "evidence.json"

evidence_db: dict[UUID, Evidence] = {}


def _load_evidence() -> None:
    """Load evidence from disk on startup."""
    if not EVIDENCE_FILE.exists():
        print(f"[EVIDENCE_SERVICE] {EVIDENCE_FILE} does not exist. Starting with empty database.")
        return
    
    try:
        loaded_data = read_json(EVIDENCE_FILE, default={})
        
        evidence_db.clear()
        for evidence_id_str, evidence_data in loaded_data.items():
            try:
                evidence_id = UUID(evidence_id_str)
                evidence_data = str_to_uuid(evidence_data, ['id', 'claim_id'])
                evidence = Evidence(**evidence_data)
                evidence_db[evidence_id] = evidence
            except Exception as e:
                print(f"[EVIDENCE_SERVICE WARNING] Failed to load evidence {evidence_id_str}: {e}")
        
        print(f"[EVIDENCE_SERVICE] Loaded {len(evidence_db)} evidence records from {EVIDENCE_FILE}")
    except Exception as e:
        print(f"[EVIDENCE_SERVICE ERROR] Failed to load evidence: {e}")


def _save_evidence() -> None:
    """Save evidence to disk."""
    try:
        serializable_data = {}
        for evidence_id, evidence in evidence_db.items():
            evidence_dict = evidence.model_dump()
            serializable_data[str(evidence_id)] = uuid_to_str(evidence_dict)
        
        atomic_write_json(EVIDENCE_FILE, serializable_data)
    except Exception as e:
        print(f"[EVIDENCE_SERVICE ERROR] Failed to save evidence: {e}")


# Load on import
_load_evidence()


class EvidenceError(Exception):
    """Custom exception for evidence service errors."""

    pass


def create_evidence(submission: EvidenceSubmission) -> Evidence:
    """
    Create and store a new evidence record.

    IMMUTABILITY: Once created, this evidence record cannot be modified.
    The hash is computed automatically from the immutable fields.

    Args:
        submission: The evidence submission data.

    Returns:
        The created Evidence object with hash computed.

    Note:
        This is the ONLY way to create evidence. There is no update function.
        If evidence needs to be corrected, a new record must be created
        with appropriate documentation explaining the correction.
    """
    # Create evidence with auto-generated ID, hash, and timestamp
    evidence = Evidence(**submission.model_dump())

    # Store in database
    evidence_db[evidence.id] = evidence
    _save_evidence()

    return evidence


def create_evidence_from_dict(data: dict) -> Evidence:
    """
    Create evidence from a dictionary (used by AI MRV integration).

    Args:
        data: Dictionary containing evidence fields.

    Returns:
        The created Evidence object.
    """
    submission = EvidenceSubmission(**data)
    return create_evidence(submission)


def get_evidence_by_id(evidence_id: UUID) -> Optional[Evidence]:
    """
    Retrieve an evidence record by its unique ID.

    Args:
        evidence_id: The UUID of the evidence to retrieve.

    Returns:
        The Evidence object if found, None otherwise.
    """
    return evidence_db.get(evidence_id)


def get_evidence_for_claim(claim_id: UUID) -> list[Evidence]:
    """
    Get all evidence records for a specific claim.

    Returns evidence in chronological order (oldest first).

    Args:
        claim_id: The UUID of the claim.

    Returns:
        List of Evidence objects for the claim.
    """
    evidence_list = [e for e in evidence_db.values() if e.claim_id == claim_id]
    return sorted(evidence_list, key=lambda e: e.created_at)


def get_evidence_summaries_for_claim(claim_id: UUID) -> list[EvidenceSummary]:
    """
    Get lightweight evidence summaries for public transparency views.

    Args:
        claim_id: The UUID of the claim.

    Returns:
        List of EvidenceSummary objects for the claim.
    """
    evidence_list = get_evidence_for_claim(claim_id)
    return [
        EvidenceSummary(
            id=e.id,
            type=e.type,
            source=e.source,
            title=e.title,
            confidence_weight=e.confidence_weight,
            hash=e.hash,
            created_at=e.created_at,
            data_ref=e.data_ref,
        )
        for e in evidence_list
    ]


def verify_evidence_integrity(evidence_id: UUID) -> tuple[bool, str]:
    """
    Verify the integrity of an evidence record by checking its hash.

    This function allows any party to verify that evidence has not been
    tampered with since creation.

    Args:
        evidence_id: The UUID of the evidence to verify.

    Returns:
        Tuple of (is_valid, message)
    """
    evidence = get_evidence_by_id(evidence_id)
    if evidence is None:
        return False, "Evidence not found"

    if evidence.verify_hash():
        return True, "Evidence integrity verified - hash matches"
    else:
        return False, "INTEGRITY FAILURE - hash mismatch detected"


def create_ai_mrv_evidence(
    claim_id: UUID,
    baseline_start: str,
    baseline_end: str,
    monitoring_start: str,
    monitoring_end: str,
    baseline_ndvi: Optional[float],
    monitoring_ndvi: Optional[float],
    delta_ndvi: Optional[float],
    min_co2e: Optional[float],
    max_co2e: Optional[float],
    confidence: str = "medium",
    data_ref: Optional[str] = None,
    failure_reason: Optional[str] = None,
) -> Evidence:
    """
    Create a SYSTEM_AI evidence record from AI MRV verification results.

    This function is called automatically when AI MRV verification completes.
    It creates an immutable record of the satellite-based analysis.

    Args:
        claim_id: The claim being verified.
        baseline_start: Start date of baseline period.
        baseline_end: End date of baseline period.
        monitoring_start: Start date of monitoring period.
        monitoring_end: End date of monitoring period.
        baseline_ndvi: Mean NDVI for baseline period.
        monitoring_ndvi: Mean NDVI for monitoring period.
        delta_ndvi: Change in NDVI.
        min_co2e: Minimum CO₂e estimate.
        max_co2e: Maximum CO₂e estimate.
        confidence: Confidence level of the analysis.

    Returns:
        The created Evidence object.
    """
    # Format values safely
    baseline_str = f"{baseline_ndvi:.4f}" if baseline_ndvi is not None else "N/A"
    monitoring_str = f"{monitoring_ndvi:.4f}" if monitoring_ndvi is not None else "N/A"
    delta_str = f"{delta_ndvi:+.4f}" if delta_ndvi is not None else "N/A"
    co2_str = (
        f"{min_co2e:.1f}-{max_co2e:.1f}"
        if min_co2e is not None and max_co2e is not None
        else "N/A"
    )

    # Build description with failure reason if applicable
    description = (
        f"Satellite-based MRV analysis using Sentinel-2 Surface Reflectance imagery. "
        f"Baseline period: {baseline_start} to {baseline_end}. "
        f"Monitoring period: {monitoring_start} to {monitoring_end}. "
        f"NDVI Results: Baseline={baseline_str}, Monitoring={monitoring_str}, Delta={delta_str}. "
        f"Estimated CO₂e impact: {co2_str} tonnes. "
        f"Analysis confidence: {confidence}. "
        f"Methodology: Cloud-masked median composite with SCL filtering."
    )
    
    # Add failure reason if provided (for rejected claims)
    if failure_reason:
        description += f" Result: {failure_reason}"

    # Map confidence to weight
    confidence_weights = {
        "low": 0.4,
        "medium": 0.7,
        "high": 0.9,
    }
    weight = confidence_weights.get(confidence.lower(), 0.7)

    # Use provided data_ref (preview image path) or fallback to GEE reference
    # Ensure data_ref is never None or empty (required by EvidenceSubmission)
    if data_ref and isinstance(data_ref, str) and data_ref.strip():
        evidence_data_ref = data_ref.strip()
    else:
        evidence_data_ref = f"gee://sentinel2/ndvi/claim-{claim_id}"
    
    # Ensure data_ref doesn't exceed max_length (max_length=1000)
    if len(evidence_data_ref) > 1000:
        evidence_data_ref = evidence_data_ref[:1000]
    
    # Ensure description meets minimum length requirement (min_length=10)
    if len(description) < 10:
        description = description + " " * (10 - len(description))
    
    # Ensure description doesn't exceed max_length (max_length=10000)
    if len(description) > 10000:
        description = description[:10000]
    
    # Ensure title meets minimum length requirement (min_length=3)
    title = "Satellite-based MRV (Sentinel-2)"
    if len(title) < 3:
        title = "MRV Analysis"
    
    # Ensure title doesn't exceed max_length (max_length=200)
    if len(title) > 200:
        title = title[:200]
    
    submission = EvidenceSubmission(
        claim_id=claim_id,
        type=EvidenceType.SYSTEM_AI,
        source="system",
        title=title,
        description=description,
        data_ref=evidence_data_ref,
        confidence_weight=weight,
    )

    return create_evidence(submission)


# -----------------------------------------------------------------------------
# NOTE: The following functions are intentionally NOT implemented
# -----------------------------------------------------------------------------
#
# def update_evidence(...):
#     """NOT IMPLEMENTED BY DESIGN - Evidence is immutable."""
#     raise NotImplementedError("Evidence records are immutable and cannot be updated")
#
# def delete_evidence(...):
#     """NOT IMPLEMENTED BY DESIGN - Evidence is immutable."""
#     raise NotImplementedError("Evidence records are immutable and cannot be deleted")
#
# If evidence needs to be corrected, create a new evidence record with:
# - Type: DOCUMENT or COMMUNITY_REPORT
# - Title: "Correction to evidence {original_id}"
# - Description: Explanation of what was incorrect and the correction
# -----------------------------------------------------------------------------
