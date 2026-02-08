"""
Fetch data for AIG Investment Clock backtest.
- FRED: VIX1M (VIXCLS), VIX3M (VXVCLS), HY OAS (BAMLH0A0HYM2), IG OAS (BAMLC0A0CM)
- yfinance: Sector ETFs (XLK, XLF, ...)
"""
import os
import json
import logging
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import yfinance as yf

import config

logger = logging.getLogger(__name__)

REQUIRED_ROWS = 100  # minimum observations (~8 years) to consider data valid


def _get_fred_key():
    """Get FRED API key from env or files. Raises ValueError with clear message if not found."""
    sources = [
        ("Environment (FRED_API_KEY)", os.getenv("FRED_API_KEY")),
        ("Project file (FRED_API_KEY.txt)", config.FRED_KEY_FILE.read_text().strip() if config.FRED_KEY_FILE.exists() else None),
        ("Doc file (Doc/FRED_API_KEY.txt)", config.DOC_FRED_KEY.read_text().strip() if config.DOC_FRED_KEY.exists() else None),
    ]
    for source, key in sources:
        if key and not key.startswith("paste") and "your" not in (key or "").lower():
            logger.info("Using FRED API key from %s", source)
            return key.strip()
    raise ValueError(
        "FRED API key not found or invalid.\n"
        "Options:\n"
        "1. Set environment variable: export FRED_API_KEY='your_key'\n"
        "2. Create FRED_API_KEY.txt in this project folder (gitignored)\n"
        "3. Create Doc/FRED_API_KEY.txt at workspace root\n"
        "Get a free key at: https://fred.stlouisfed.org/docs/api/"
    )


def fetch_fred_indicators():
    """Fetch VIX1M, VIX3M, HY-OAS, IG-OAS from FRED."""
    api_key = _get_fred_key()
    try:
        from fredapi import Fred
        fred = Fred(api_key=api_key)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize FRED API: {e}") from e

    start = config.START_DATE
    end = config.END_DATE
    series_map = [
        ("VIX1M", config.FRED_VIX1M),
        ("VIX3M", config.FRED_VIX3M),
        ("HY_OAS", config.FRED_HY_OAS),
        ("IG_OAS", config.FRED_IG_OAS),
    ]
    out = {}
    for name, series_id in series_map:
        try:
            s = fred.get_series(series_id, observation_start=start, observation_end=end)
            if s is None or (hasattr(s, "empty") and s.empty):
                logger.warning("%s (%s): No data returned", name, series_id)
            else:
                s.name = name
                out[name] = s
                logger.info("%s: %s records from %s to %s", name, len(s), s.index.min(), s.index.max())
        except Exception as e:
            raise RuntimeError(f"Failed to fetch {name} ({series_id}): {e}") from e
    return out


def fetch_sector_etfs():
    """Fetch sector ETF prices from yfinance with retries for transient failures."""
    start = config.START_DATE
    end = config.END_DATE
    data = {}
    max_retries = 3
    for ticker in config.SECTOR_ETFS:
        for attempt in range(max_retries):
            try:
                t = yf.Ticker(ticker)
                hist = t.history(start=start, end=end)
                if hist is None or hist.empty:
                    logger.warning("%s: No data returned", ticker)
                    break
                if "Close" not in hist.columns:
                    logger.error("%s: Missing 'Close' column", ticker)
                    break
                data[ticker] = hist["Close"].dropna()
                logger.info("%s: %s records", ticker, len(hist))
                break
            except (ConnectionError, TimeoutError, OSError) as e:
                if attempt < max_retries - 1:
                    logger.warning("%s attempt %s failed: %s, retrying...", ticker, attempt + 1, e)
                    time.sleep(2 ** attempt)
                    continue
                logger.error("%s failed after %s attempts: %s", ticker, max_retries, e)
            except KeyError as e:
                logger.error("%s: Missing column %s", ticker, e)
                break
            except Exception as e:
                logger.error("%s: Unexpected error: %s", ticker, e)
                break
    return data


def run():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Fetching FRED indicators...")
    fred = fetch_fred_indicators()
    df_fred = pd.DataFrame(fred)

    # Validate FRED data
    expected_series = {"VIX1M", "VIX3M", "HY_OAS", "IG_OAS"}
    missing_series = expected_series - set(df_fred.columns)
    if missing_series:
        raise ValueError(f"Missing FRED series: {missing_series}")
    if len(df_fred) < REQUIRED_ROWS:
        raise ValueError(
            f"FRED data has only {len(df_fred)} rows, expected at least {REQUIRED_ROWS}. "
            "Check date range and API."
        )

    df_fred["VIX_RATIO"] = df_fred["VIX1M"] / df_fred["VIX3M"]
    df_fred["HY_IG_SPREAD"] = df_fred["HY_OAS"] - df_fred["IG_OAS"]
    df_fred.to_csv(config.DATA_DIR / "indicators_daily.csv")
    logger.info("FRED indicators: %s rows, %s to %s", len(df_fred), df_fred.index.min(), df_fred.index.max())
    logger.info("Missing values: %s / %s", df_fred.isnull().sum().sum(), df_fred.size)

    logger.info("Fetching sector ETFs...")
    etfs = fetch_sector_etfs()
    expected_etfs = set(config.SECTOR_ETFS)
    missing_etfs = expected_etfs - set(etfs.keys())
    if missing_etfs:
        logger.warning("Missing ETFs: %s (continuing with %s ETFs)", missing_etfs, len(etfs))

    df_etf = pd.DataFrame(etfs)
    if len(df_etf) < REQUIRED_ROWS:
        raise ValueError(
            f"ETF data has only {len(df_etf)} rows, expected at least {REQUIRED_ROWS}. "
            "Check yfinance and date range."
        )
    df_etf.to_csv(config.DATA_DIR / "sector_etfs_daily.csv")
    logger.info("Sector ETFs: %s symbols, %s rows", len(etfs), len(df_etf))

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
        "validation": {
            "fred_series_count": len(df_fred.columns),
            "etf_count": len(etfs),
            "missing_etfs": list(missing_etfs),
            "missing_values": int(df_fred.isnull().sum().sum()),
        },
    }
    with open(config.DATA_DIR / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    logger.info("All data fetched successfully. Ready to run backtest.py.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting data fetch...")
    run()
    logger.info("Data fetch completed.")
