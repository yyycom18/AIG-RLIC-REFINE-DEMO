"""
AIG Investment Clock – Streamlit dashboard.
- Regime Backtest study: backtest results (sector return/drawdown by quadrant, favorite/unfavorite).
- AIG Investment Clock: current month-end X & Y and current regime.
"""
import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import config

st.set_page_config(
    page_title="AIG Investment Clock",
    page_icon="🕐",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE = Path(__file__).resolve().parent
OUTPUTS = BASE / "outputs"
DATA = BASE / "data"


@st.cache_data
def load_backtest():
    p = OUTPUTS / "backtest_results.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


@st.cache_data
def load_indicators_monthly():
    p = DATA / "indicators_monthly.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    return df


def main():
    st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; color: white; text-align: center; margin-bottom: 1.5rem;">
            <h1>🕐 AIG Investment Clock</h1>
            <p>RLIC Refine: VIX1M/3M (X) × HY–IG Spread (Y) → Regime & Sector Backtest</p>
        </div>
    """, unsafe_allow_html=True)

    sidebar = st.sidebar
    sidebar.header("Navigation")
    section = sidebar.radio(
        "Section",
        ["Regime Backtest Study", "AIG Investment Clock (Current Status)"],
    )

    # Debug: show paths and file existence (helps when deployed on Streamlit Cloud)
    with sidebar.expander("🔧 Paths & files (debug)"):
        backtest_path = OUTPUTS / "backtest_results.json"
        indicators_path = DATA / "indicators_monthly.csv"
        st.code(f"BASE: {BASE}\nbacktest_results.json exists: {backtest_path.exists()}\nindicators_monthly.csv exists: {indicators_path.exists()}", language=None)

    bt = load_backtest()
    ind = load_indicators_monthly()

    if section == "Regime Backtest Study":
        st.header("Regime Backtest Study")
        if not bt:
            st.warning("Run `python fetch_data.py` then `python backtest.py` to generate backtest results.")
            return

        # Check if this is placeholder data (no months in any quadrant)
        monthly_quad = bt.get("monthly_by_quadrant") or []
        total_months = sum(q.get("n_months", 0) for q in monthly_quad)
        if total_months == 0:
            st.info("**Placeholder data.** For full results: run `python fetch_data.py` then `python backtest.py` locally, commit `outputs/backtest_results.json`, and push to refresh this app.")

        window = bt.get("rolling_window_months", 60)
        st.caption(f"Rolling window: {window} months for percentile-based quadrant classification.")

        # Monthly by quadrant: table of avg return and avg drawdown per sector
        st.subheader("1. Monthly: Sector performance by quadrant")
        monthly_quad = bt.get("monthly_by_quadrant") or []
        for item in monthly_quad:
            q = item.get("quadrant", "")
            parts = q.split("_")
            label = config.QUADRANTS.get((parts[0], parts[1]), q) if len(parts) >= 2 else q
            with st.expander(f"**{q}** — {label} ({item.get('n_months', 0)} months)"):
                ret = item.get("avg_return") or {}
                dd = item.get("avg_drawdown") or {}
                df = pd.DataFrame({
                    "Avg monthly return (%)": [round(ret.get(t, 0) * 100, 2) for t in ret],
                    "Avg drawdown (%)": [round(dd.get(t, 0) * 100, 2) for t in dd],
                }, index=list(ret.keys()))
                st.dataframe(df, use_container_width=True)
                fav = bt.get("monthly_favorite_unfavorite") or {}
                fav_q = fav.get(q, {})
                if fav_q:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write("**Favorite by return:**", ", ".join(fav_q.get("favorite_by_return", [])))
                        st.write("**Unfavorite by return:**", ", ".join(fav_q.get("unfavorite_by_return", [])))
                    with c2:
                        st.write("**Favorite by drawdown (less risk):**", ", ".join(fav_q.get("favorite_by_drawdown", [])))
                        st.write("**Unfavorite by drawdown:**", ", ".join(fav_q.get("unfavorite_by_drawdown", [])))

        st.subheader("2. Quarterly: Sector performance by quadrant")
        quarterly_quad = bt.get("quarterly_by_quadrant") or []
        for item in quarterly_quad:
            q = item.get("quadrant", "")
            with st.expander(f"**{q}** ({item.get('n_quarters', 0)} quarters)"):
                ret = item.get("avg_return") or {}
                dd = item.get("avg_drawdown") or {}
                df = pd.DataFrame({
                    "Avg quarterly return (%)": [round(ret.get(t, 0) * 100, 2) for t in ret],
                    "Avg drawdown (%)": [round(dd.get(t, 0) * 100, 2) for t in dd],
                }, index=list(ret.keys()))
                st.dataframe(df, use_container_width=True)
                fav = bt.get("quarterly_favorite_unfavorite") or {}
                fav_q = fav.get(q, {})
                if fav_q:
                    st.write("**Favorite by return:**", ", ".join(fav_q.get("favorite_by_return", [])))
                    st.write("**Unfavorite by return:**", ", ".join(fav_q.get("unfavorite_by_return", [])))

        # Quadrant history over time (chart)
        st.subheader("3. Quadrant history (monthly)")
        hist = bt.get("quadrant_history_monthly") or []
        if hist:
            df_h = pd.DataFrame(hist)
            if "date" in df_h.columns:
                df_h["date"] = pd.to_datetime(df_h["date"])
                quad_order = df_h["Quadrant"].unique()
                fig = go.Figure()
                for q in quad_order:
                    mask = df_h["Quadrant"] == q
                    fig.add_trace(go.Scatter(
                        x=df_h.loc[mask, "date"],
                        y=df_h.loc[mask, "VIX_ratio"],
                        mode="markers",
                        name=q,
                        marker=dict(size=6),
                    ))
                fig.update_layout(
                    title="VIX ratio over time (colored by quadrant)",
                    xaxis_title="Date",
                    yaxis_title="VIX 1M/3M ratio",
                    height=400,
                    legend=dict(orientation="h"),
                )
                st.plotly_chart(fig, use_container_width=True)

    else:
        st.header("AIG Investment Clock: Current Status")
        st.caption("Month-end X (VIX1M/3M) and Y (HY–IG spread) with current regime.")

        if not bt or not bt.get("current_regime"):
            if ind is not None and not ind.empty:
                st.info("Run `python backtest.py` to compute current regime.")
            else:
                st.warning("Run `python fetch_data.py` then `python backtest.py` to see current regime.")
            return

        cur = bt["current_regime"]
        st.subheader("Current regime (month-end)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Date", cur.get("date", "—"))
            st.metric("VIX 1M/3M ratio", f"{cur.get('VIX_ratio', 0):.4f}")
            st.metric("X (Stress horizon)", cur.get("VIX_class", "—"))
        with col2:
            st.metric("HY–IG spread (bps)", f"{cur.get('HY_IG_spread', 0):.2f}")
            st.metric("Y (Credit stress)", cur.get("HYIG_class", "—"))
        with col3:
            st.metric("Quadrant", cur.get("Quadrant", "—"))
            st.success("**" + cur.get("QuadrantLabel", "") + "**")

        st.subheader("Quadrant interpretation")
        st.markdown("""
        | Quadrant | Meaning | Equity implication |
        |----------|---------|--------------------|
        | Low VIX, Easy credit | Stable expansion | Risk-on |
        | Low VIX, Tight credit | Late cycle | Selective |
        | High VIX, Easy credit | Shock regime | Buy recovery |
        | High VIX, Tight credit | Structural stress | Capital preservation |
        """)

        if ind is not None and not ind.empty:
            st.subheader("X & Y over time (monthly)")
            ind_m = ind[["VIX_RATIO", "HY_IG_SPREAD"]].dropna()
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(x=ind_m.index, y=ind_m["VIX_RATIO"], name="VIX 1M/3M (X)", line=dict(color="#667eea")),
                secondary_y=False,
            )
            fig.add_trace(
                go.Scatter(x=ind_m.index, y=ind_m["HY_IG_SPREAD"], name="HY–IG spread (Y)", line=dict(color="#28a745")),
                secondary_y=True,
            )
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="VIX ratio", secondary_y=False)
            fig.update_yaxes(title_text="HY–IG spread (bps)", secondary_y=True)
            fig.update_layout(height=450, title="AIG Investment Clock indicators")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.caption("AIG Research | RLIC Refine Demo | Data: FRED (VIXCLS, VXVCLS, BAMLH0A0HYM2, BAMLC0A0CM) & yfinance (sector ETFs)")


if __name__ == "__main__":
    main()
