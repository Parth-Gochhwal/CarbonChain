"""
CarbonChain MVP - Credit Monitoring Service

Service layer for post-mint credit lifecycle monitoring.
Implements deterministic burn rules based on NDVI degradation.

DESIGN PRINCIPLES:
1. DETERMINISTIC: All burn decisions use explicit thresholds, no ML or heuristics
2. CONSERVATIVE: System errs on the side of caution when detecting degradation
3. AUDITABLE: Every monitoring run creates immutable SYSTEM_AI evidence
4. EXPLAINABLE: All decisions are documented with clear reasoning

BURN RULES (deterministic thresholds):
- delta_ndvi >= -0.05 → OK (no action)
- -0.05 > delta_ndvi >= -0.15 → WARNING → CreditStatus.AT_RISK
- -0.15 > delta_ndvi >= -0.30 → FAILURE → Partial burn
- delta_ndvi < -0.30 → FAILURE → Full burn

Partial burn calculation:
burn_percentage = abs(delta_ndvi) / 0.30 (capped at 1.0)
burn_amount = remaining_tonnes_co2e * burn_percentage
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import ee

from backend.app.earth_engine.change_detection import compute_ndvi_change
from backend.app.earth_engine.ee_client import init_ee
from backend.app.models.claim import Claim
from backend.app.models.monitoring import MonitoringOutcome, MonitoringRun
from backend.app.models.review import CreditStatus, MintedCredit
from backend.app.services import claim_service, evidence_service
from backend.app.services.review_service import minted_credits_db


# -----------------------------------------------------------------------------
# JSON file storage
# -----------------------------------------------------------------------------
from pathlib import Path
from backend.app.storage import atomic_write_json, read_json, uuid_to_str, str_to_uuid

STORAGE_DIR = Path("backend/app/storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
MONITORING_FILE = STORAGE_DIR / "monitoring.json"

monitoring_runs_db: dict[UUID, MonitoringRun] = {}


def _load_monitoring() -> None:
    """Load monitoring runs from disk on startup."""
    if not MONITORING_FILE.exists():
        print(f"[MONITORING_SERVICE] {MONITORING_FILE} does not exist. Starting with empty database.")
        return
    
    try:
        loaded_data = read_json(MONITORING_FILE, default={})
        
        monitoring_runs_db.clear()
        for monitoring_id_str, monitoring_data in loaded_data.items():
            try:
                monitoring_id = UUID(monitoring_id_str)
                monitoring_data = str_to_uuid(monitoring_data, ['id', 'claim_id', 'credit_id'])
                monitoring_run = MonitoringRun(**monitoring_data)
                monitoring_runs_db[monitoring_id] = monitoring_run
            except Exception as e:
                print(f"[MONITORING_SERVICE WARNING] Failed to load monitoring run {monitoring_id_str}: {e}")
        
        print(f"[MONITORING_SERVICE] Loaded {len(monitoring_runs_db)} monitoring runs from {MONITORING_FILE}")
    except Exception as e:
        print(f"[MONITORING_SERVICE ERROR] Failed to load monitoring runs: {e}")


def _save_monitoring() -> None:
    """Save monitoring runs to disk."""
    try:
        serializable_data = {}
        for monitoring_id, monitoring_run in monitoring_runs_db.items():
            monitoring_dict = monitoring_run.model_dump()
            serializable_data[str(monitoring_id)] = uuid_to_str(monitoring_dict)
        
        atomic_write_json(MONITORING_FILE, serializable_data)
    except Exception as e:
        print(f"[MONITORING_SERVICE ERROR] Failed to save monitoring runs: {e}")


# Load on import
_load_monitoring()


class MonitoringError(Exception):
    """Custom exception for monitoring service errors."""
    pass


def run_monitoring(claim_id: UUID, credit_id: UUID) -> MonitoringRun:
    """
    Run post-mint monitoring for a credit.
    
    This function:
    1. Retrieves the credit and claim
    2. Gets current NDVI using Sentinel-2 pipeline
    3. Compares against baseline NDVI recorded at mint time
    4. Applies deterministic burn rules
    5. Updates credit status and remaining amount if needed
    6. Creates immutable SYSTEM_AI evidence record
    
    Args:
        claim_id: ID of the claim associated with the credit.
        credit_id: ID of the credit to monitor.
    
    Returns:
        The created MonitoringRun object.
    
    Raises:
        MonitoringError: If credit/claim not found or monitoring fails.
    """
    # Retrieve credit
    credit = minted_credits_db.get(credit_id)
    if credit is None:
        raise MonitoringError(f"Credit {credit_id} not found")
    
    if credit.claim_id != claim_id:
        raise MonitoringError(
            f"Credit {credit_id} does not belong to claim {claim_id}"
        )
    
    # Retrieve claim
    claim = claim_service.get_claim_by_id(claim_id)
    if claim is None:
        raise MonitoringError(f"Claim {claim_id} not found")
    
    # Check if credit has baseline NDVI
    if credit.baseline_ndvi is None:
        raise MonitoringError(
            f"Credit {credit_id} has no baseline NDVI recorded. Cannot monitor."
        )
    
    # Get current NDVI using Sentinel-2 pipeline
    # Use claim location and recent date range
    geometry = ee.Geometry.Point([claim.location.longitude, claim.location.latitude])
    
    # Use last 90 days for current NDVI (conservative recent window)
    run_date = datetime.utcnow()
    monitoring_end = run_date.strftime("%Y-%m-%d")
    monitoring_start = (run_date - timedelta(days=90)).strftime("%Y-%m-%d")
    
    # Baseline period: use mint date as reference (90 days before mint)
    mint_date = credit.minted_at
    baseline_end = mint_date.strftime("%Y-%m-%d")
    baseline_start = (mint_date - timedelta(days=90)).strftime("%Y-%m-%d")
    
    try:
        init_ee()
        ndvi_result = compute_ndvi_change(
            geometry=geometry,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            monitoring_start=monitoring_start,
            monitoring_end=monitoring_end,
        )
    except Exception as e:
        raise MonitoringError(f"Failed to compute NDVI change: {str(e)}")
    
    if ndvi_result["monitoring_ndvi"] is None:
        raise MonitoringError("Failed to retrieve current NDVI from Sentinel-2")
    
    current_ndvi = ndvi_result["monitoring_ndvi"]
    baseline_ndvi = credit.baseline_ndvi
    delta_ndvi = current_ndvi - baseline_ndvi
    
    # Apply deterministic burn rules
    outcome, burn_amount = _apply_burn_rules(credit, delta_ndvi)
    
    # Create monitoring run record
    monitoring_run = MonitoringRun(
        claim_id=claim_id,
        credit_id=credit_id,
        run_date=run_date,
        baseline_ndvi=baseline_ndvi,
        current_ndvi=current_ndvi,
        delta_ndvi=delta_ndvi,
        outcome=outcome,
    )
    
    # Store monitoring run
    monitoring_runs_db[monitoring_run.id] = monitoring_run
    _save_monitoring()
    
    # Persist credit update
    from backend.app.services.review_service import _save_credits
    _save_credits()
    
    # Update credit if burn occurred
    if burn_amount > 0:
        credit.remaining_tonnes_co2e = max(0.0, credit.remaining_tonnes_co2e - burn_amount)
        
        if credit.remaining_tonnes_co2e <= 0:
            credit.status = CreditStatus.FULLY_BURNED
        elif credit.status == CreditStatus.ACTIVE:
            credit.status = CreditStatus.PARTIALLY_BURNED
        # If already AT_RISK or PARTIALLY_BURNED, keep current status
    
    # Update credit status for warnings
    if outcome == MonitoringOutcome.WARNING:
        if credit.status == CreditStatus.ACTIVE:
            credit.status = CreditStatus.AT_RISK
    
    # Create immutable SYSTEM_AI evidence record
    _create_monitoring_evidence(claim, credit, monitoring_run, burn_amount)
    
    return monitoring_run


def _apply_burn_rules(
    credit: MintedCredit,
    delta_ndvi: float,
) -> tuple[MonitoringOutcome, float]:
    """
    Apply deterministic burn rules based on NDVI delta.
    
    Rules:
    - delta_ndvi >= -0.05 → OK (no burn)
    - -0.05 > delta_ndvi >= -0.15 → WARNING (no burn, status to AT_RISK)
    - -0.15 > delta_ndvi >= -0.30 → FAILURE (partial burn)
    - delta_ndvi < -0.30 → FAILURE (full burn)
    
    Args:
        credit: The credit being monitored.
        delta_ndvi: Change in NDVI (current - baseline).
    
    Returns:
        Tuple of (outcome, burn_amount)
    """
    if delta_ndvi >= -0.05:
        return (MonitoringOutcome.OK, 0.0)
    
    elif delta_ndvi >= -0.15:
        return (MonitoringOutcome.WARNING, 0.0)
    
    elif delta_ndvi >= -0.30:
        # Partial burn
        burn_percentage = abs(delta_ndvi) / 0.30  # Capped at 1.0 by threshold
        burn_amount = credit.remaining_tonnes_co2e * burn_percentage
        return (MonitoringOutcome.FAILURE, burn_amount)
    
    else:
        # Full burn
        return (MonitoringOutcome.FAILURE, credit.remaining_tonnes_co2e)


def _create_monitoring_evidence(
    claim: Claim,
    credit: MintedCredit,
    monitoring_run: MonitoringRun,
    burn_amount: float,
) -> None:
    """
    Create an immutable SYSTEM_AI evidence record for a monitoring run.
    
    Args:
        claim: The claim associated with the credit.
        credit: The credit being monitored.
        monitoring_run: The monitoring run result.
        burn_amount: Amount burned (if any).
    """
    from backend.app.models.evidence import EvidenceSubmission, EvidenceType
    
    # Build description with all required information
    burn_info = ""
    if burn_amount > 0:
        burn_info = f"Burn decision: {burn_amount:.2f} tCO2e burned. "
        if credit.status == CreditStatus.FULLY_BURNED:
            burn_info += "Credit fully burned. "
        elif credit.status == CreditStatus.PARTIALLY_BURNED:
            burn_info += "Credit partially burned. "
    else:
        burn_info = "No burn required. "
    
    threshold_info = ""
    if monitoring_run.outcome == MonitoringOutcome.OK:
        threshold_info = "Threshold: delta >= -0.05 (OK). "
    elif monitoring_run.outcome == MonitoringOutcome.WARNING:
        threshold_info = "Threshold: -0.15 <= delta < -0.05 (WARNING). "
    elif monitoring_run.delta_ndvi >= -0.30:
        threshold_info = "Threshold: -0.30 <= delta < -0.15 (PARTIAL BURN). "
    else:
        threshold_info = "Threshold: delta < -0.30 (FULL BURN). "
    
    description = (
        f"Post-mint credit monitoring run. "
        f"Baseline NDVI: {monitoring_run.baseline_ndvi:.4f}. "
        f"Current NDVI: {monitoring_run.current_ndvi:.4f}. "
        f"Delta NDVI: {monitoring_run.delta_ndvi:+.4f}. "
        f"Outcome: {monitoring_run.outcome.value.upper()}. "
        f"{threshold_info}"
        f"{burn_info}"
        f"Credit status: {credit.status.value}. "
        f"Remaining CO₂e: {credit.remaining_tonnes_co2e:.2f} tonnes. "
        f"This monitoring run uses deterministic thresholds for burn decisions."
    )
    
    submission = EvidenceSubmission(
        claim_id=claim.id,
        type=EvidenceType.SYSTEM_AI,
        source="system",
        title="Credit Monitoring Run",
        description=description,
        data_ref=f"monitoring://credit-{credit.token_id}/run-{monitoring_run.id}",
        confidence_weight=0.8,  # High confidence in deterministic monitoring
    )
    
    evidence_service.create_evidence(submission)


def get_monitoring_runs_by_credit(credit_id: UUID) -> list[MonitoringRun]:
    """
    Get all monitoring runs for a specific credit.
    
    Returns runs in chronological order (oldest first).
    
    Args:
        credit_id: The UUID of the credit.
    
    Returns:
        List of MonitoringRun objects for the credit.
    """
    runs = [r for r in monitoring_runs_db.values() if r.credit_id == credit_id]
    return sorted(runs, key=lambda r: r.run_date)


def get_monitoring_runs_by_claim(claim_id: UUID) -> list[MonitoringRun]:
    """
    Get all monitoring runs for a specific claim.
    
    Returns runs in chronological order (oldest first).
    
    Args:
        claim_id: The UUID of the claim.
    
    Returns:
        List of MonitoringRun objects for the claim.
    """
    runs = [r for r in monitoring_runs_db.values() if r.claim_id == claim_id]
    return sorted(runs, key=lambda r: r.run_date)
