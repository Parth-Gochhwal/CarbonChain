"""
CarbonChain MVP - Verification Service

Service layer for claim verification operations.
Uses in-memory storage for MVP demonstration purposes.

EVIDENCE INTEGRATION:
When verification completes, this service automatically creates a SYSTEM_AI
evidence record that captures the MRV analysis results. This evidence is
immutable and provides an auditable record of the verification.

REAL MRV COMPUTATION:
This service now uses real satellite-based NDVI computation and CO₂ estimation
via Earth Engine, replacing all mocked values with actual calculations.
"""

import requests
from datetime import datetime, timedelta
from math import isnan
from pathlib import Path
from typing import Optional
from uuid import UUID

import ee
from shapely.geometry import shape

from backend.app.earth_engine.change_detection import compute_ndvi_change
from backend.app.earth_engine.ee_client import init_ee
from backend.app.earth_engine.sentinel2 import get_sentinel2_rgb_preview
from backend.app.mrv import estimate_co2e_from_ndvi_delta
from backend.app.models.ai_verdict import AIConsistencyResult
from backend.app.models.claim import Claim, ClaimStatus
from backend.app.models.verification import (
    ConfidenceLevel,
    VerificationOutcome,
    VerificationResult,
    VerificationStatus,
    VerifiedCarbonImpact,
)
from backend.app.services.claim_service import claims_db
from backend.app.services import evidence_service
from backend.app.services import ai_consistency_service

# -----------------------------------------------------------------------------
# JSON file storage
# -----------------------------------------------------------------------------
from pathlib import Path
from backend.app.storage import atomic_write_json, read_json, uuid_to_str, str_to_uuid

STORAGE_DIR = Path("backend/app/storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
VERIFICATIONS_FILE = STORAGE_DIR / "verifications.json"

verifications_db: dict[UUID, VerificationResult] = {}


def _load_verifications() -> None:
    """Load verifications from disk on startup."""
    if not VERIFICATIONS_FILE.exists():
        print(f"[VERIFICATION_SERVICE] {VERIFICATIONS_FILE} does not exist. Starting with empty database.")
        return
    
    try:
        loaded_data = read_json(VERIFICATIONS_FILE, default={})
        
        verifications_db.clear()
        for verification_id_str, verification_data in loaded_data.items():
            try:
                verification_id = UUID(verification_id_str)
                verification_data = str_to_uuid(verification_data, ['id', 'claim_id'])
                verification = VerificationResult(**verification_data)
                verifications_db[verification_id] = verification
            except Exception as e:
                print(f"[VERIFICATION_SERVICE WARNING] Failed to load verification {verification_id_str}: {e}")
        
        print(f"[VERIFICATION_SERVICE] Loaded {len(verifications_db)} verifications from {VERIFICATIONS_FILE}")
    except Exception as e:
        print(f"[VERIFICATION_SERVICE ERROR] Failed to load verifications: {e}")


def _save_verifications() -> None:
    """Save verifications to disk."""
    try:
        serializable_data = {}
        for verification_id, verification in verifications_db.items():
            verification_dict = verification.model_dump()
            serializable_data[str(verification_id)] = uuid_to_str(verification_dict)
        
        atomic_write_json(VERIFICATIONS_FILE, serializable_data)
    except Exception as e:
        print(f"[VERIFICATION_SERVICE ERROR] Failed to save verifications: {e}")


# Load on import
_load_verifications()


def verify_claim(claim: Claim) -> VerificationResult:
    """
    Perform real satellite-based MRV verification of a climate action claim.

    REAL MRV COMPUTATION:
    This function now uses actual Earth Engine satellite analysis:
    - Computes real NDVI change from Sentinel-2 imagery
    - Estimates CO₂e from NDVI delta using conservative biomass models
    - Creates VerificationResult with real computed values
    - Updates claim status to AI_ANALYZED
    - Creates immutable SYSTEM_AI evidence records with real data

    IMPORTANT: AI MRV estimates are independent of the claim and verification outcome.
    The verification outcome (APPROVED/REJECTED) is based on real satellite analysis.

    Args:
        claim: The Claim object to verify.

    Returns:
        The VerificationResult with real satellite-based verification data.
    """
    print(f"[MRV] ========================================")
    print(f"[MRV] Starting real satellite-based verification for claim {claim.id}")
    print(f"[MRV] Claim type: {claim.claim_type.value}")
    print(f"[MRV] Claim area: {claim.area_hectares} hectares")
    print(f"[MRV] Claim location: {claim.location.latitude:.6f}, {claim.location.longitude:.6f}")
    
    # Initialize Earth Engine (idempotent)
    print(f"[MRV] Initializing Earth Engine...")
    init_ee()
    print(f"[MRV] Earth Engine initialized successfully")
    
    # Convert claim geometry to Earth Engine Geometry
    # REAL MRV: Use actual claim geometry (polygon or buffer) for satellite analysis
    if claim.geometry_geojson is None:
        error_msg = f"Claim {claim.id} has no geometry - cannot perform satellite analysis"
        print(f"[MRV ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    # Convert GeoJSON to Earth Engine Geometry
    # REAL MRV: Convert claim geometry to Earth Engine format for satellite analysis
    shapely_geom = shape(claim.geometry_geojson)
    if shapely_geom.geom_type == "Polygon":
        # Earth Engine Polygon expects: [[[lon, lat], [lon, lat], ...]]
        # Exterior ring coordinates (exclude last duplicate point)
        coords = list(shapely_geom.exterior.coords)[:-1]  # Remove duplicate closing point
        ee_geometry = ee.Geometry.Polygon([[[lon, lat] for lon, lat in coords]])
    elif shapely_geom.geom_type == "MultiPolygon":
        # Earth Engine MultiPolygon expects: [[[[lon, lat], ...]], [[[lon, lat], ...]], ...]
        polygons = []
        for poly in shapely_geom.geoms:
            coords = list(poly.exterior.coords)[:-1]  # Remove duplicate closing point
            polygons.append([[lon, lat] for lon, lat in coords])
        ee_geometry = ee.Geometry.MultiPolygon(polygons)
    else:
        raise ValueError(f"Unsupported geometry type: {shapely_geom.geom_type}")
    
    print(f"[MRV] Geometry converted: {shapely_geom.geom_type}, Area: {shapely_geom.area:.6f} deg²")
    print(f"[MRV] Geometry source: {claim.geometry_source.value if claim.geometry_source else 'unknown'}")
    print(f"[MRV] Geometry type: {claim.geometry_type.value if claim.geometry_type else 'unknown'}")
    
    # REAL MRV: Calculate date ranges from claim dates
    # Baseline: 1 year before action start
    # Monitoring: action start to end (or 1 year after start if no end)
    action_start = claim.action_start_date
    # If no end date, use 1 year after start for monitoring period
    if claim.action_end_date:
        action_end = claim.action_end_date
    else:
        action_end = action_start + timedelta(days=365)
    
    # Baseline period: 1 year before action start
    baseline_end = action_start - timedelta(days=1)
    baseline_start = baseline_end - timedelta(days=365)
    
    baseline_start_str = baseline_start.strftime("%Y-%m-%d")
    baseline_end_str = baseline_end.strftime("%Y-%m-%d")
    monitoring_start_str = action_start.strftime("%Y-%m-%d")
    monitoring_end_str = action_end.strftime("%Y-%m-%d")
    
    print(f"[MRV] Baseline period: {baseline_start_str} to {baseline_end_str}")
    print(f"[MRV] Monitoring period: {monitoring_start_str} to {monitoring_end_str}")
    
    # REAL MRV: Compute actual NDVI change from Sentinel-2 satellite imagery
    # This calls the same function used in test.py - real Earth Engine computation
    land_cover_type = "forest" if claim.claim_type.value in ["reforestation", "mangrove_restoration", "wetland_restoration"] else None
    ndvi_result = compute_ndvi_change(
        geometry=ee_geometry,
        baseline_start=baseline_start_str,
        baseline_end=baseline_end_str,
        monitoring_start=monitoring_start_str,
        monitoring_end=monitoring_end_str,
        land_cover=land_cover_type,
    )
    
    baseline_ndvi = ndvi_result.get("baseline_ndvi")
    monitoring_ndvi = ndvi_result.get("monitoring_ndvi")
    delta_ndvi = ndvi_result.get("delta_ndvi")
    
    print(f"[MRV] ========================================")
    print(f"[MRV] NDVI COMPUTATION RESULTS:")
    print(f"[MRV]   Baseline NDVI: {baseline_ndvi:.4f}")
    print(f"[MRV]   Monitoring NDVI: {monitoring_ndvi:.4f}")
    print(f"[MRV]   Delta NDVI: {delta_ndvi:+.4f}")
    print(f"[MRV] ========================================")
    
    # Validate NDVI results - prevent None and NaN values
    if baseline_ndvi is None or monitoring_ndvi is None or delta_ndvi is None:
        raise ValueError(f"Insufficient satellite data for claim {claim.id}. NDVI computation returned None values.")
    if not isinstance(baseline_ndvi, (int, float)) or not isinstance(monitoring_ndvi, (int, float)) or not isinstance(delta_ndvi, (int, float)):
        raise ValueError(f"Invalid NDVI data types for claim {claim.id}. Expected numbers, got: baseline={type(baseline_ndvi)}, monitoring={type(monitoring_ndvi)}, delta={type(delta_ndvi)}")
    if isnan(baseline_ndvi) or isnan(monitoring_ndvi) or isnan(delta_ndvi):
        raise ValueError(f"NaN NDVI values for claim {claim.id}. Baseline={baseline_ndvi}, Monitoring={monitoring_ndvi}, Delta={delta_ndvi}")
    
    # REAL MRV: Estimate CO₂e from actual NDVI delta using conservative biomass model
    # This calls the same function used in test.py - real carbon estimation
    if claim.area_hectares is None or claim.area_hectares <= 0:
        raise ValueError(f"Claim {claim.id} has invalid area_hectares: {claim.area_hectares}")
    
    carbon_estimate = estimate_co2e_from_ndvi_delta(
        delta_ndvi=delta_ndvi,
        area_hectares=claim.area_hectares,
    )
    
    # REAL MRV: Use actual computed CO₂e estimates (not mocked multipliers)
    ai_mrv_min = carbon_estimate["min_tonnes_co2e"]
    ai_mrv_max = carbon_estimate["max_tonnes_co2e"]
    
    # VALIDATION: Ensure CO₂e estimates are valid numbers (not NaN)
    if not isinstance(ai_mrv_min, (int, float)) or not isinstance(ai_mrv_max, (int, float)):
        raise ValueError(f"Invalid CO₂e estimate types for claim {claim.id}: min={type(ai_mrv_min)}, max={type(ai_mrv_max)}")
    if isnan(ai_mrv_min) or isnan(ai_mrv_max):
        raise ValueError(f"NaN CO₂e estimates for claim {claim.id}: min={ai_mrv_min}, max={ai_mrv_max}")
    
    print(f"[MRV] ========================================")
    print(f"[MRV] CO₂ ESTIMATION RESULTS:")
    print(f"[MRV]   AI MRV Min CO₂e: {ai_mrv_min:.2f} tonnes")
    print(f"[MRV]   AI MRV Max CO₂e: {ai_mrv_max:.2f} tonnes")
    print(f"[MRV]   Claim Area: {claim.area_hectares:.2f} hectares")
    print(f"[MRV] ========================================")
    
    # MRV RESULT CLASSIFICATION: Determine if claim shows positive carbon impact
    # Negative or zero CO₂e means degradation or no gain - scientifically valid but claim should be rejected
    has_positive_carbon_impact = ai_mrv_max > 0
    
    if not has_positive_carbon_impact:
        # SCIENTIFIC RESULT: Negative or zero carbon impact detected
        # This is NOT an error - it's a valid scientific finding (degradation/no gain)
        print(f"[MRV_RESULT] status=failed reason=negative_carbon max_co2e={ai_mrv_max:.2f} delta_ndvi={delta_ndvi:.4f}")
        print(f"[MRV] Negative CO2 detected — clamping verified impact to zero. AI MRV raw estimate preserved for transparency: {ai_mrv_min:.2f}-{ai_mrv_max:.2f} tCO2e")
        
        # DATA MODEL SEPARATION: AI MRV estimates (can be negative) vs VerifiedCarbonImpact (must be >= 0)
        # Preserve raw negative AI MRV values in evidence/logs for scientific transparency
        # But clamp verified impact to >= 0 for governance/approval purposes
        # SAFE CLAMPING RULE: When AI MRV CO2 estimate < 0:
        # - Store raw negative value in AI MRV evidence (for transparency)
        # - Set verified_min_tonnes_co2e = 0
        # - Set verified_max_tonnes_co2e = max(0, ai_estimate_max) = 0
        verified_min = 0.0  # Clamp to zero for verified impact
        verified_max = max(0.0, ai_mrv_max)  # Clamp to zero (ai_mrv_max <= 0)
        point_estimate = 0.0  # Point estimate is zero when max is <= 0
        
        # Determine confidence level based on NDVI delta magnitude
        # Even for negative results, we want to know how confident we are in the measurement
        if abs(delta_ndvi) > 0.15:
            confidence_level = ConfidenceLevel.HIGH
        elif abs(delta_ndvi) > 0.05:
            confidence_level = ConfidenceLevel.MEDIUM
        else:
            confidence_level = ConfidenceLevel.LOW
        
        # Create VerifiedCarbonImpact with clamped values (>= 0)
        # This represents the verified impact available for governance approval
        # Raw negative AI MRV values are preserved in evidence for scientific transparency
        verified_impact = VerifiedCarbonImpact(
            min_tonnes_co2e=verified_min,  # Clamped to 0.0
            max_tonnes_co2e=verified_max,  # Clamped to 0.0
            point_estimate_tonnes_co2e=point_estimate,  # 0.0
            confidence=confidence_level,
            methodology_used=f"Real satellite-based MRV: Sentinel-2 NDVI analysis ({baseline_start_str} to {monitoring_end_str}), "
                            f"conservative biomass model. "
                            f"NDVI delta: {delta_ndvi:.4f} (negative indicates degradation), Area: {claim.area_hectares:.2f} ha. "
                            f"AI MRV raw estimate: {ai_mrv_min:.2f}-{ai_mrv_max:.2f} tCO2e (negative = degradation). "
                            f"Verified impact clamped to 0.0 (no positive carbon sequestration detected).",
            deviation_from_claim_percent=None,  # Not applicable for rejected claims
        )
        
        # Create verification result with REJECTED outcome
        # PIPELINE CONTINUITY: Always create a valid VerificationResult, even for negative CO2
        # This ensures the frontend never hangs waiting for a response
        verification = VerificationResult(
            claim_id=claim.id,
            status=VerificationStatus.COMPLETED,
            outcome=VerificationOutcome.REJECTED,
            verified_impact=verified_impact,  # Clamped to >= 0
            overall_confidence=confidence_level,
            summary=f"Real satellite-based verification completed. NDVI delta: {delta_ndvi:.4f} (negative/zero indicates degradation or no gain). "
                    f"AI MRV raw estimate: {ai_mrv_min:.2f}-{ai_mrv_max:.2f} tCO2e (negative = degradation). "
                    f"Verified impact: {verified_min:.2f}-{verified_max:.2f} tCO2e (clamped to zero). "
                    f"No positive carbon sequestration detected. Claim rejected.",
            verification_notes=f"AI MRV analysis detected negative or zero carbon impact. "
                             f"Raw AI estimate: {ai_mrv_min:.2f}-{ai_mrv_max:.2f} tCO2e. "
                             f"Verified impact clamped to 0.0 for governance purposes. "
                             f"Raw negative values preserved in evidence for scientific transparency.",
            completed_at=datetime.utcnow(),
            verifier_id="system-satellite-mrv",
        )
        
        print(f"[MRV_RESULT] Verification result created: {verification.id}, Outcome: REJECTED, Confidence: {confidence_level.value}")
        
        # Store verification
        verifications_db[verification.id] = verification
        _save_verifications()
        
        # Update claim status to AI_REJECTED (analysis completed, no positive impact)
        claim.status = ClaimStatus.AI_REJECTED
        claim.verification_id = verification.id
        claim.updated_at = datetime.utcnow()
        
        # Persist claim update
        from backend.app.services.claim_service import _save_claims
        _save_claims()
        
        # Generate and save MRV preview image
        preview_image_path = _generate_and_save_mrv_preview(
            claim,
            ee_geometry,
            monitoring_start_str,
            monitoring_end_str,
        )
        
        # Always create evidence even on failure - this is critical for audit trail
        # EVIDENCE INTEGRITY: Store raw AI MRV values (can be negative) for scientific transparency
        # The evidence preserves the actual AI computation results, while verified_impact is clamped to >= 0
        _create_mrv_evidence(
            claim, 
            verification, 
            ai_mrv_min,  # Raw AI MRV value (can be negative) - preserved for transparency
            ai_mrv_max,  # Raw AI MRV value (can be negative) - preserved for transparency
            baseline_start_str,
            baseline_end_str,
            monitoring_start_str,
            monitoring_end_str,
            baseline_ndvi,
            monitoring_ndvi,
            delta_ndvi,
            preview_image_path,
            failure_reason=f"No positive carbon sequestration detected. Satellite data shows degradation or no gain. "
                          f"AI MRV raw estimate: {ai_mrv_min:.2f}-{ai_mrv_max:.2f} tCO2e (negative = degradation). "
                          f"Verified impact clamped to 0.0 for governance approval purposes."
        )
        
        print(f"[MRV_RESULT] Claim {claim.id} rejected. Status: {claim.status.value}. Evidence created.")
        print(f"[MRV] AI MRV raw estimate preserved for transparency: {ai_mrv_min:.2f}-{ai_mrv_max:.2f} tCO2e")
        print(f"[MRV] ========================================")
        print(f"[MRV] VERIFICATION COMPLETED (REJECTED)")
        print(f"[MRV]   Claim ID: {claim.id}")
        print(f"[MRV]   Final Status: {claim.status.value}")
        print(f"[MRV]   Verification Outcome: {verification.outcome.value}")
        print(f"[MRV]   Verification ID: {verification.id}")
        print(f"[MRV]   Evidence records created: 1 (MRV)")
        print(f"[MRV] ========================================")
        
        # PIPELINE CONTINUITY: Always return a valid VerificationResult
        # This ensures the frontend never hangs and the claim status always transitions
        # Return early - no consistency evaluation needed for rejected claims
        return verification
    
    # POSITIVE CARBON IMPACT PATH: Continue with normal verification flow
    # Verification outcome: Use conservative adjustment of AI estimate
    # This represents the verification decision, separate from AI MRV estimate
    verified_min = ai_mrv_min * 0.9  # 10% conservative adjustment
    verified_max = ai_mrv_max * 0.9
    point_estimate = (verified_min + verified_max) / 2
    
    original_min = claim.carbon_impact_estimate.min_tonnes_co2e
    original_max = claim.carbon_impact_estimate.max_tonnes_co2e
    deviation_from_claim = ((point_estimate - (original_min + original_max) / 2) / ((original_min + original_max) / 2)) * 100

    # Determine confidence level based on NDVI delta magnitude
    # REAL MRV: Confidence based on actual vegetation change signal strength
    if abs(delta_ndvi) > 0.15:
        confidence_level = ConfidenceLevel.HIGH
    elif abs(delta_ndvi) > 0.05:
        confidence_level = ConfidenceLevel.MEDIUM
    else:
        confidence_level = ConfidenceLevel.LOW
    
    # DATA MODEL SEPARATION: VerifiedCarbonImpact must be >= 0
    # AI MRV raw estimates (ai_mrv_min/max) can be negative, but verified impact is clamped
    # Safety check: Ensure verified values are never negative
    if verified_min < 0 or verified_max < 0:
        print(f"[MRV WARNING] Verified impact was negative. Clamping to zero. Original: {verified_min:.2f}-{verified_max:.2f}")
        verified_min = max(0.0, verified_min)
        verified_max = max(0.0, verified_max)
        point_estimate = (verified_min + verified_max) / 2
    
    verified_impact = VerifiedCarbonImpact(
        min_tonnes_co2e=verified_min,  # Guaranteed >= 0
        max_tonnes_co2e=verified_max,  # Guaranteed >= 0
        point_estimate_tonnes_co2e=point_estimate,  # Guaranteed >= 0
        confidence=confidence_level,
        methodology_used=f"Real satellite-based MRV: Sentinel-2 NDVI analysis ({baseline_start_str} to {monitoring_end_str}), "
                        f"conservative biomass model, 10% adjustment applied. "
                        f"NDVI delta: {delta_ndvi:.4f}, Area: {claim.area_hectares:.2f} ha. "
                        f"AI MRV raw estimate: {ai_mrv_min:.2f}-{ai_mrv_max:.2f} tCO2e.",
        deviation_from_claim_percent=deviation_from_claim,
    )

    # Create verification result
    verification = VerificationResult(
        claim_id=claim.id,
        status=VerificationStatus.COMPLETED,
        outcome=VerificationOutcome.APPROVED,
        verified_impact=verified_impact,
        overall_confidence=confidence_level,
        summary=f"Real satellite-based verification completed. NDVI delta: {delta_ndvi:.4f}, "
                f"Estimated CO₂e: {ai_mrv_min:.2f}-{ai_mrv_max:.2f} tonnes. "
                f"Claim approved with conservative adjustment.",
        completed_at=datetime.utcnow(),
        verifier_id="system-satellite-mrv",
    )
    
    print(f"[MRV_RESULT] Verification result created: {verification.id}, Outcome: APPROVED, Confidence: {confidence_level.value}")

    # Store verification
    verifications_db[verification.id] = verification
    _save_verifications()
    
    # Persist claim update
    from backend.app.services.claim_service import _save_claims
    _save_claims()

    # Update claim status to AI_VERIFIED (analysis completed, positive impact detected)
    # Approval happens only via governance (authority + community review)
    # REAL MRV: Status was set to AI_ANALYSIS_IN_PROGRESS before this function was called
    claim.status = ClaimStatus.AI_VERIFIED
    claim.verification_id = verification.id
    claim.updated_at = datetime.utcnow()

    # Generate and save MRV preview image
    preview_image_path = _generate_and_save_mrv_preview(
        claim,
        ee_geometry,
        monitoring_start_str,
        monitoring_end_str,
    )
    
    # Create immutable SYSTEM_AI evidence record for AI MRV
    # REAL MRV: Pass actual computed NDVI values and date ranges
    _create_mrv_evidence(
        claim, 
        verification, 
        ai_mrv_min, 
        ai_mrv_max,
        baseline_start_str,
        baseline_end_str,
        monitoring_start_str,
        monitoring_end_str,
        baseline_ndvi,
        monitoring_ndvi,
        delta_ndvi,
        preview_image_path,
    )
    
    # Perform AI claim consistency evaluation
    # REAL MRV: Use actual computed AI estimates and NDVI delta
    # This compares INDEPENDENT AI-derived MRV results against claimant-declared estimates
    # The evaluation uses deterministic, rule-based logic (no ML models)
    
    # VALIDATION: Ensure all inputs are valid before consistency evaluation
    # Prevent NaN values from propagating to confidence calculation
    if not isinstance(delta_ndvi, (int, float)) or isnan(delta_ndvi):
        raise ValueError(f"Invalid NDVI delta for claim {claim.id}: {delta_ndvi}")
    if not isinstance(claim.area_hectares, (int, float)) or claim.area_hectares <= 0:
        raise ValueError(f"Invalid area_hectares for claim {claim.id}: {claim.area_hectares}")
    if not isinstance(ai_mrv_min, (int, float)) or not isinstance(ai_mrv_max, (int, float)):
        raise ValueError(f"Invalid CO₂e estimates for claim {claim.id}: min={ai_mrv_min}, max={ai_mrv_max}")
    if isnan(ai_mrv_min) or isnan(ai_mrv_max):
        raise ValueError(f"NaN CO₂e estimates for claim {claim.id}: min={ai_mrv_min}, max={ai_mrv_max}")
    
    # AI CONSISTENCY EVALUATION: Compare AI MRV estimate against claimant's declared estimate
    # This uses raw AI MRV values (can be negative) for scientific accuracy
    # The consistency verdict helps authority reviewers understand if AI supports or contradicts the claim
    consistency_result = ai_consistency_service.evaluate_claim_consistency(
        claim=claim,
        ai_estimate_min=ai_mrv_min,  # Raw AI MRV value (can be negative)
        ai_estimate_max=ai_mrv_max,  # Raw AI MRV value (can be negative)
        ndvi_delta=delta_ndvi,
        area_hectares=claim.area_hectares,
    )
    
    # VALIDATION: Ensure confidence score is valid (not NaN)
    if not isinstance(consistency_result.confidence_score, (int, float)) or isnan(consistency_result.confidence_score):
        raise ValueError(f"Invalid confidence_score for claim {claim.id}: {consistency_result.confidence_score}")
    
    # Ensure confidence score is in valid range [0, 1]
    confidence_score = max(0.0, min(1.0, consistency_result.confidence_score))
    if confidence_score != consistency_result.confidence_score:
        print(f"[MRV WARNING] Confidence score {consistency_result.confidence_score} clamped to {confidence_score}")
        consistency_result.confidence_score = confidence_score
    
    print(f"[MRV] Consistency verdict: {consistency_result.verdict.value}, "
          f"Confidence score: {consistency_result.confidence_score:.3f}, "
          f"Deviation: {consistency_result.deviation_percent:+.1f}%, "
          f"AI MRV raw estimate: {ai_mrv_min:.2f}-{ai_mrv_max:.2f} tCO2e")
    
    # Create SYSTEM_AI evidence record for consistency verdict
    # This provides an auditable record of how AI estimate compares to claim
    _create_consistency_evidence(claim, consistency_result)
    
    print(f"[MRV] ========================================")
    print(f"[MRV] VERIFICATION COMPLETED SUCCESSFULLY")
    print(f"[MRV]   Claim ID: {claim.id}")
    print(f"[MRV]   Final Status: {claim.status.value}")
    print(f"[MRV]   Verification Outcome: {verification.outcome.value}")
    print(f"[MRV]   Verification ID: {verification.id}")
    print(f"[MRV]   Confidence: {verification.overall_confidence.value}")
    print(f"[MRV]   Evidence records created: 2 (MRV + Consistency)")
    print(f"[MRV] ========================================")

    return verification


def _generate_and_save_mrv_preview(
    claim: Claim,
    geometry: ee.Geometry,
    monitoring_start: str,
    monitoring_end: str,
) -> Optional[str]:
    """
    Generate and save a Sentinel-2 RGB preview image for MRV evidence.
    
    This creates a visual representation of the satellite imagery used for verification.
    The image is saved to /uploads/claims/{claim_id}/sentinel2_preview.png
    
    Args:
        claim: The claim being verified.
        geometry: Earth Engine geometry for the claim area.
        monitoring_start: Monitoring period start date (YYYY-MM-DD).
        monitoring_end: Monitoring period end date (YYYY-MM-DD).
    
    Returns:
        Public file path (e.g., "/uploads/claims/{claim_id}/sentinel2_preview.png") or None if generation fails.
    """
    try:
        # Get Sentinel-2 RGB preview for monitoring period
        img = get_sentinel2_rgb_preview(
            geometry=geometry,
            start_date=monitoring_start,
            end_date=monitoring_end,
        )
        
        # Prepare RGB visualization
        rgb = img.visualize(
            bands=["B4", "B3", "B2"],  # Red, Green, Blue
            min=0,
            max=3000,
        )
        
        # Request a thumbnail URL from Earth Engine
        thumb_url = rgb.getThumbURL({
            "region": geometry,
            "dimensions": 512,
            "format": "png",
        })
        
        # Download the image
        response = requests.get(thumb_url, timeout=30)
        response.raise_for_status()
        
        # Save to uploads directory (use same structure as main.py)
        DATA_DIR = Path("data")
        UPLOAD_DIR = DATA_DIR / "uploads"
        claim_dir = UPLOAD_DIR / "claims" / str(claim.id)
        claim_dir.mkdir(parents=True, exist_ok=True)
        
        preview_filename = "sentinel2_preview.png"
        preview_path = claim_dir / preview_filename
        preview_path.write_bytes(response.content)
        
        # Return public path (relative to /uploads mount point)
        public_path = f"/uploads/claims/{claim.id}/{preview_filename}"
        print(f"[MRV] Preview image saved: {preview_path}, public path: {public_path}")
        
        return public_path
        
    except Exception as e:
        # Log error but don't fail verification if image generation fails
        print(f"[MRV WARNING] Failed to generate preview image for claim {claim.id}: {str(e)}")
        return None


def _create_mrv_evidence(
    claim: Claim,
    verification: VerificationResult,
    min_co2e: float,
    max_co2e: float,
    baseline_start: str,
    baseline_end: str,
    monitoring_start: str,
    monitoring_end: str,
    baseline_ndvi: float,
    monitoring_ndvi: float,
    delta_ndvi: float,
    preview_image_path: Optional[str] = None,
    failure_reason: Optional[str] = None,
) -> None:
    """
    Create an immutable evidence record for AI MRV verification.
    
    REAL MRV: This function now uses actual computed NDVI values and date ranges
    from satellite analysis, not mocked values.
    
    This function is called automatically when verification completes.
    The evidence record provides an auditable, tamper-evident record
    of the satellite-based analysis.
    
    Args:
        claim: The verified claim.
        verification: The verification result.
        min_co2e: Minimum CO₂e estimate (from real NDVI computation).
        max_co2e: Maximum CO₂e estimate (from real NDVI computation).
        baseline_start: Baseline period start date (YYYY-MM-DD).
        baseline_end: Baseline period end date (YYYY-MM-DD).
        monitoring_start: Monitoring period start date (YYYY-MM-DD).
        monitoring_end: Monitoring period end date (YYYY-MM-DD).
        baseline_ndvi: Real baseline NDVI from Sentinel-2.
        monitoring_ndvi: Real monitoring NDVI from Sentinel-2.
        delta_ndvi: Real NDVI delta (monitoring - baseline).
    """
    # Map confidence level to string
    confidence_map = {
        ConfidenceLevel.LOW: "low",
        ConfidenceLevel.MEDIUM: "medium",
        ConfidenceLevel.HIGH: "high",
    }
    confidence = confidence_map.get(verification.overall_confidence, "medium")
    
    # REAL MRV: Create evidence with actual computed values
    # Always create evidence even on failure - critical for audit trail
    # Use preview image path if available, otherwise use GEE reference
    data_ref = preview_image_path if preview_image_path else f"gee://sentinel2/ndvi/claim-{claim.id}"
    
    evidence_service.create_ai_mrv_evidence(
        claim_id=claim.id,
        baseline_start=baseline_start,
        baseline_end=baseline_end,
        monitoring_start=monitoring_start,
        monitoring_end=monitoring_end,
        baseline_ndvi=baseline_ndvi,
        monitoring_ndvi=monitoring_ndvi,
        delta_ndvi=delta_ndvi,
        min_co2e=min_co2e,
        max_co2e=max_co2e,
        confidence=confidence,
        data_ref=data_ref,
        failure_reason=failure_reason,
    )
    
    print(f"[MRV] SYSTEM_AI evidence created for claim {claim.id} with real NDVI values" + 
          (f" (failure: {failure_reason})" if failure_reason else "") +
          (f" (preview: {preview_image_path})" if preview_image_path else ""))


def _create_consistency_evidence(
    claim: Claim,
    consistency_result: AIConsistencyResult,
) -> None:
    """
    Create an immutable SYSTEM_AI evidence record for the AI claim consistency verdict.
    
    This function is called automatically after consistency evaluation.
    The evidence record provides an auditable, tamper-evident record
    of how the AI-derived MRV estimate compares to the claimant's declared estimate.
    
    Args:
        claim: The claim being evaluated.
        consistency_result: The AI consistency evaluation result.
    """
    from backend.app.models.evidence import EvidenceSubmission, EvidenceType
    
    # Format verdict for description
    verdict_map = {
        "strongly_supports": "STRONGLY_SUPPORTS",
        "partially_supports": "PARTIALLY_SUPPORTS",
        "contradicts": "CONTRADICTS",
    }
    verdict_str = verdict_map.get(consistency_result.verdict.value, consistency_result.verdict.value.upper())
    
    # Build description with all required information
    description = (
        f"AI Claim Consistency Verdict: {verdict_str}. "
        f"Claimed range: {consistency_result.claimed_min_co2e:.1f}-{consistency_result.claimed_max_co2e:.1f} tCO2e. "
        f"AI estimated range: {consistency_result.estimated_min_co2e:.1f}-{consistency_result.estimated_max_co2e:.1f} tCO2e. "
        f"Deviation: {consistency_result.deviation_percent:+.1f}%. "
        f"Confidence score: {consistency_result.confidence_score:.2f}. "
        f"Explanation: {consistency_result.explanation}"
    )
    
    # Map confidence score to weight (for evidence system)
    if consistency_result.confidence_score >= 0.7:
        confidence_weight = 0.85
    elif consistency_result.confidence_score >= 0.4:
        confidence_weight = 0.65
    else:
        confidence_weight = 0.45
    
    submission = EvidenceSubmission(
        claim_id=claim.id,
        type=EvidenceType.SYSTEM_AI,
        source="system",
        title="AI Claim Consistency Verdict",
        description=description,
        data_ref=f"ai-consistency://claim-{claim.id}",
        confidence_weight=confidence_weight,
    )
    
    evidence_service.create_evidence(submission)


def get_verification_by_id(verification_id: UUID) -> Optional[VerificationResult]:
    """
    Retrieve a VerificationResult by its unique ID.

    Args:
        verification_id: The UUID of the verification to retrieve.

    Returns:
        The VerificationResult object if found, None otherwise.
    """
    return verifications_db.get(verification_id)
