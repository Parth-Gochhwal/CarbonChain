import ee
import requests
from pathlib import Path

from backend.app.earth_engine.sentinel2 import get_sentinel2_rgb_preview
from backend.app.earth_engine.ee_client import init_ee

# Initialize Earth Engine
init_ee()

# Same geometry you used before
geom = ee.Geometry.Polygon([
    [
        [72.85, 19.00],
        [72.90, 19.00],
        [72.90, 19.05],
        [72.85, 19.05],
        [72.85, 19.00],
    ]
])

# Fetch composite
img = get_sentinel2_rgb_preview(
    geometry=geom,
    start_date="2024-01-01",
    end_date="2024-03-31",
)

# Prepare RGB visualization
rgb = img.visualize(
    bands=["B4", "B3", "B2"],  # Red, Green, Blue
    min=0,
    max=3000,
)

# Request a thumbnail
url = rgb.getThumbURL({
    "region": geom,
    "dimensions": 512,
    "format": "png",
})

print("Downloading image from:", url)

# Download locally
output = Path("sentinel2_preview.png")
response = requests.get(url)
output.write_bytes(response.content)

print("Saved:", output.resolve())
