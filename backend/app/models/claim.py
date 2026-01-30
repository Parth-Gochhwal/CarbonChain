"""
CarbonChain - Climate Action Claim Models

This module defines the data contracts for climate action claims.
A claim represents a self-reported climate-positive action that needs verification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from backend.app.models.evidence import EvidenceType


class ClaimStatus(str, Enum):
    """
    Lifecycle status of a climate action claim.

    Valid state transitions (governance flow):
        SUBMITTED → AI_ANALYZED → AUTHORITY_REVIEWED → COMMUNITY_REVIEWED → APPROVED → MINTED

    Governance stages:
        - AI_ANALYZED: AI MRV analysis complete, awaiting authority review (analysis completed, not approved)
        - AUTHORITY_REVIEWED: Government/regulator approved, awaiting community review
        - COMMUNITY_REVIEWED: Public transparency check passed, ready for final approval

    Legacy status (kept for backwards compatibility):
        - VERIFIED: Legacy status (maps to AI_ANALYZED in new flow)
        - AI_VERIFIED: Legacy status (maps to AI_ANALYZED in new flow)

    Special case:
        - REJECTED can occur at AUTHORITY_REVIEWED or COMMUNITY_REVIEWED stages

    Note: State transition enforcement is implemented in review_service.py
    """

    SUBMITTED = "submitted"  # Initial state: claim received, awaiting AI analysis
    AI_ANALYSIS_PENDING = "ai_analysis_pending"  # AI MRV computation queued (async background task)
    AI_ANALYSIS_IN_PROGRESS = "ai_analysis_in_progress"  # AI MRV computation is running (async)
    VERIFIED = (
        "verified"  # Legacy: AI analysis complete (use AI_VERIFIED for new claims)
    )
    AI_VERIFIED = "ai_verified"  # AI MRV analysis complete with positive carbon impact, awaiting authority review
    AI_REJECTED = "ai_rejected"  # AI MRV analysis complete but no positive carbon impact detected (degradation or zero gain)
    AI_ANALYZED = "ai_analyzed"  # Alias for AI_VERIFIED (kept for backwards compatibility)
    AUTHORITY_REVIEWED = (
        "authority_reviewed"  # Authority approved, awaiting community review
    )
    COMMUNITY_REVIEWED = (
        "community_reviewed"  # Community approved, ready for final approval
    )
    APPROVED = "approved"  # Approved for carbon credit minting
    REJECTED = "rejected"  # Claim rejected (at any governance stage)
    MINTED = "minted"  # Carbon credits have been issued (simulated)


class ClaimType(str, Enum):
    """
    Categories of climate-positive actions supported by CarbonChain MVP.

    MVP assumption: We support a limited set of well-understood action types.
    Each type has different verification requirements and carbon calculation methods.
    """

    MANGROVE_RESTORATION = "mangrove_restoration"  # Planting/restoring mangrove forests
    SOLAR_INSTALLATION = "solar_installation"  # Solar panel/park deployment
    WIND_INSTALLATION = "wind_installation"  # Wind turbine deployment
    REFORESTATION = "reforestation"  # General tree planting projects
    WETLAND_RESTORATION = "wetland_restoration"  # Wetland/marsh restoration
    AVOIDED_DEFORESTATION = "avoided_deforestation"  # Protecting existing forests
    OTHER = "other"  # Catch-all for MVP flexibility


class GeoLocation(BaseModel):
    """
    Geographic coordinates for a climate action site.

    MVP assumption: Simple lat/lng is sufficient.
    Production would need polygons, boundaries, and area calculations.
    
    API-BOUNDARY-SAFE: This model accepts latitude/longitude from frontend
    without strict validation at the boundary. Validation happens in services.
    """

    latitude: float = Field(
        ..., description="Latitude in decimal degrees (-90 to 90)"
    )
    longitude: float = Field(
        ..., description="Longitude in decimal degrees (-180 to 180)"
    )
    # Optional human-readable location for display purposes
    location_name: Optional[str] = Field(
        default=None,
        description="Human-readable location name (e.g., 'Sundarbans, Bangladesh')",
    )
    
    class Config:
        """Pydantic configuration for GeoLocation."""
        extra = "ignore"
        populate_by_name = True


class GeometryType(str, Enum):
    """Geometry representation for the claim site."""

    POINT = "point"
    BUFFER = "buffer"
    POLYGON = "polygon"


class GeometrySource(str, Enum):
    """
    Who/what defined the geometry.

    USER_POINT: User provided a point; system generated buffer
    USER_DRAWN: User provided a polygon directly
    AUTHORITY_DEFINED: Authority replaced/confirmed geometry
    """

    USER_POINT = "user_point"
    USER_DRAWN = "user_drawn"
    AUTHORITY_DEFINED = "authority_defined"


class CarbonImpactEstimate(BaseModel):
    """
    Self-reported carbon impact estimate with uncertainty range.

    CRITICAL: Carbon impact is expressed as a RANGE, not a single value.
    This acknowledges inherent uncertainty in carbon calculations.
    All values are in metric tons of CO2 equivalent (tCO2e).
    
    API-BOUNDARY-SAFE: Validation constraints are relaxed at the boundary.
    Business logic validation happens in claim_service.
    """

    min_tonnes_co2e: float = Field(
        ..., description="Lower bound estimate of carbon impact in tonnes CO2e"
    )
    max_tonnes_co2e: float = Field(
        ..., description="Upper bound estimate of carbon impact in tonnes CO2e"
    )
    # MVP assumption: Claimant provides their own estimate methodology
    estimation_methodology: Optional[str] = Field(
        default=None, description="Brief description of how the estimate was calculated"
    )
    # Time period over which impact is measured
    time_horizon_years: int = Field(
        default=1,
        description="Number of years over which carbon impact is projected",
    )
    
    class Config:
        """Pydantic configuration for CarbonImpactEstimate."""
        extra = "ignore"
        populate_by_name = True

    @model_validator(mode="after")
    def validate_carbon_range(self) -> "CarbonImpactEstimate":
        """
        Ensure min_tonnes_co2e does not exceed max_tonnes_co2e.
        
        NOTE: This validation is kept for data integrity, but ge=0 constraints
        are removed to allow frontend to send values that will be validated
        in claim_service with better error messages.
        """
        if self.min_tonnes_co2e > self.max_tonnes_co2e:
            raise ValueError(
                f"min_tonnes_co2e ({self.min_tonnes_co2e}) cannot be greater than "
                f"max_tonnes_co2e ({self.max_tonnes_co2e})"
            )
        return self


class EvidenceMetadata(BaseModel):
    """
    Metadata about evidence supporting a claim.

    MVP assumption: We store metadata only, not actual files.
    File handling would be added in production with Azure Blob Storage.
    """

    evidence_type: EvidenceType = Field(
        ...,
        description="Type of evidence (satellite_image, ground_photo, sensor_data, report, other)",
    )
    description: str = Field(
        ..., description="Human-readable description of what this evidence shows"
    )
    # Reference to where evidence is stored (URL, file path, or placeholder)
    source_reference: Optional[str] = Field(
        default=None,
        description="Reference to evidence source (URL or identifier). Actual file handling TBD.",
    )
    capture_date: Optional[datetime] = Field(
        default=None, description="When the evidence was captured/created"
    )
    # Flag for transparency about evidence quality
    is_verified_source: bool = Field(
        default=False,
        description="Whether this evidence comes from a trusted/verified source",
    )


class ClaimSubmission(BaseModel):
    """
    Input model for submitting a new climate action claim.

    API-BOUNDARY-SAFE: This model is designed to accept frontend payloads
    with maximum tolerance. It ignores unknown fields and allows optional
    geometry/area fields. Validation is deferred to claim_service.create_claim().

    This is what a claimant provides when registering their action.
    Does not include system-generated fields like ID or status.
    """

    claim_type: ClaimType = Field(
        ..., description="Category of climate action being claimed"
    )
    title: str = Field(
        ...,
        description="Short descriptive title for the claim",
    )
    description: str = Field(
        ...,
        description="Detailed description of the climate action taken",
    )
    # Location can be provided as GeoLocation object OR as lat/lng dict
    # Frontend may send: { latitude: float, longitude: float }
    location: Optional[GeoLocation] = Field(
        default=None,
        description="Geographic location of the climate action (point). Optional when a polygon is provided.",
    )
    geometry_geojson: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional GeoJSON polygon for the claim boundary.",
    )
    geometry_type: Optional[GeometryType] = Field(
        default=None,
        description="System-determined geometry type (point, buffer, polygon).",
    )
    geometry_source: Optional[GeometrySource] = Field(
        default=None,
        description="Who/what defined the geometry (user point, user drawn, authority).",
    )
    # Area is optional because some actions (like solar) may use capacity instead
    area_hectares: Optional[float] = Field(
        default=None,
        description="Area of the project in hectares (if applicable)",
    )
    carbon_impact_estimate: CarbonImpactEstimate = Field(
        ..., description="Claimant's estimate of carbon impact with uncertainty range"
    )
    evidence: list[EvidenceMetadata] = Field(
        default_factory=list,
        description="List of evidence metadata supporting this claim",
    )
    # When the climate action started
    action_start_date: datetime = Field(
        ..., description="Date when the climate action began"
    )
    # Optional end date for completed actions
    action_end_date: Optional[datetime] = Field(
        default=None,
        description="Date when the climate action was completed (if applicable)",
    )
    # Transparency: claimant-declared assumptions
    stated_assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions the claimant made in their carbon estimate",
    )
    # Transparency: known limitations or missing data
    known_limitations: list[str] = Field(
        default_factory=list, description="Known limitations or gaps in the claim data"
    )
    # Contact info for follow-up (simplified for MVP)
    submitter_name: str = Field(
        ..., description="Name of person or organization submitting the claim"
    )
    submitter_contact: Optional[str] = Field(
        default=None, description="Contact email or identifier for the submitter"
    )

    class Config:
        """Pydantic configuration for API-boundary tolerance."""
        # CRITICAL: Ignore extra fields from frontend (UI flags, temp fields, etc.)
        # This prevents 422 errors when frontend sends additional metadata
        extra = "ignore"
        # Allow population by field name for flexibility
        populate_by_name = True

    @model_validator(mode="before")
    @classmethod
    def normalize_location(cls, data: Any) -> Any:
        """
        Normalize location input to handle frontend sending lat/lng directly.
        
        Frontend may send:
        - location: { latitude: float, longitude: float } (dict)
        - location: GeoLocation object (already correct)
        - location: None (when geometry_geojson is provided)
        
        This converts dict format to GeoLocation if needed.
        """
        if isinstance(data, dict):
            location = data.get("location")
            if location is not None and isinstance(location, dict):
                # Check if it's already a GeoLocation (has latitude/longitude)
                if "latitude" in location and "longitude" in location:
                    # It's already in the correct format, Pydantic will handle it
                    pass
        return data

    @model_validator(mode="after")
    def validate_geometry_inputs(self) -> "ClaimSubmission":
        """
        Ensure at least one geometry input is present.

        Users can provide either a point (location) or a polygon (geometry_geojson).
        NOTE: This validation is deferred - we allow None here and let
        claim_service.create_claim() handle the validation with better error messages.
        """
        # Allow both to be None - claim_service will validate and provide clear errors
        # This prevents 422 errors at the API boundary
        return self


class Claim(ClaimSubmission):
    """
    Complete claim record including system-generated fields.

    Extends ClaimSubmission with ID, status, and timestamps.
    This is the full claim object stored and tracked by the system.
    """

    id: UUID = Field(
        default_factory=uuid4, description="Unique identifier for this claim"
    )
    status: ClaimStatus = Field(
        default=ClaimStatus.SUBMITTED,
        description="Current lifecycle status of the claim",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the claim was submitted",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the claim was last modified",
    )
    # Reference to verification result (if verified)
    verification_id: Optional[UUID] = Field(
        default=None,
        description="ID of the verification record (populated after verification)",
    )

    class Config:
        """Pydantic configuration for the Claim model."""

        # Allow population by field name for flexibility
        populate_by_name = True
        # Generate JSON schema with examples
        json_schema_extra = {
            "example": {
                "claim_type": "mangrove_restoration",
                "title": "Sundarbans Mangrove Restoration Project",
                "description": "Restoration of 50 hectares of mangrove forest in the Sundarbans delta region...",
                "location": {
                    "latitude": 21.9497,
                    "longitude": 89.1833,
                    "location_name": "Sundarbans, Bangladesh",
                },
                "area_hectares": 50.0,
                "carbon_impact_estimate": {
                    "min_tonnes_co2e": 150.0,
                    "max_tonnes_co2e": 300.0,
                    "estimation_methodology": "IPCC Tier 1 defaults for mangrove restoration",
                    "time_horizon_years": 10,
                },
                "action_start_date": "2025-01-15T00:00:00Z",
                "submitter_name": "Green Delta Foundation",
            }
        }
"""
CarbonChain - Climate Action Claim Models

This module defines the data contracts for climate action claims.
A claim represents a self-reported climate-positive action that needs verification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from backend.app.models.evidence import EvidenceType


class ClaimStatus(str, Enum):
    """
    Lifecycle status of a climate action claim.

    Valid state transitions (governance flow):
        SUBMITTED → AI_ANALYZED → AUTHORITY_REVIEWED → COMMUNITY_REVIEWED → APPROVED → MINTED

    Governance stages:
        - AI_ANALYZED: AI MRV analysis complete, awaiting authority review (analysis completed, not approved)
        - AUTHORITY_REVIEWED: Government/regulator approved, awaiting community review
        - COMMUNITY_REVIEWED: Public transparency check passed, ready for final approval

    Legacy status (kept for backwards compatibility):
        - VERIFIED: Legacy status (maps to AI_ANALYZED in new flow)
        - AI_VERIFIED: Legacy status (maps to AI_ANALYZED in new flow)

    Special case:
        - REJECTED can occur at AUTHORITY_REVIEWED or COMMUNITY_REVIEWED stages

    Note: State transition enforcement is implemented in review_service.py
    """

    SUBMITTED = "submitted"  # Initial state: claim received, awaiting AI analysis
    AI_ANALYSIS_PENDING = "ai_analysis_pending"  # AI MRV computation queued (async background task)
    AI_ANALYSIS_IN_PROGRESS = "ai_analysis_in_progress"  # AI MRV computation is running (async)
    VERIFIED = (
        "verified"  # Legacy: AI analysis complete (use AI_VERIFIED for new claims)
    )
    AI_VERIFIED = "ai_verified"  # AI MRV analysis complete with positive carbon impact, awaiting authority review
    AI_REJECTED = "ai_rejected"  # AI MRV analysis complete but no positive carbon impact detected (degradation or zero gain)
    AI_ANALYZED = "ai_analyzed"  # Alias for AI_VERIFIED (kept for backwards compatibility)
    AUTHORITY_REVIEWED = (
        "authority_reviewed"  # Authority approved, awaiting community review
    )
    COMMUNITY_REVIEWED = (
        "community_reviewed"  # Community approved, ready for final approval
    )
    APPROVED = "approved"  # Approved for carbon credit minting
    REJECTED = "rejected"  # Claim rejected (at any governance stage)
    MINTED = "minted"  # Carbon credits have been issued (simulated)


class ClaimType(str, Enum):
    """
    Categories of climate-positive actions supported by CarbonChain MVP.

    MVP assumption: We support a limited set of well-understood action types.
    Each type has different verification requirements and carbon calculation methods.
    """

    MANGROVE_RESTORATION = "mangrove_restoration"  # Planting/restoring mangrove forests
    SOLAR_INSTALLATION = "solar_installation"  # Solar panel/park deployment
    WIND_INSTALLATION = "wind_installation"  # Wind turbine deployment
    REFORESTATION = "reforestation"  # General tree planting projects
    WETLAND_RESTORATION = "wetland_restoration"  # Wetland/marsh restoration
    AVOIDED_DEFORESTATION = "avoided_deforestation"  # Protecting existing forests
    OTHER = "other"  # Catch-all for MVP flexibility


class GeoLocation(BaseModel):
    """
    Geographic coordinates for a climate action site.

    MVP assumption: Simple lat/lng is sufficient.
    Production would need polygons, boundaries, and area calculations.
    
    API-BOUNDARY-SAFE: This model accepts latitude/longitude from frontend
    without strict validation at the boundary. Validation happens in services.
    """

    latitude: float = Field(
        ..., description="Latitude in decimal degrees (-90 to 90)"
    )
    longitude: float = Field(
        ..., description="Longitude in decimal degrees (-180 to 180)"
    )
    # Optional human-readable location for display purposes
    location_name: Optional[str] = Field(
        default=None,
        description="Human-readable location name (e.g., 'Sundarbans, Bangladesh')",
    )
    
    class Config:
        """Pydantic configuration for GeoLocation."""
        extra = "ignore"
        populate_by_name = True


class GeometryType(str, Enum):
    """Geometry representation for the claim site."""

    POINT = "point"
    BUFFER = "buffer"
    POLYGON = "polygon"


class GeometrySource(str, Enum):
    """
    Who/what defined the geometry.

    USER_POINT: User provided a point; system generated buffer
    USER_DRAWN: User provided a polygon directly
    AUTHORITY_DEFINED: Authority replaced/confirmed geometry
    """

    USER_POINT = "user_point"
    USER_DRAWN = "user_drawn"
    AUTHORITY_DEFINED = "authority_defined"


class CarbonImpactEstimate(BaseModel):
    """
    Self-reported carbon impact estimate with uncertainty range.

    CRITICAL: Carbon impact is expressed as a RANGE, not a single value.
    This acknowledges inherent uncertainty in carbon calculations.
    All values are in metric tons of CO2 equivalent (tCO2e).
    
    API-BOUNDARY-SAFE: Validation constraints are relaxed at the boundary.
    Business logic validation happens in claim_service.
    """

    min_tonnes_co2e: float = Field(
        ..., description="Lower bound estimate of carbon impact in tonnes CO2e"
    )
    max_tonnes_co2e: float = Field(
        ..., description="Upper bound estimate of carbon impact in tonnes CO2e"
    )
    # MVP assumption: Claimant provides their own estimate methodology
    estimation_methodology: Optional[str] = Field(
        default=None, description="Brief description of how the estimate was calculated"
    )
    # Time period over which impact is measured
    time_horizon_years: int = Field(
        default=1,
        description="Number of years over which carbon impact is projected",
    )
    
    class Config:
        """Pydantic configuration for CarbonImpactEstimate."""
        extra = "ignore"
        populate_by_name = True

    @model_validator(mode="after")
    def validate_carbon_range(self) -> "CarbonImpactEstimate":
        """
        Ensure min_tonnes_co2e does not exceed max_tonnes_co2e.
        
        NOTE: This validation is kept for data integrity, but ge=0 constraints
        are removed to allow frontend to send values that will be validated
        in claim_service with better error messages.
        """
        if self.min_tonnes_co2e > self.max_tonnes_co2e:
            raise ValueError(
                f"min_tonnes_co2e ({self.min_tonnes_co2e}) cannot be greater than "
                f"max_tonnes_co2e ({self.max_tonnes_co2e})"
            )
        return self


class EvidenceMetadata(BaseModel):
    """
    Metadata about evidence supporting a claim.

    MVP assumption: We store metadata only, not actual files.
    File handling would be added in production with Azure Blob Storage.
    """

    evidence_type: EvidenceType = Field(
        ...,
        description="Type of evidence (satellite_image, ground_photo, sensor_data, report, other)",
    )
    description: str = Field(
        ..., description="Human-readable description of what this evidence shows"
    )
    # Reference to where evidence is stored (URL, file path, or placeholder)
    source_reference: Optional[str] = Field(
        default=None,
        description="Reference to evidence source (URL or identifier). Actual file handling TBD.",
    )
    capture_date: Optional[datetime] = Field(
        default=None, description="When the evidence was captured/created"
    )
    # Flag for transparency about evidence quality
    is_verified_source: bool = Field(
        default=False,
        description="Whether this evidence comes from a trusted/verified source",
    )


class ClaimSubmission(BaseModel):
    """
    Input model for submitting a new climate action claim.

    API-BOUNDARY-SAFE: This model is designed to accept frontend payloads
    with maximum tolerance. It ignores unknown fields and allows optional
    geometry/area fields. Validation is deferred to claim_service.create_claim().

    This is what a claimant provides when registering their action.
    Does not include system-generated fields like ID or status.
    """

    claim_type: ClaimType = Field(
        ..., description="Category of climate action being claimed"
    )
    title: str = Field(
        ...,
        description="Short descriptive title for the claim",
    )
    description: str = Field(
        ...,
        description="Detailed description of the climate action taken",
    )
    # Location can be provided as GeoLocation object OR as lat/lng dict
    # Frontend may send: { latitude: float, longitude: float }
    location: Optional[GeoLocation] = Field(
        default=None,
        description="Geographic location of the climate action (point). Optional when a polygon is provided.",
    )
    geometry_geojson: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional GeoJSON polygon for the claim boundary.",
    )
    geometry_type: Optional[GeometryType] = Field(
        default=None,
        description="System-determined geometry type (point, buffer, polygon).",
    )
    geometry_source: Optional[GeometrySource] = Field(
        default=None,
        description="Who/what defined the geometry (user point, user drawn, authority).",
    )
    # Area is optional because some actions (like solar) may use capacity instead
    area_hectares: Optional[float] = Field(
        default=None,
        description="Area of the project in hectares (if applicable)",
    )
    carbon_impact_estimate: CarbonImpactEstimate = Field(
        ..., description="Claimant's estimate of carbon impact with uncertainty range"
    )
    evidence: list[EvidenceMetadata] = Field(
        default_factory=list,
        description="List of evidence metadata supporting this claim",
    )
    # When the climate action started
    action_start_date: datetime = Field(
        ..., description="Date when the climate action began"
    )
    # Optional end date for completed actions
    action_end_date: Optional[datetime] = Field(
        default=None,
        description="Date when the climate action was completed (if applicable)",
    )
    # Transparency: claimant-declared assumptions
    stated_assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions the claimant made in their carbon estimate",
    )
    # Transparency: known limitations or missing data
    known_limitations: list[str] = Field(
        default_factory=list, description="Known limitations or gaps in the claim data"
    )
    # Contact info for follow-up (simplified for MVP)
    submitter_name: str = Field(
        ..., description="Name of person or organization submitting the claim"
    )
    submitter_contact: Optional[str] = Field(
        default=None, description="Contact email or identifier for the submitter"
    )

    class Config:
        """Pydantic configuration for API-boundary tolerance."""
        # CRITICAL: Ignore extra fields from frontend (UI flags, temp fields, etc.)
        # This prevents 422 errors when frontend sends additional metadata
        extra = "ignore"
        # Allow population by field name for flexibility
        populate_by_name = True

    @model_validator(mode="before")
    @classmethod
    def normalize_location(cls, data: Any) -> Any:
        """
        Normalize location input to handle frontend sending lat/lng directly.
        
        Frontend may send:
        - location: { latitude: float, longitude: float } (dict)
        - location: GeoLocation object (already correct)
        - location: None (when geometry_geojson is provided)
        
        This converts dict format to GeoLocation if needed.
        """
        if isinstance(data, dict):
            location = data.get("location")
            if location is not None and isinstance(location, dict):
                # Check if it's already a GeoLocation (has latitude/longitude)
                if "latitude" in location and "longitude" in location:
                    # It's already in the correct format, Pydantic will handle it
                    pass
        return data

    @model_validator(mode="after")
    def validate_geometry_inputs(self) -> "ClaimSubmission":
        """
        Ensure at least one geometry input is present.

        Users can provide either a point (location) or a polygon (geometry_geojson).
        NOTE: This validation is deferred - we allow None here and let
        claim_service.create_claim() handle the validation with better error messages.
        """
        # Allow both to be None - claim_service will validate and provide clear errors
        # This prevents 422 errors at the API boundary
        return self


class Claim(ClaimSubmission):
    """
    Complete claim record including system-generated fields.

    Extends ClaimSubmission with ID, status, and timestamps.
    This is the full claim object stored and tracked by the system.
    """

    id: UUID = Field(
        default_factory=uuid4, description="Unique identifier for this claim"
    )
    status: ClaimStatus = Field(
        default=ClaimStatus.SUBMITTED,
        description="Current lifecycle status of the claim",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the claim was submitted",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when the claim was last modified",
    )
    # Reference to verification result (if verified)
    verification_id: Optional[UUID] = Field(
        default=None,
        description="ID of the verification record (populated after verification)",
    )

    class Config:
        """Pydantic configuration for the Claim model."""

        # Allow population by field name for flexibility
        populate_by_name = True
        # Generate JSON schema with examples
        json_schema_extra = {
            "example": {
                "claim_type": "mangrove_restoration",
                "title": "Sundarbans Mangrove Restoration Project",
                "description": "Restoration of 50 hectares of mangrove forest in the Sundarbans delta region...",
                "location": {
                    "latitude": 21.9497,
                    "longitude": 89.1833,
                    "location_name": "Sundarbans, Bangladesh",
                },
                "area_hectares": 50.0,
                "carbon_impact_estimate": {
                    "min_tonnes_co2e": 150.0,
                    "max_tonnes_co2e": 300.0,
                    "estimation_methodology": "IPCC Tier 1 defaults for mangrove restoration",
                    "time_horizon_years": 10,
                },
                "action_start_date": "2025-01-15T00:00:00Z",
                "submitter_name": "Green Delta Foundation",
            }
        }
