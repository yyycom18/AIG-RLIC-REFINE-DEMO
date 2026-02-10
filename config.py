"""
Configuration for AIG Investment Clock (RLIC Refine).
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"

# FRED API key: project FRED_API_KEY.txt (gitignored), or Doc/FRED_API_KEY.txt, or env FRED_API_KEY
FRED_KEY_FILE = BASE_DIR / "FRED_API_KEY.txt"
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

# S&P cycles (Bull / Bear periods) for regime backtest by sub-period
# Each period is used to slice the sample and show avg return / drawdown by quadrant within that period
SP_CYCLES = [
    {"name": "Full sample", "start": None, "end": None, "description": "Entire backtest range"},
    {"name": "Dot-com bust & aftermath", "start": "2000-03-31", "end": "2002-09-30", "description": "Bear"},
    {"name": "2002–2007 expansion", "start": "2002-10-31", "end": "2007-10-31", "description": "Bull"},
    {"name": "GFC (2007–2009)", "start": "2007-11-30", "end": "2009-02-28", "description": "Bear"},
    {"name": "2009–2020 bull", "start": "2009-03-31", "end": "2020-02-29", "description": "Bull"},
    {"name": "COVID crash & rebound", "start": "2020-03-31", "end": "2020-05-31", "description": "Bear then rebound"},
    {"name": "2020–2021 recovery", "start": "2020-06-30", "end": "2021-12-31", "description": "Bull"},
    {"name": "2022 bear", "start": "2022-01-31", "end": "2022-10-31", "description": "Bear"},
    {"name": "2022–2025 recovery", "start": "2022-11-30", "end": "2025-12-31", "description": "Bull"},
]
