"""
Fetch data for AIG Investment Clock backtest.
- FRED: VIX1M (VIXCLS), VIX3M (VXVCLS), HY OAS (BAMLH0A0HYM2), IG OAS (BAMLC0A0CM)
- yfinance: Sector ETFs (XLK, XLF, ...)
"""
import os
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import yfinance as yf

import config

# Try to load FRED key: env FRED_API_KEY, then project FRED_API_KEY.txt, then Doc/FRED_API_KEY.txt
def _get_fred_key():
    key = os.getenv("FRED_API_KEY")
    if key:
        return key.strip()
    for path in (config.FRED_KEY_FILE, config.DOC_FRED_KEY):
        if path.exists():
            key = path.read_text().strip()
            if key and not key.startswith("paste") and "your" not in key.lower():
                return key
    return None


def fetch_fred_indicators():
    """Fetch VIX1M, VIX3M, HY-OAS, IG-OAS from FRED."""
    api_key = _get_fred_key()
    if not api_key:
        raise ValueError(
            "FRED API key not found. Set FRED_API_KEY env or put key in Doc/FRED_API_KEY.txt"
        )
    from fredapi import Fred
    fred = Fred(api_key=api_key)

    start = config.START_DATE
    end = config.END_DATE

    out = {}
    # VIX 1M
    s = fred.get_series(config.FRED_VIX1M, observation_start=start, observation_end=end)
    s.name = "VIX1M"
    out["VIX1M"] = s

    # VIX 3M
    s = fred.get_series(config.FRED_VIX3M, observation_start=start, observation_end=end)
    s.name = "VIX3M"
    out["VIX3M"] = s

    # HY OAS
    s = fred.get_series(config.FRED_HY_OAS, observation_start=start, observation_end=end)
    s.name = "HY_OAS"
    out["HY_OAS"] = s

    # IG OAS
    s = fred.get_series(config.FRED_IG_OAS, observation_start=start, observation_end=end)
    s.name = "IG_OAS"
    out["IG_OAS"] = s

    return out


def fetch_sector_etfs():
    """Fetch sector ETF prices from yfinance."""
    start = config.START_DATE
    end = config.END_DATE
    data = {}
    for ticker in config.SECTOR_ETFS:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(start=start, end=end)
            if hist is not None and not hist.empty:
                data[ticker] = hist["Close"].dropna()
        except Exception as e:
            print(f"  Warning: {ticker} failed: {e}")
    return data


def run():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching FRED indicators...")
    fred = fetch_fred_indicators()
    df_fred = pd.DataFrame(fred)
    df_fred["VIX_RATIO"] = df_fred["VIX1M"] / df_fred["VIX3M"]
    df_fred["HY_IG_SPREAD"] = df_fred["HY_OAS"] - df_fred["IG_OAS"]
    df_fred.to_csv(config.DATA_DIR / "indicators_daily.csv")
    print(f"  Saved indicators_daily.csv: {df_fred.index.min()} to {df_fred.index.max()}")

    print("Fetching sector ETFs...")
    etfs = fetch_sector_etfs()
    df_etf = pd.DataFrame(etfs)
    df_etf.to_csv(config.DATA_DIR / "sector_etfs_daily.csv")
    print(f"  Saved sector_etfs_daily.csv: {len(etfs)} ETFs")

    # Monthly and quarterly resampled (for backtest)
    df_fred_m = df_fred.resample("ME").last()
    df_fred_m.to_csv(config.DATA_DIR / "indicators_monthly.csv")
    df_fred_q = df_fred.resample("QE").last()
    df_fred_q.to_csv(config.DATA_DIR / "indicators_quarterly.csv")

    df_etf_m = df_etf.resample("ME").last()
    df_etf_m.to_csv(config.DATA_DIR / "sector_etfs_monthly.csv")
    df_etf_q = df_etf.resample("QE").last()
    df_etf_q.to_csv(config.DATA_DIR / "sector_etfs_quarterly.csv")

    meta = {
        "fetched_at": datetime.now().isoformat(),
        "indicators_daily_rows": len(df_fred),
        "sector_etfs": list(etfs.keys()),
        "date_range": {"start": str(df_fred.index.min().date()), "end": str(df_fred.index.max().date())},
    }
    with open(config.DATA_DIR / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("Done.")


if __name__ == "__main__":
    run()
