import ee

from backend.app.earth_engine.ee_client import init_ee
from backend.app.earth_engine.change_detection import compute_ndvi_change
from backend.app.mrv import estimate_co2e_from_ndvi_delta

# ---------------------------------------------------------------------
# Initialize Earth Engine (idempotent)
# ---------------------------------------------------------------------
init_ee()

# ---------------------------------------------------------------------
# Example geometry (coastal vegetation patch – placeholder)
# ---------------------------------------------------------------------
geometry = ee.Geometry.Polygon([
    [
        [72.85, 19.00],
        [72.90, 19.00],
        [72.90, 19.05],
        [72.85, 19.05],
        [72.85, 19.00],
    ]
])

AREA_HECTARES = 50.0  # Example project size

# ---------------------------------------------------------------------
# Step 1: NDVI change detection
# ---------------------------------------------------------------------
ndvi_result = compute_ndvi_change(
    geometry=geometry,
    baseline_start="2022-01-01",
    baseline_end="2022-12-31",
    monitoring_start="2024-01-01",
    monitoring_end="2024-12-31",
)

print("\nNDVI Change Detection Result")
print(f"Baseline NDVI   : {ndvi_result['baseline_ndvi']}")
print(f"Monitoring NDVI : {ndvi_result['monitoring_ndvi']}")
print(f"Delta NDVI      : {ndvi_result['delta_ndvi']}")

# ---------------------------------------------------------------------
# Step 2: Carbon estimation from NDVI delta
# ---------------------------------------------------------------------
carbon_estimate = estimate_co2e_from_ndvi_delta(
    delta_ndvi=ndvi_result["delta_ndvi"],
    area_hectares=AREA_HECTARES,
)

print("\nCarbon Estimation Result (Conservative Range)")
print(f"Min CO2e (tonnes): {carbon_estimate['min_tonnes_co2e']}")
print(f"Max CO2e (tonnes): {carbon_estimate['max_tonnes_co2e']}")

print("\nAssumptions:")
for assumption in carbon_estimate["assumptions"]:
    print(f"- {assumption}")
