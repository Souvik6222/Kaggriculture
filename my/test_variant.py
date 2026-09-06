"""Configurable Agent for ablation testing."""
import sys
import os

# We import baseline's BLOB, decoding, constants, and helper functions
with open("my/baseline_main.py", "r") as f:
    baseline_code = f.read()

# We can parameterize Agent's act() method with feature flags:
# - enable_water_rescue
# - enable_harvest_rescue
# - market_style: 'baseline' or 'reorder'
# - dead_stock_style: 'baseline' or 'v4_early'
# - enable_safety_layer
# - enable_fertilizer_718 (sweep fertilizer at step 718)
