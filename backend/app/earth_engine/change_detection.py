"""
NDVI change detection module for MRV verification.

Computes vegetation change between baseline and monitoring periods.
"""

from typing import Optional

import ee

from backend.app.earth_engine.ee_client import init_ee
from backend.app.earth_engine.indices import ndvi
from backend.app.earth_engine.sentinel2 import get_sentinel2_composite


def compute_ndvi_change(
    geometry: ee.Geometry,
    baseline_start: str,
    baseline_end: str,
    monitoring_start: str,
    monitoring_end: str,
    land_cover: Optional[str] = None,
) -> dict:
    """
    Compute NDVI change between baseline and monitoring periods.

    Delta NDVI is computed in Python (not Earth Engine) because pixel-wise
    image subtraction can fail when baseline and monitoring periods have
    different valid pixel masks due to cloud cover, seasonality, or SCL
    classification differences. Computing delta from reduced means ensures
    consistent results regardless of mask alignment.

    Args:
        geometry: Area of interest as an ee.Geometry object.
        baseline_start: Baseline period start date (YYYY-MM-DD).
        baseline_end: Baseline period end date (YYYY-MM-DD).
        monitoring_start: Monitoring period start date (YYYY-MM-DD).
        monitoring_end: Monitoring period end date (YYYY-MM-DD).
        land_cover: Optional land cover type to control SCL masking.
                    - "forest": Vegetation only (SCL class 4)
                    - None or other: Default vegetation + bare soil classes

    Returns:
        Dictionary with mean NDVI values:
            - baseline_ndvi: Mean NDVI for baseline period (None if insufficient pixels)
            - monitoring_ndvi: Mean NDVI for monitoring period (None if insufficient pixels)
            - delta_ndvi: Change in NDVI (monitoring - baseline), or None if either mean is None
    """
    init_ee()

    # Fetch composites for both periods
    baseline_composite = get_sentinel2_composite(geometry, baseline_start, baseline_end, land_cover)
    monitoring_composite = get_sentinel2_composite(geometry, monitoring_start, monitoring_end, land_cover)

    # Compute NDVI for each period
    baseline_ndvi_img = ndvi(baseline_composite)
    monitoring_ndvi_img = ndvi(monitoring_composite)

    # Reduce over geometry to get mean values
    baseline_mean = baseline_ndvi_img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=10,
        maxPixels=1e9,
    ).get("NDVI").getInfo()

    monitoring_mean = monitoring_ndvi_img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=10,
        maxPixels=1e9,
    ).get("NDVI").getInfo()

    # Compute delta in Python to avoid mask alignment issues
    if baseline_mean is not None and monitoring_mean is not None:
        delta_mean = monitoring_mean - baseline_mean
    else:
        delta_mean = None

    return {
        "baseline_ndvi": baseline_mean,
        "monitoring_ndvi": monitoring_mean,
        "delta_ndvi": delta_mean,
    }
