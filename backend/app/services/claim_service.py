"""
CarbonChain MVP - Claim Service

Service layer for claim creation and retrieval operations.
Uses JSON file persistence for MVP demonstration purposes.
"""

from pathlib import Path
from typing import Optional
from uuid import UUID

from pyproj import Transformer
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform

from backend.app.models.claim import (
    Claim,
    ClaimSubmission,
    ClaimType,
    GeoLocation,
    GeometrySource,
    GeometryType,
)
from backend.app.storage import atomic_write_json, read_json, uuid_to_str, str_to_uuid

# -----------------------------------------------------------------------------
# JSON file storage
# -----------------------------------------------------------------------------
STORAGE_DIR = Path("backend/app/storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
CLAIMS_FILE = STORAGE_DIR / "claims.json"

claims_db: dict[UUID, Claim] = {}


def _load_claims() -> None:
    """Load claims from disk on startup."""
    if not CLAIMS_FILE.exists():
        print(f"[CLAIM_SERVICE] {CLAIMS_FILE} does not exist. Starting with empty database.")
        return
    
    try:
        loaded_data = read_json(CLAIMS_FILE, default={})
        
        # Convert dict of dicts to dict of Claim objects
        claims_db.clear()
        for claim_id_str, claim_data in loaded_data.items():
            try:
                claim_id = UUID(claim_id_str)
                # Convert nested UUID strings to UUID objects
                claim_data = str_to_uuid(claim_data, ['id', 'verification_id'])
                # Reconstruct Claim object
                claim = Claim(**claim_data)
                claims_db[claim_id] = claim
            except Exception as e:
                print(f"[CLAIM_SERVICE WARNING] Failed to load claim {claim_id_str}: {e}")
        
        print(f"[CLAIM_SERVICE] Loaded {len(claims_db)} claims from {CLAIMS_FILE}")
    except Exception as e:
        print(f"[CLAIM_SERVICE ERROR] Failed to load claims: {e}")


def _save_claims() -> None:
    """Save claims to disk."""
    try:
        # Convert UUID keys to strings and UUID values in data to strings
        serializable_data = {}
        for claim_id, claim in claims_db.items():
            claim_dict = claim.model_dump()
            serializable_data[str(claim_id)] = uuid_to_str(claim_dict)
        
        atomic_write_json(CLAIMS_FILE, serializable_data)
    except Exception as e:
        print(f"[CLAIM_SERVICE ERROR] Failed to save claims: {e}")


# Load on import
_load_claims()


def _radius_km_for_claim_type(claim_type: ClaimType) -> float:
    """Deterministic buffer radius (km) based on claim type grouping."""
    forest_types = {
        ClaimType.MANGROVE_RESTORATION,
        ClaimType.REFORESTATION,
        ClaimType.WETLAND_RESTORATION,
        ClaimType.AVOIDED_DEFORESTATION,
    }
    energy_types = {ClaimType.SOLAR_INSTALLATION, ClaimType.WIND_INSTALLATION}

    if claim_type in forest_types:
        return 2.0
    if claim_type in energy_types:
        return 1.0
    # Fallback (agriculture/other) gets a slightly larger buffer
    return 3.0


def _generate_buffer_geojson(location: GeoLocation, claim_type: ClaimType) -> dict:
    """Create a buffered polygon (GeoJSON) around a point using Web Mercator for meters."""
    radius_m = _radius_km_for_claim_type(claim_type) * 1000
    # Transform to projected CRS for accurate meter-based buffer
    to_mercator = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
    to_wgs84 = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True).transform

    point_wgs84 = Point(location.longitude, location.latitude)
    point_mercator = transform(to_mercator, point_wgs84)
    buffered_mercator = point_mercator.buffer(radius_m)
    buffered_wgs84 = transform(to_wgs84, buffered_mercator)
    return mapping(buffered_wgs84)


def _validate_polygon_geojson(geometry_geojson: dict) -> dict:
    """Validate GeoJSON polygon/multipolygon integrity."""
    geom = shape(geometry_geojson)
    if geom.geom_type not in {"Polygon", "MultiPolygon"}:
        raise ValueError("Provided geometry must be a Polygon or MultiPolygon")
    if geom.is_empty or not geom.is_valid:
        raise ValueError("Provided geometry is invalid or empty")
    if geom.area == 0:
        raise ValueError("Provided geometry must have non-zero area")
    return mapping(geom)


def _ensure_location_from_geometry(
    geometry_geojson: dict, fallback_location: Optional[GeoLocation]
) -> GeoLocation:
    """
    Ensure we have a point location for downstream consumers.

    Uses centroid of polygon when explicit point is absent.
    """
    if fallback_location:
        return fallback_location
    geom = shape(geometry_geojson)
    centroid = geom.centroid
    return GeoLocation(latitude=centroid.y, longitude=centroid.x, location_name=None)


def create_claim(submission: ClaimSubmission) -> Claim:
    """
    Create and store a new Claim from a ClaimSubmission.

    Applies deterministic geometry handling:
    - If a polygon is provided, validate it and mark as USER_DRAWN.
    - If only a point is provided, generate a BUFFER polygon using claim-type rules.
    - Geometry is required before AI MRV; enforcement happens in the verification step.

    CRITICAL: Normalizes null/None values from frontend before validation.
    Frontend sends JSON null, which Pydantic converts to None, but we ensure
    empty objects and null values are properly handled.

    Args:
        submission: The claim submission data from the claimant.

    Returns:
        The created Claim object with system-generated fields populated.
    """
    # STEP 4: Normalize nulls safely (no guessing)
    # Explicitly normalize frontend nulls before any processing
    if submission.geometry_geojson == {}:
        submission.geometry_geojson = None
    
    if submission.area_hectares == "":
        submission.area_hectares = None
    
    if submission.submitter_contact == "":
        submission.submitter_contact = None
    
    submission_data = submission.model_dump()

    # NORMALIZE INPUTS: Convert null/empty values to None before validation
    # Frontend may send geometry_geojson: null (JSON null) which Pydantic converts to None
    # But we also need to handle empty dicts {} which should be treated as None
    location: Optional[GeoLocation] = submission.location
    geometry_geojson = submission.geometry_geojson
    
    # Normalize: Convert empty dict {} to None, ensure null is None
    if geometry_geojson is not None:
        if isinstance(geometry_geojson, dict):
            # Check if it's an empty dict or invalid structure
            if not geometry_geojson or geometry_geojson.get("type") is None:
                geometry_geojson = None
        elif not isinstance(geometry_geojson, dict):
            # Not a dict at all - treat as None
            geometry_geojson = None

    # VALIDATION: Ensure at least one geometry input exists
    if geometry_geojson is None and location is None:
        raise ValueError("Either location (lat/lng) or geometry_geojson must be provided")

    if geometry_geojson is not None:
        validated_geojson = _validate_polygon_geojson(geometry_geojson)
        submission_data["geometry_geojson"] = validated_geojson
        submission_data["geometry_type"] = GeometryType.POLYGON
        submission_data["geometry_source"] = GeometrySource.USER_DRAWN
        submission_data["location"] = _ensure_location_from_geometry(
            validated_geojson, location
        )
    else:
        # Auto-generate buffer polygon from point
        assert location is not None  # for type checker
        buffer_geojson = _generate_buffer_geojson(location, submission.claim_type)
        submission_data["geometry_geojson"] = buffer_geojson
        submission_data["geometry_type"] = GeometryType.BUFFER
        submission_data["geometry_source"] = GeometrySource.USER_POINT
        submission_data["location"] = location

    claim = Claim(**submission_data)
    claims_db[claim.id] = claim
    _save_claims()
    return claim


def get_claim_by_id(claim_id: UUID) -> Optional[Claim]:
    """
    Retrieve a Claim by its unique ID.

    Args:
        claim_id: The UUID of the claim to retrieve.

    Returns:
        The Claim object if found, None otherwise.
    """
    return claims_db.get(claim_id)


def update_claim_geometry_authority(claim_id: UUID, geometry_geojson: dict) -> Claim:
    """
    Replace claim geometry as an authority-defined polygon.

    Geometry is validated and stored as POLYGON with AUTHORITY_DEFINED source.
    Location is set to centroid to preserve point access for downstream consumers.
    """
    claim = claims_db.get(claim_id)
    if claim is None:
        raise ValueError(f"Claim with id {claim_id} not found")

    validated = _validate_polygon_geojson(geometry_geojson)
    centroid_loc = _ensure_location_from_geometry(validated, claim.location)

    claim.geometry_geojson = validated
    claim.geometry_type = GeometryType.POLYGON
    claim.geometry_source = GeometrySource.AUTHORITY_DEFINED
    claim.location = centroid_loc
    _save_claims()
    return claim
