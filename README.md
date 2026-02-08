# AIG Investment Clock (RLIC Refine Demo)

Reframing the Royal London Investment Clock (RLIC) with **market-native, forward-looking** axes:

- **X-axis (Stress horizon):** VIX 1M / VIX 3M ratio (replaces Core CPI)
- **Y-axis (Credit stress):** HY–IG credit spread (replaces GDP growth)

Quadrants:

| X \ Y   | Easy credit     | Tight credit    |
|---------|------------------|-----------------|
| **Low VIX**  | Stable expansion (Risk-on) | Late cycle (Selective) |
| **High VIX** | Shock regime (Buy recovery) | Structural stress (Capital preservation) |

## Data

- **FRED:** VIX1M (VIXCLS), VIX3M (VXVCLS), HY OAS (BAMLH0A0HYM2), IG OAS (BAMLC0A0CM)
- **yfinance:** Sector ETFs (XLK, XLF, XLV, XLY, XLC, XLI, XLP, XLE, XLU, XLB, XLRE)

FRED API key: set `FRED_API_KEY` in the environment or place the key in `Doc/FRED_API_KEY.txt` (one line) at the workspace root (parent of this folder).

## Setup

```bash
cd AIG-RLIC-REFINE-DEMO
pip install -r requirements.txt
```

## Run

1. **Fetch data** (FRED + sector ETFs, 1990–2025):

   ```bash
   python fetch_data.py
   ```

2. **Run backtest** (rolling 60‑month percentiles → quadrants, sector return/drawdown by quadrant):

   ```bash
   python backtest.py
   ```

3. **Dashboard** (Regime Backtest study + AIG Investment Clock current status):

   ```bash
   streamlit run streamlit_app.py
   ```

## Dashboard

- **Regime Backtest study:** Sector average return and drawdown by quadrant (monthly and quarterly); favorite/unfavorite sectors by return and by drawdown; quadrant history over time.
- **AIG Investment Clock:** Current month-end X (VIX ratio) and Y (HY–IG spread), current regime label, and time series of both indicators.

## GitHub

Repo: [https://github.com/yyycom18/AIG-RLIC-REFINE-DEMO](https://github.com/yyycom18/AIG-RLIC-REFINE-DEMO)

**Pushing with GitHub Desktop:** See **[GITHUB_DESKTOP.md](GITHUB_DESKTOP.md)** for step-by-step (init repo, add folder, set remote, fix common push errors).

**Command line (first time):**

```bash
cd AIG-RLIC-REFINE-DEMO
git init
git remote add origin https://github.com/yyycom18/AIG-RLIC-REFINE-DEMO.git
git add .
git commit -m "AIG Investment Clock: fetch, backtest, Streamlit dashboard"
git branch -M main
git push -u origin main
```

The repo includes a **placeholder** `outputs/backtest_results.json` so the Streamlit app loads on first deploy. For **full backtest results**: run `fetch_data.py` and `backtest.py` locally (with FRED API key), then commit `outputs/backtest_results.json` and push so the app shows real data. The `.gitignore` allows that file; other `data/*` and `outputs/*` files stay ignored to keep the repo small.
