"""
Carbon estimation module for MRV verification.

This module provides conservative CO₂e estimation from NDVI change data.
It is designed for transparency and auditability, not precision claims.

IMPORTANT: This is an MVP estimation model using simplified linear assumptions.
Results should be interpreted as indicative ranges, not exact measurements.
"""

# Biomass conversion factors (tonnes dry biomass per hectare per unit NDVI change)
_MIN_BIOMASS_FACTOR = 5.0
_MAX_BIOMASS_FACTOR = 15.0

# Carbon content of dry biomass (IPCC default)
_CARBON_FRACTION = 0.47

# CO₂ to carbon molecular weight ratio (44/12)
_CO2_TO_CARBON_RATIO = 44.0 / 12.0


def estimate_co2e_from_ndvi_delta(
    delta_ndvi: float,
    area_hectares: float,
) -> dict:
    """
    Estimate CO₂e sequestration from NDVI change over a given area.

    This is an MVP estimation model that uses conservative linear assumptions
    to convert vegetation index changes into carbon dioxide equivalent estimates.
    The model is designed for transparency and auditability in MRV workflows,
    not for making precision claims about carbon sequestration.

    The estimation pipeline:
        1. NDVI delta → Biomass change (using conservative min/max factors)
        2. Biomass → Carbon (using IPCC 0.47 carbon fraction)
        3. Carbon → CO₂e (using molecular weight ratio 44/12)
        4. Scale by area in hectares

    Args:
        delta_ndvi: Change in mean NDVI between baseline and monitoring periods.
                    Positive values indicate vegetation increase.
        area_hectares: Project area in hectares.

    Returns:
        Dictionary containing:
            - min_tonnes_co2e: Conservative lower bound estimate
            - max_tonnes_co2e: Conservative upper bound estimate
            - assumptions: List of strings explaining the model assumptions

    Note:
        Negative delta_ndvi values will produce negative CO₂e estimates,
        indicating net emissions rather than sequestration.
    """
    # Calculate biomass change range (tonnes dry biomass)
    min_biomass = delta_ndvi * _MIN_BIOMASS_FACTOR * area_hectares
    max_biomass = delta_ndvi * _MAX_BIOMASS_FACTOR * area_hectares

    # Convert biomass to carbon (tonnes C)
    min_carbon = min_biomass * _CARBON_FRACTION
    max_carbon = max_biomass * _CARBON_FRACTION

    # Convert carbon to CO₂e (tonnes CO₂e)
    min_co2e = min_carbon * _CO2_TO_CARBON_RATIO
    max_co2e = max_carbon * _CO2_TO_CARBON_RATIO

    return {
        "min_tonnes_co2e": min_co2e,
        "max_tonnes_co2e": max_co2e,
        "assumptions": [
            "MVP estimation model using simplified linear NDVI-to-biomass conversion",
            f"Biomass factor range: {_MIN_BIOMASS_FACTOR}-{_MAX_BIOMASS_FACTOR} tonnes dry biomass/ha per unit NDVI",
            f"Carbon fraction of biomass: {_CARBON_FRACTION} (IPCC default)",
            f"CO₂ to carbon ratio: {_CO2_TO_CARBON_RATIO:.2f} (molecular weight 44/12)",
            "Values are conservative estimates intended for transparency, not precision claims",
            "Model does not account for soil carbon, root biomass, or species-specific factors",
        ],
    }
