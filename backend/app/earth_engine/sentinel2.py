"""
Sentinel-2 Surface Reflectance imagery helper module.

Provides functions to fetch and process Sentinel-2 SR data from Google Earth Engine.
"""

from typing import List, Optional

import ee

from backend.app.earth_engine.ee_client import init_ee

_SENTINEL2_SR = "COPERNICUS/S2_SR"
_MAX_CLOUD_PERCENTAGE = 20

# SCL class definitions
# 4 = Vegetation (includes all green vegetation: crops, grass, shrubs, forests)
# 5 = Bare Soil
# 6 = Water (NOT forest - must be excluded from vegetation analysis)
# Note: Forests are spectrally represented by SCL class 4 (Vegetation) in Sentinel-2 SR.
#       No explicit forest class exists in SCL.
# See: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR
SCL_VEGETATION = 4
SCL_BARE_SOIL = 5
SCL_WATER = 6

# Predefined SCL class sets for different land cover types
# Default: vegetation + bare soil (suitable for agriculture, urban, mixed)
SCL_CLASSES_DEFAULT = [SCL_VEGETATION, SCL_BARE_SOIL]
# Forest: vegetation only (excludes bare soil to focus on canopy)
SCL_CLASSES_FOREST = [SCL_VEGETATION]


def _create_scl_mask(scl_classes: List[int]):
    """
    Create a masking function for specified SCL classes.

    Args:
        scl_classes: List of SCL class values to keep.

    Returns:
        Function that masks an ee.Image based on SCL band.
    """
    def _mask_scl(image: ee.Image) -> ee.Image:
        scl = image.select("SCL")
        # Build mask by OR-ing all allowed classes
        valid_mask = scl.eq(scl_classes[0])
        for cls in scl_classes[1:]:
            valid_mask = valid_mask.Or(scl.eq(cls))
        return image.updateMask(valid_mask)
    
    return _mask_scl


def get_sentinel2_composite(
    geometry: ee.Geometry,
    start_date: str,
    end_date: str,
    land_cover: Optional[str] = None,
) -> ee.Image:
    """
    Fetch a cloud-filtered median composite from Sentinel-2 Surface Reflectance.

    Args:
        geometry: Area of interest as an ee.Geometry object.
        start_date: Start date in YYYY-MM-DD format.
        end_date: End date in YYYY-MM-DD format.
        land_cover: Optional land cover type to control SCL masking.
                    - "forest": SCL class 4 only (vegetation, where forests are classified)
                    - None or other: Default classes 4, 5 (vegetation + bare soil)

    Returns:
        Median composite ee.Image from filtered Sentinel-2 SR collection.
    """
    init_ee()

    # Select SCL classes based on land cover type
    if land_cover == "forest":
        scl_classes = SCL_CLASSES_FOREST
    else:
        scl_classes = SCL_CLASSES_DEFAULT

    mask_fn = _create_scl_mask(scl_classes)

    collection = (
        ee.ImageCollection(_SENTINEL2_SR)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", _MAX_CLOUD_PERCENTAGE))
        .select(["B4", "B8", "SCL"])
        .map(mask_fn)
        .select(["B4", "B8"])
    )

    return collection.median()

def get_sentinel2_rgb_preview(
    geometry: ee.Geometry,
    start_date: str,
    end_date: str,
) -> ee.Image:
    """
    Fetch a cloud-filtered RGB composite for human visualization.

    This function is intended ONLY for visual inspection and admin review,
    not for quantitative analysis.

    Returns:
        ee.Image with B4, B3, B2 bands preserved.
    """
    init_ee()

    collection = (
        ee.ImageCollection(_SENTINEL2_SR)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", _MAX_CLOUD_PERCENTAGE))
        .select(["B4", "B3", "B2"])
    )

    return collection.median()
