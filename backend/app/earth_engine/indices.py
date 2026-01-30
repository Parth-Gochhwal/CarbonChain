"""
Vegetation index computation functions for Sentinel-2 imagery.

Pure functions that compute spectral indices from ee.Image inputs.
"""

import ee


def ndvi(image: ee.Image) -> ee.Image:
    """
    Compute Normalized Difference Vegetation Index (NDVI).

    NDVI = (NIR - RED) / (NIR + RED)

    Args:
        image: Sentinel-2 SR ee.Image containing B8 (NIR) and B4 (RED) bands.

    Returns:
        ee.Image with a single band named "NDVI".
    """
    nir = image.select("B8")
    red = image.select("B4")

    ndvi = nir.subtract(red).divide(nir.add(red))

    return ndvi.rename("NDVI")
