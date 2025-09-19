
# dashboard.py
import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from datetime import datetime, date

st.set_page_config(page_title="Transport Analytics Dashboard", layout="wide")

# -------------------------
# Helpers
# -------------------------
def find_column(df, candidates):
    """Return first matching column name in df for any candidate substring/alias (case-insensitive)."""
    if df is None or df.empty:
        return None
    cols = list(df.columns)
    for cand in candidates:
        for c in cols:
            if c and cand.lower() in c.lower():
                return c
    # Also prefer exact matches
    for cand in candidates:
        if cand in cols:
            return cand
    return None

@st.cache_data(ttl=60)
def load_data_from_api(api_url: str):
    """Fetch JSON from API and normalize to DataFrame. If fails, return empty DataFrame."""
    try:
        resp = requests.get(api_url, timeout=8)
        resp.raise_for_status()
        payload = resp.json()

        # handle dict-vs-list JSON shapes
        if isinstance(payload, dict):
            # common wrapper keys
            for k in ("data", "items", "results", "transports"):
                if k in payload and isinstance(payload[k], list):
                    payload = payload[k]
                    break
            else:
                # If it's a single record dict, convert to list
                payload = [payload]
        if not isinstance(payload, list):
            payload = list(payload)

        df = pd.json_normalize(payload)
        # Clean column names
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()

def try_numeric(series):
    return pd.to_numeric(series, errors="coerce")

def parse_dates(series):
    try:
        return pd.to_datetime(series, errors="coerce")
    except Exception:
        return pd.to_datetime(series.astype(str), errors="coerce")

# -------------------------
# UI: Configuration
# -------------------------
st.title("📦 Transport Analytics Dashboard")
st.markdown("Fetches transport logs from your FastAPI and provides filters, charts and export.")

with st.sidebar:
    st.header("Configuration")
    API_URL = st.text_input("API URL (GET endpoint returning list of records)", 
                           value="http://127.0.0.1:8000/get-transports")  # 🔹 updated for your API
    if st.button("Refresh data"):
        st.experimental_rerun()

# -------------------------
# Load data
# -------------------------
df = load_data_from_api(API_URL)

if df.empty:
    st.warning("No data fetched from the API (or API returned empty). Check the API URL or add data via your FastAPI.")
    st.info("You can still view raw JSON if available locally (put transport_data.csv in project folder).")
    try:
        local_df = pd.read_csv("transport_data.csv")
        st.success("Loaded fallback local file 'transport_data.csv'")
        df = local_df
    except Exception:
        st.stop()

# -------------------------
# Auto-detect important columns
# -------------------------
mode_candidates = ["recommended_mode", "mode", "transport_mode"]
weight_candidates = ["weight"]
distance_candidates = ["distance"]
date_candidates = ["created_at", "created", "timestamp", "date", "time"]

mode_col = find_column(df, mode_candidates)
weight_col = find_column(df, weight_candidates)
distance_col = find_column(df, distance_candidates)
date_col = find_column(df, date_candidates)

# Column mapping UI
st.sidebar.header("Column mapping (auto-detected)")
all_columns = ["(none)"] + list(df.columns)
mode_col = st.sidebar.selectbox("Mode column", all_columns, index=(all_columns.index(mode_col) if mode_col in all_columns else 0))
weight_col = st.sidebar.selectbox("Weight column", all_columns, index=(all_columns.index(weight_col) if weight_col in all_columns else 0))
distance_col = st.sidebar.selectbox("Distance column", all_columns, index=(all_columns.index(distance_col) if distance_col in all_columns else 0))
date_col = st.sidebar.selectbox("Date column", all_columns, index=(all_columns.index(date_col) if date_col in all_columns else 0))

mode_col = None if mode_col == "(none)" else mode_col
weight_col = None if weight_col == "(none)" else weight_col
distance_col = None if distance_col == "(none)" else distance_col
date_col = None if date_col == "(none)" else date_col

# -------------------------
# Prepare DataFrame
# -------------------------
working = df.copy()

for c in working.select_dtypes(include=["object"]).columns:
    working[c] = working[c].astype(str).str.strip()

if weight_col:
    working[weight_col] = try_numeric(working[weight_col])
if distance_col:
    working[distance_col] = try_numeric(working[distance_col])
if date_col:
    working[date_col] = parse_dates(working[date_col])

# -------------------------
# Filters UI
# -------------------------
st.sidebar.header("Filters")
filters = {}

# Mode filter
if mode_col and mode_col in working.columns:
    all_modes = working[mode_col].dropna().astype(str).unique().tolist()
    all_modes.sort()
    selected_modes = st.sidebar.multiselect("Select modes", all_modes, default=all_modes)
    filters["mode_mask"] = working[mode_col].astype(str).isin(selected_modes)
else:
    filters["mode_mask"] = pd.Series([True]*len(working))

# Weight filter
if weight_col and weight_col in working.columns:
    min_w, max_w = int(working[weight_col].min(skipna=True) or 0), int(working[weight_col].max(skipna=True) or 0)
    weight_range = (min_w, max_w) if min_w == max_w else st.sidebar.slider("Weight range", min_w, max_w, (min_w, max_w))
    filters["weight_mask"] = working[weight_col].between(weight_range[0], weight_range[1], inclusive="both")
else:
    filters["weight_mask"] = pd.Series([True]*len(working))

# Distance filter
if distance_col and distance_col in working.columns:
    min_d, max_d = int(working[distance_col].min(skipna=True) or 0), int(working[distance_col].max(skipna=True) or 0)
    distance_range = (min_d, max_d) if min_d == max_d else st.sidebar.slider("Distance range", min_d, max_d, (min_d, max_d))
    filters["distance_mask"] = working[distance_col].between(distance_range[0], distance_range[1], inclusive="both")
else:
    filters["distance_mask"] = pd.Series([True]*len(working))

# Date filter
if date_col and date_col in working.columns:
    min_date, max_date = working[date_col].dropna().min(), working[date_col].dropna().max()
    if pd.notna(min_date) and pd.notna(max_date):
        d0 = st.sidebar.date_input("Start date", value=min_date.date())
        d1 = st.sidebar.date_input("End date", value=max_date.date())
        mask_date = working[date_col].apply(lambda x: x.date() if pd.notna(x) else None)
        filters["date_mask"] = mask_date.between(d0, d1)
    else:
        filters["date_mask"] = pd.Series([True]*len(working))
else:
    filters["date_mask"] = pd.Series([True]*len(working))

# Global text search
search_text = st.sidebar.text_input("Search (global text across all columns)")
if search_text:
    text_mask = pd.Series(False, index=working.index)
    for c in working.columns:
        if working[c].dtype == object or working[c].dtype.name.startswith("string"):
            text_mask |= working[c].astype(str).str.contains(search_text, case=False, na=False)
    filters["text_mask"] = text_mask
else:
    filters["text_mask"] = pd.Series([True]*len(working))

# Apply mask
combined_mask = pd.Series(True, index=working.index)
for m in filters.values():
    combined_mask &= m.fillna(False)

filtered_df = working[combined_mask].reset_index(drop=True)

# -------------------------
# Main page layout
# -------------------------
st.markdown("## 📋 Records")
st.write(f"Showing **{len(filtered_df)}** records (filtered from {len(working)})")
st.dataframe(filtered_df, use_container_width=True, height=600)

csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download CSV", csv, "transport_data_filtered.csv", "text/csv")

# -------------------------
# Analytics
# -------------------------
st.markdown("## 📊 Analytics")

# Mode distribution
mode_counts = filtered_df[mode_col].value_counts() if mode_col and mode_col in filtered_df.columns else pd.Series(dtype=int)

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Mode distribution (bar)")
    st.bar_chart(mode_counts) if not mode_counts.empty else st.info("No values to plot.")
with col2:
    st.subheader("Mode distribution (pie)")
    if not mode_counts.empty:
        fig, ax = plt.subplots(figsize=(4,4))
        ax.pie(mode_counts.values, labels=mode_counts.index, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
    else:
        st.info("Pie chart not available.")

# Time-series
if date_col and date_col in filtered_df.columns:
    st.subheader("Time trend")
    if not filtered_df[date_col].dropna().empty:
        ts = filtered_df.copy()
        ts["__date"] = pd.to_datetime(ts[date_col], errors="coerce").dt.date
        ts_group = ts.groupby("__date").size().rename("count")
        st.line_chart(ts_group)
    else:
        st.info("Date column present but no valid values.")
else:
    st.info("No date column mapped — time-series unavailable.")

# -------------------------
# Summary metrics
# -------------------------
st.markdown("## 📌 Summary")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total records", len(filtered_df))
c2.metric("Unique modes", int(filtered_df[mode_col].nunique() if mode_col in filtered_df.columns else 0))
c3.metric("Average weight", round(filtered_df[weight_col].dropna().mean(), 2) if weight_col in filtered_df.columns else "—")
c4.metric("Average distance", round(filtered_df[distance_col].dropna().mean(), 2) if distance_col in filtered_df.columns else "—")

# -------------------------
# Debug / raw view
# -------------------------
with st.expander("Debug: raw data & columns"):
    st.write("Detected columns:", list(df.columns))
    st.write("Working DataFrame (first rows):")
    st.dataframe(working.head(10), use_container_width=True)
    st.write("Filtered DataFrame (first rows):")
    st.dataframe(filtered_df.head(10), use_container_width=True)