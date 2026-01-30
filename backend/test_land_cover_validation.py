"""
NDVI Pipeline Land Cover Validation Test

Validates that the NDVI pipeline produces expected results across
contrasting land cover types:
- Urban area (expected: low NDVI)
- Dense forest (expected: high NDVI)
- Agricultural region (expected: moderate NDVI)

This demonstrates pipeline sensitivity and correctness.
"""

import ee

from backend.app.earth_engine.ee_client import init_ee
from backend.app.earth_engine.change_detection import compute_ndvi_change

# ---------------------------------------------------------------------
# Initialize Earth Engine
# ---------------------------------------------------------------------
init_ee()

# ---------------------------------------------------------------------
# Date ranges (consistent across all test cases)
# ---------------------------------------------------------------------
BASELINE_START = "2022-01-01"
BASELINE_END = "2022-12-31"
MONITORING_START = "2024-01-01"
MONITORING_END = "2024-12-31"

# ---------------------------------------------------------------------
# Test geometries representing different land cover types
# ---------------------------------------------------------------------

# Urban area - Mumbai city center (expected: low NDVI)
urban_geometry = ee.Geometry.Polygon([
    [
        [72.85, 19.00],
        [72.90, 19.00],
        [72.90, 19.05],
        [72.85, 19.05],
        [72.85, 19.00],
    ]
])

# Dense forest - Western Ghats forest region (expected: high NDVI)
forest_geometry = ee.Geometry.Polygon([
    [
        [73.70, 15.40],
        [73.75, 15.40],
        [73.75, 15.45],
        [73.70, 15.45],
        [73.70, 15.40],
    ]
])

# Agricultural region - Punjab farmland (expected: moderate NDVI)
agriculture_geometry = ee.Geometry.Polygon([
    [
        [75.80, 30.90],
        [75.85, 30.90],
        [75.85, 30.95],
        [75.80, 30.95],
        [75.80, 30.90],
    ]
])

# ---------------------------------------------------------------------
# Test cases: (name, geometry, expectation, land_cover)
# ---------------------------------------------------------------------
test_cases = [
    ("Urban (Mumbai)", urban_geometry, "Low NDVI expected", None),
    ("Dense Forest (Western Ghats)", forest_geometry, "High NDVI expected", "forest"),
    ("Agriculture (Punjab)", agriculture_geometry, "Moderate NDVI expected", None),
]

# ---------------------------------------------------------------------
# Run validation
# ---------------------------------------------------------------------
print("=" * 70)
print("NDVI PIPELINE LAND COVER VALIDATION")
print("=" * 70)
print(f"\nBaseline Period:   {BASELINE_START} to {BASELINE_END}")
print(f"Monitoring Period: {MONITORING_START} to {MONITORING_END}")
print()

results = []

for name, geometry, expectation, land_cover in test_cases:
    print("-" * 70)
    print(f"Testing: {name}")
    print(f"Expectation: {expectation}")
    print(f"Land cover mode: {land_cover or 'default'}")
    print("-" * 70)
    
    ndvi_result = compute_ndvi_change(
        geometry=geometry,
        baseline_start=BASELINE_START,
        baseline_end=BASELINE_END,
        monitoring_start=MONITORING_START,
        monitoring_end=MONITORING_END,
        land_cover=land_cover,
    )
    
    print(f"  Baseline NDVI   : {ndvi_result['baseline_ndvi']:.4f}")
    print(f"  Monitoring NDVI : {ndvi_result['monitoring_ndvi']:.4f}")
    print(f"  Delta NDVI      : {ndvi_result['delta_ndvi']:.4f}")
    print()
    
    results.append({
        "name": name,
        "baseline": ndvi_result["baseline_ndvi"],
        "monitoring": ndvi_result["monitoring_ndvi"],
        "delta": ndvi_result["delta_ndvi"],
    })

# ---------------------------------------------------------------------
# Summary comparison
# ---------------------------------------------------------------------
print("=" * 70)
print("SUMMARY COMPARISON")
print("=" * 70)
print(f"{'Land Cover':<30} {'Baseline':>12} {'Monitoring':>12} {'Delta':>12}")
print("-" * 70)

for r in results:
    print(f"{r['name']:<30} {r['baseline']:>12.4f} {r['monitoring']:>12.4f} {r['delta']:>12.4f}")

print()
print("Validation: Forest should have highest NDVI, Urban lowest.")
print("=" * 70)
