"""
Google Earth Engine utilities for satellite-based MRV verification.
"""

from backend.app.earth_engine.ee_client import init_ee
from backend.app.earth_engine.indices import ndvi
from backend.app.earth_engine.sentinel2 import get_sentinel2_composite

__all__ = [
    "init_ee",
    "get_sentinel2_composite",
    "compute_ndvi",
]
