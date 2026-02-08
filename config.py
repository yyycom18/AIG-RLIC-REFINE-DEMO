"""
Configuration for AIG Investment Clock (RLIC Refine).
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

# FRED API key: Doc/FRED_API_KEY.txt (workspace) or env FRED_API_KEY
DOC_FRED_KEY = BASE_DIR.parent / "Doc" / "FRED_API_KEY.txt"

# Data range
START_DATE = "1990-01-01"
END_DATE = "2025-12-31"

# Sector ETFs (target)
SECTOR_ETFS = [
    "XLK",   # Technology
    "XLF",   # Financials
    "XLV",   # Health Care
    "XLY",   # Consumer Discretionary
    "XLC",   # Communication Services
    "XLI",   # Industrials
    "XLP",   # Consumer Staples
    "XLE",   # Energy
    "XLU",   # Utilities
    "XLB",   # Materials
    "XLRE",  # Real Estate
]

# FRED series
FRED_VIX1M = "VIXCLS"
FRED_VIX3M = "VXVCLS"
FRED_HY_OAS = "BAMLH0A0HYM2"
FRED_IG_OAS = "BAMLC0A0CM"

# Rolling window for percentile-based regime (months)
ROLLING_WINDOW_MONTHS = 60

# Quadrant labels (X = VIX ratio = stress horizon, Y = HY-IG = credit stress)
QUADRANTS = {
    ("Low", "Easy"): "Stable expansion (Risk-on)",
    ("Low", "Tight"): "Late cycle (Selective)",
    ("High", "Easy"): "Shock regime (Buy recovery)",
    ("High", "Tight"): "Structural stress (Capital preservation)",
}
