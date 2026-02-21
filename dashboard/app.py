import sys
import os
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

from src.config.settings import Config

st.set_page_config(page_title="Stock ETL Dashboard", layout="wide")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def load_runs():
    cfg = Config()
    engine = create_engine(cfg.DATABASE_URL())
    with engine.connect() as conn:
        # Table may not exist yet if ETL has never run
        exists = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'etl_runs')"
        )).scalar()
        if not exists:
            return pd.DataFrame()
        df = pd.read_sql(
            text("SELECT * FROM etl_runs ORDER BY run_at DESC"),
            conn,
        )
    df["run_at"] = pd.to_datetime(df["run_at"], utc=True)
    df["duration_secs"] = pd.to_numeric(df["duration_secs"], errors="coerce")
    df["rows_loaded"] = pd.to_numeric(df["rows_loaded"], errors="coerce")
    return df


@st.cache_data(ttl=30)
def load_stock_data():
    cfg = Config()
    engine = create_engine(cfg.DATABASE_URL())
    with engine.connect() as conn:
        df = pd.read_sql(
            text("SELECT * FROM stock_prices ORDER BY symbol, timestamp"),
            conn,
        )
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["daily_return"] = (
        df.sort_values(["symbol", "timestamp"])
        .groupby("symbol")["close"]
        .pct_change()
        .mul(100)
        .round(4)
    )
    return df


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

try:
    runs_df = load_runs()
    stock_df = load_stock_data()
    db_ok = True
    db_error = None
except Exception as exc:
    db_ok = False
    db_error = str(exc)
    runs_df = pd.DataFrame()
    stock_df = pd.DataFrame()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("Stock ETL Dashboard")

if not db_ok:
    st.error(
        f"Could not connect to the database.\n\n`{db_error}`\n\n"
        "Make sure Docker is running (`docker-compose up -d`) and the ETL has been executed (`python main.py`)."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_stats, tab_table = st.tabs(["ETL Statistics", "Data Table"])

# ===========================================================================
# TAB 1 — ETL Run Statistics
# ===========================================================================

with tab_stats:

    if runs_df.empty:
        st.info("No ETL runs recorded yet. Run `python main.py` to populate this dashboard.")
    else:
        total_runs = len(runs_df)
        successful = (runs_df["status"] == "success").sum()
        last_run = runs_df["run_at"].max()
        total_rows = runs_df["rows_loaded"].sum()

        # KPI cards
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Runs", total_runs)
        k2.metric("Successful", f"{successful} / {total_runs}")
        k3.metric("Total Rows Loaded", f"{int(total_rows):,}")
        k4.metric("Last Run", last_run.strftime("%Y-%m-%d %H:%M"))

        st.divider()

        # Rows loaded per run bar chart
        st.subheader("Rows Loaded per Run")
        chart_df = runs_df.sort_values("run_at")
        fig_rows = px.bar(
            chart_df,
            x="run_at",
            y="rows_loaded",
            color="status",
            color_discrete_map={"success": "#636EFA", "error": "#EF553B", "no_data": "#FFA15A"},
            labels={"run_at": "Run Time", "rows_loaded": "Rows Loaded", "status": "Status"},
        )
        fig_rows.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_rows, use_container_width=True)

        # Duration per run line chart
        st.subheader("ETL Duration (seconds)")
        fig_dur = px.line(
            chart_df[chart_df["status"] == "success"],
            x="run_at",
            y="duration_secs",
            markers=True,
            labels={"run_at": "Run Time", "duration_secs": "Duration (s)"},
        )
        fig_dur.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_dur, use_container_width=True)

        st.divider()

        # Full run log table
        st.subheader("Run Log")
        display = runs_df[["run_at", "symbols", "rows_loaded", "duration_secs", "status", "error_message"]].rename(
            columns={
                "run_at": "Run At",
                "symbols": "Symbols",
                "rows_loaded": "Rows Loaded",
                "duration_secs": "Duration (s)",
                "status": "Status",
                "error_message": "Error",
            }
        )
        st.dataframe(display, use_container_width=True, hide_index=True)


# ===========================================================================
# TAB 2 — Data Table
# ===========================================================================

with tab_table:

    st.subheader("Browse Stock Data")

    if stock_df.empty:
        st.info("No stock data loaded. Run `python main.py` first.")
    else:
        col_filter, col_date = st.columns([1, 2])

        with col_filter:
            selected_symbols = st.multiselect(
                "Filter by Symbol",
                options=sorted(stock_df["symbol"].unique().tolist()),
                default=sorted(stock_df["symbol"].unique().tolist()),
            )

        with col_date:
            min_ts = stock_df["timestamp"].min()
            max_ts = stock_df["timestamp"].max()
            min_date = datetime.date(min_ts.year, min_ts.month, min_ts.day)
            max_date = datetime.date(max_ts.year, max_ts.month, max_ts.day)
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )

        filtered = stock_df[stock_df["symbol"].isin(selected_symbols)].copy()
        filtered["_date"] = filtered["timestamp"].dt.date
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start, end = date_range
            filtered = filtered[(filtered["_date"] >= start) & (filtered["_date"] <= end)]

        display_cols = ["symbol", "timestamp", "open", "high", "low", "close", "volume", "daily_return"]
        display_cols = [c for c in display_cols if c in filtered.columns]

        st.caption(f"{len(filtered):,} rows")
        st.dataframe(
            filtered[display_cols].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
        )
