"""
Google Earth Engine initialization module.

Handles service account authentication and ensures single initialization per process.
"""

import os
from pathlib import Path

import ee

_initialized: bool = False

_SERVICE_ACCOUNT = "earthengine-sa@carbonchain-483708.iam.gserviceaccount.com"
_DEFAULT_KEY_PATH = Path(__file__).parent.parent.parent / "secrets" / "earthengine-key.json"


def init_ee() -> None:
    """
    Initialize Google Earth Engine with service account credentials.

    Reads credentials from GOOGLE_APPLICATION_CREDENTIALS environment variable,
    falling back to secrets/earthengine-key.json if not set.

    This function is idempotent - calling it multiple times has no effect
    after the first successful initialization.

    Raises:
        FileNotFoundError: If the credentials file does not exist.
        ee.EEException: If Earth Engine initialization fails.
    """
    global _initialized

    if _initialized:
        return

    key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if key_path is None:
        key_path = str(_DEFAULT_KEY_PATH)

    if not Path(key_path).exists():
        raise FileNotFoundError(f"Earth Engine credentials not found at: {key_path}")

    credentials = ee.ServiceAccountCredentials(_SERVICE_ACCOUNT, key_path)
    ee.Initialize(credentials)

    _initialized = True
