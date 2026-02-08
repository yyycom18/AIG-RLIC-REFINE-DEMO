"""
AIG Investment Clock backtest.
- Classify each month/quarter into quadrant using rolling percentiles (X=VIX ratio, Y=HY-IG spread).
- Compute sector ETF return and drawdown by quadrant (monthly and quarterly).
- Output favorite/unfavorite sectors per quadrant; backtest summary.
"""
import json
import logging
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

import config

logger = logging.getLogger(__name__)


def load_data():
    """Load monthly indicator and sector ETF data. Raises helpful errors if files missing."""
    data_dir = config.DATA_DIR
    ind_path = data_dir / "indicators_monthly.csv"
    etf_path = data_dir / "sector_etfs_monthly.csv"

    if not ind_path.exists():
        raise FileNotFoundError(
            f"Data file not found: {ind_path}\n"
            "Run 'python fetch_data.py' first to download data from FRED and yfinance."
        )
    if not etf_path.exists():
        raise FileNotFoundError(
            f"Data file not found: {etf_path}\n"
            "Run 'python fetch_data.py' first to download data from FRED and yfinance."
        )

    try:
        ind = pd.read_csv(ind_path, index_col=0, parse_dates=True)
        etf = pd.read_csv(etf_path, index_col=0, parse_dates=True)
    except Exception as e:
        raise ValueError(f"Error loading data: {e}. Check file format and integrity.") from e

    for col in ["VIX_RATIO", "HY_IG_SPREAD"]:
        if col not in ind.columns:
            raise ValueError(f"indicators_monthly.csv missing column: {col}")
    ind = ind[["VIX_RATIO", "HY_IG_SPREAD"]].dropna(how="all")
    common = ind.index.intersection(etf.index)
    if common.empty:
        raise ValueError(
            f"No overlapping dates between indicators ({ind.index.min()} to {ind.index.max()}) "
            f"and ETF data ({etf.index.min()} to {etf.index.max()}). Check data range."
        )
    ind = ind.loc[common].sort_index()
    etf = etf.loc[common].sort_index()
    logger.info("load_data: %s to %s (%s months)", common.min(), common.max(), len(common))
    return ind, etf


def rolling_percentile(series: pd.Series, window: int, p: float) -> pd.Series:
    """Rolling percentile (0-100)."""
    return series.rolling(window, min_periods=max(1, window // 2)).apply(
        lambda x: np.nanpercentile(x.dropna(), p), raw=False
    )


def classify_quadrant(vix_ratio: pd.Series, hy_ig: pd.Series, window: int):
    """
    Classify each date into quadrant using rolling 50th percentile (median) as threshold.
    Low VIX ratio = below median; High = above. Easy credit = below median HY-IG; Tight = above.
    Returns DataFrame with columns: VIX_class, HYIG_class, Quadrant, QuadrantLabel.
    """
    vix_p50 = rolling_percentile(vix_ratio, window, 50)
    hy_p50 = rolling_percentile(hy_ig, window, 50)
    vix_class = (vix_ratio >= vix_p50).map({True: "High", False: "Low"})
    hy_class = (hy_ig >= hy_p50).map({True: "Tight", False: "Easy"})
    quad_label = vix_class + " VIX, " + hy_class + " credit"
    quad_name = vix_class + "_" + hy_class
    df = pd.DataFrame({
        "VIX_ratio": vix_ratio,
        "HY_IG_spread": hy_ig,
        "VIX_class": vix_class,
        "HYIG_class": hy_class,
        "Quadrant": quad_name,
        "QuadrantLabel": quad_label,
    }, index=vix_ratio.index)
    return df


def returns_and_drawdown(prices: pd.DataFrame) -> tuple:
    """
    Compute period returns, running drawdown (from peak), and per-column max drawdown.
    Returns: ret, dd (running), max_dd (Series: most negative drawdown per column).
    """
    ret = prices.pct_change()
    cum = (1 + ret).cumprod()
    peak = cum.expanding().max()
    dd = (cum - peak) / peak  # drawdown as negative
    max_dd = dd.min()  # most negative = worst drawdown per column
    return ret, dd, max_dd


def backtest_monthly_quarterly(ind: pd.DataFrame, etf: pd.DataFrame, window: int):
    """
    Backtest: quadrant classification + sector return/drawdown by quadrant.
    Returns dict with monthly and quarterly stats, favorite/unfavorite sectors per quadrant.
    """
    vix = ind["VIX_RATIO"]
    hyig = ind["HY_IG_SPREAD"]
    quad = classify_quadrant(vix, hyig, window)

    ret_m, dd_m, max_dd_m = returns_and_drawdown(etf)
    ret_m = ret_m.dropna(how="all")

    common_index = quad.index.intersection(ret_m.index)
    if common_index.empty:
        raise ValueError(
            f"No overlapping dates between indicators ({quad.index.min()} to {quad.index.max()}) "
            f"and ETF returns ({ret_m.index.min()} to {ret_m.index.max()})."
        )
    logger.info("Backtest period: %s to %s (%s months)", common_index.min(), common_index.max(), len(common_index))

    quad_aligned = quad.reindex(ret_m.index).ffill()
    n_valid = quad_aligned["Quadrant"].notna().sum()
    if n_valid == 0:
        raise ValueError("Quadrant alignment failed: all NaN. Check indicator and ETF date alignment.")
    logger.info("Valid quadrant assignments: %s / %s", n_valid, len(quad_aligned))

    # Monthly: average return, average drawdown, and max drawdown by quadrant (per sector)
    monthly_by_quad = []
    for q in quad_aligned["Quadrant"].dropna().unique():
        mask = quad_aligned["Quadrant"] == q
        if mask.sum() < 2:
            continue
        ret_q = ret_m.loc[mask]
        dd_q = dd_m.loc[mask]
        avg_ret = ret_q.mean()
        avg_dd = dd_q.mean()
        max_dd_q = dd_q.min()  # worst drawdown in this quadrant per sector
        n = mask.sum()
        monthly_by_quad.append({
            "quadrant": q,
            "n_months": int(n),
            "avg_return": avg_ret.to_dict(),
            "avg_drawdown": avg_dd.to_dict(),
            "max_drawdown": max_dd_q.to_dict(),
        })

    # Quarterly
    ind_q = ind.resample("QE").last()
    etf_q = etf.resample("QE").last()
    vix_q = ind_q["VIX_RATIO"]
    hyig_q = ind_q["HY_IG_SPREAD"]
    quad_q = classify_quadrant(vix_q, hyig_q, max(4, window // 3))  # ~quarterly window
    ret_q, dd_q, _ = returns_and_drawdown(etf_q)
    ret_q = ret_q.dropna(how="all")
    quad_q_aligned = quad_q.reindex(ret_q.index).ffill()

    quarterly_by_quad = []
    for q in quad_q_aligned["Quadrant"].dropna().unique():
        mask = quad_q_aligned["Quadrant"] == q
        if mask.sum() < 2:
            continue
        rq = ret_q.loc[mask]
        dq = dd_q.loc[mask]
        quarterly_by_quad.append({
            "quadrant": q,
            "n_quarters": int(mask.sum()),
            "avg_return": rq.mean().to_dict(),
            "avg_drawdown": dq.mean().to_dict(),
            "max_drawdown": dq.min().to_dict(),
        })

    # Favorite / unfavorite per quadrant (by avg return and by avg drawdown)
    def fav_unfav(avg_ret_series, avg_dd_series, n=4):
        sr = pd.Series(avg_ret_series).dropna()
        sd = pd.Series(avg_dd_series).dropna()
        by_ret = sr.sort_values(ascending=False)
        by_dd = sd.sort_values(ascending=True)  # less negative = better
        return {
            "favorite_by_return": by_ret.head(n).index.tolist(),
            "unfavorite_by_return": by_ret.tail(n).index.tolist(),
            "favorite_by_drawdown": by_dd.head(n).index.tolist(),
            "unfavorite_by_drawdown": by_dd.tail(n).index.tolist(),
        }

    monthly_fav = {}
    for item in monthly_by_quad:
        monthly_fav[item["quadrant"]] = fav_unfav(item["avg_return"], item["avg_drawdown"], n=4)

    quarterly_fav = {}
    for item in quarterly_by_quad:
        quarterly_fav[item["quadrant"]] = fav_unfav(item["avg_return"], item["avg_drawdown"], n=4)

    # Full history for dashboard: quadrant per month/quarter (use list of dicts for JSON)
    quad_history_m = quad_aligned.dropna(how="all").reset_index()
    quad_history_m = quad_history_m.rename(columns={quad_history_m.columns[0]: "date"})
    quad_history_m["date"] = quad_history_m["date"].astype(str)
    quad_history_q = quad_q_aligned.dropna(how="all").reset_index()
    quad_history_q = quad_history_q.rename(columns={quad_history_q.columns[0]: "date"})
    quad_history_q["date"] = quad_history_q["date"].astype(str)

    total_months = sum(item["n_months"] for item in monthly_by_quad)
    return {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "data_sources": "FRED + yfinance",
            "data_range": {"start": str(ind.index.min()), "end": str(ind.index.max())},
            "is_real_data": total_months > 0 and len(ind) >= 100,
        },
        "rolling_window_months": window,
        "monthly_by_quadrant": monthly_by_quad,
        "quarterly_by_quadrant": quarterly_by_quad,
        "monthly_favorite_unfavorite": monthly_fav,
        "quarterly_favorite_unfavorite": quarterly_fav,
        "quadrant_history_monthly": quad_history_m.to_dict(orient="records"),
        "quadrant_history_quarterly": quad_history_q.to_dict(orient="records"),
        "indicators_monthly": ind.reset_index().rename(columns={"index": "date"}).assign(date=lambda x: x["date"].astype(str)).to_dict(orient="records"),
    }


def current_regime(ind: pd.DataFrame, window: int):
    """Current month-end regime (last row) using rolling percentiles."""
    vix = ind["VIX_RATIO"].dropna()
    hyig = ind["HY_IG_SPREAD"].dropna()
    if vix.empty or hyig.empty:
        return None
    last_dt = ind.index.max()
    vix_p50 = rolling_percentile(vix, window, 50)
    hy_p50 = rolling_percentile(hyig, window, 50)
    vix_last = vix.loc[last_dt]
    hy_last = hyig.loc[last_dt]
    v50 = vix_p50.loc[last_dt] if last_dt in vix_p50.index else np.nanpercentile(vix.dropna().values, 50)
    h50 = hy_p50.loc[last_dt] if last_dt in hy_p50.index else np.nanpercentile(hyig.dropna().values, 50)
    vix_class = "High" if vix_last >= v50 else "Low"
    hy_class = "Tight" if hy_last >= h50 else "Easy"
    quad = f"{vix_class}_{hy_class}"
    label = config.QUADRANTS.get((vix_class, hy_class), quad)
    return {
        "date": str(last_dt.date()) if hasattr(last_dt, "date") else str(last_dt),
        "VIX_ratio": float(vix_last),
        "HY_IG_spread": float(hy_last),
        "VIX_class": vix_class,
        "HYIG_class": hy_class,
        "Quadrant": quad,
        "QuadrantLabel": label,
        "threshold_VIX_median": float(v50),
        "threshold_HY_IG_median": float(h50),
    }


def run_backtest():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    config.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    ind, etf = load_data()
    window = config.ROLLING_WINDOW_MONTHS
    results = backtest_monthly_quarterly(ind, etf, window)
    current = current_regime(ind, window)
    results["current_regime"] = current

    # Serialize for JSON (convert any non-serializable)
    def to_serializable(obj):
        if isinstance(obj, dict):
            return {k: to_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [to_serializable(x) for x in obj]
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if hasattr(obj, "item"):
            return obj.item()
        return obj

    out = to_serializable(results)
    with open(config.OUTPUTS_DIR / "backtest_results.json", "w") as f:
        json.dump(out, f, indent=2)

    # Also save quadrant history as CSV for dashboard
    if results.get("quadrant_history_monthly"):
        df_q = pd.DataFrame(results["quadrant_history_monthly"])
        df_q.to_csv(config.OUTPUTS_DIR / "quadrant_history_monthly.csv", index=False)

    logger.info("Backtest saved to %s", config.OUTPUTS_DIR / "backtest_results.json")
    if current:
        logger.info("Current regime: %s", current["QuadrantLabel"])
    return results


if __name__ == "__main__":
    run_backtest()
