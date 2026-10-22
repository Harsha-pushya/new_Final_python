"""Shared dark dashboard theme and chart helpers (kept from original app)."""

from __future__ import annotations

import matplotlib.pyplot as plt
import streamlit as st

BG = "#0c1017"
PANEL = "#151b24"
CARD = "#18202c"
LINE = "#253244"
TEXT = "#d8e2ec"
DIM = "#8da2b5"
TITLE = "#f1f5f9"

BLUE = "#38bdf8"
GREEN = "#00d26a"
AMBER = "#fbbf24"
RED = "#f87171"
PURPLE = "#a78bfa"
TEAL = "#2dd4bf"
ROSE = "#fb7185"
COLORS = [BLUE, GREEN, AMBER, RED, PURPLE, TEAL, ROSE, "#94a3b8"]

CSS = """
    <style>
    .stApp {
        background-color: #0c1017;
        color: #d8e2ec;
    }
    h1 {
        font-size: 1.68rem !important;
        font-weight: 700 !important;
        color: #f1f5f9 !important;
        margin-bottom: 0.35rem !important;
        border-left: 3px solid #38bdf8;
        padding-left: 10px;
    }
    h2 {
        font-size: 1.18rem !important;
        font-weight: 600 !important;
        color: #f1f5f9 !important;
        margin-top: 1.4rem !important;
        margin-bottom: 0.8rem !important;
        border-bottom: 1px solid #253244;
        padding-bottom: 6px;
    }
    h3 {
        font-size: 1.0rem !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #121721 !important;
        border-right: 1px solid #253244 !important;
    }
    [data-testid="stSidebar"] h1 {
        font-size: 1.25rem !important;
        color: #f1f5f9 !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 0 !important;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.88rem;
        transition: background-color 0.15s ease;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background-color: #1a222f;
    }
    [data-testid="stMetric"] {
        background-color: #151b24;
        border: 1px solid #253244;
        border-left: 3px solid #38bdf8;
        border-radius: 6px;
        padding: 12px 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }
    [data-testid="stMetric"] label {
        color: #8da2b5 !important;
        font-size: 0.8rem !important;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-weight: 700;
        font-size: 1.55rem !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: transparent;
        border-bottom: 1px solid #253244;
        padding: 0;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        font-size: 0.86rem;
        padding: 8px 14px;
        color: #8da2b5;
        border-radius: 4px 4px 0 0;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        color: #38bdf8 !important;
        font-weight: 600;
        border-bottom: 2px solid #38bdf8 !important;
        background: transparent !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #253244;
        border-radius: 6px;
    }
    .card-box {
        background-color: #151b24;
        border: 1px solid #253244;
        border-radius: 6px;
        padding: 14px 16px;
        margin-bottom: 12px;
    }
    .tag-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .tag-blue { background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .tag-green { background: rgba(0, 210, 106, 0.12); color: #00d26a; border: 1px solid rgba(0, 210, 106, 0.3); }
    .tag-amber { background: rgba(251, 191, 36, 0.12); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.3); }
    .tag-purple { background: rgba(167, 139, 250, 0.12); color: #a78bfa; border: 1px solid rgba(167, 139, 250, 0.3); }
    .stButton > button {
        background-color: #1e2634;
        color: #d8e2ec;
        border: 1px solid #2d3b4f;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
        padding: 6px 14px;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #263346;
        color: #38bdf8;
        border-color: #38bdf8;
    }
    code {
        background-color: #1a222e !important;
        color: #38bdf8 !important;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85em;
        border: 1px solid #253244;
    }
    hr {
        border-color: #202a3a;
        margin: 1.5rem 0;
    }
    </style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    plt.rcParams.update(
        {
            "figure.facecolor": PANEL,
            "axes.facecolor": PANEL,
            "axes.edgecolor": LINE,
            "axes.labelcolor": DIM,
            "text.color": TEXT,
            "xtick.color": DIM,
            "ytick.color": DIM,
            "grid.color": "#1e2736",
            "axes.grid": True,
            "grid.alpha": 0.5,
            "font.family": "sans-serif",
            "font.size": 9.5,
            "axes.titlesize": 11,
            "axes.titleweight": "600",
            "axes.titlecolor": TITLE,
            "figure.dpi": 110,
            "figure.autolayout": True,
        }
    )


def show(title=""):
    ax = plt.gca()
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["left"].set_color(LINE)
    ax.spines["bottom"].set_color(LINE)
    if title:
        ax.set_title(title, color=TITLE, pad=10, fontweight="600")
    plt.tight_layout()
    st.pyplot(plt.gcf(), use_container_width=True)
    plt.close()


def bar(labels, values, title, color=BLUE, horizontal=False, figure=(8, 4)):
    fig, ax = plt.subplots(figsize=figure)
    pos = range(len(labels))
    if horizontal:
        ax.barh(list(pos), values, color=color, height=0.62)
        ax.set_yticks(list(pos))
        ax.set_yticklabels([str(v) for v in labels], fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel("Value", color=DIM)
    else:
        ax.bar(list(pos), values, color=color, width=0.62)
        ax.set_xticks(list(pos))
        ax.set_xticklabels([str(v) for v in labels], rotation=25, ha="right", fontsize=9)
        ax.set_ylabel("Value", color=DIM)
    show(title)


def pie(labels, values, title):
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, percents = ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        colors=COLORS[: len(values)],
        wedgeprops={"width": 0.48, "edgecolor": PANEL, "linewidth": 2},
        pctdistance=0.75,
    )
    for t in texts:
        t.set_fontsize(8.5)
        t.set_color(TEXT)
    for p in percents:
        p.set_fontsize(8.5)
        p.set_color("#ffffff")
        p.set_weight("600")
    show(title)


def line(labels, values, title, color=BLUE):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(labels, values, marker="o", color=color, linewidth=2, markersize=5)
    ax.set_ylabel("Value", color=DIM)
    ax.grid(True, linestyle="--", alpha=0.3)
    show(title)


def metrics(rows):
    cols = st.columns(len(rows))
    for col, (label, value) in zip(cols, rows):
        col.metric(label, value)


def search_table(df, key, dataset_name=""):
    st.subheader(f"🔍 Search & Filter — {dataset_name}" if dataset_name else "🔍 Search & Filter Records")
    text = st.text_input(
        "Enter any element or value to search (e.g. text, port, status, IP, number):",
        key=f"text_{key}",
        placeholder="Type any element to search records...",
    )
    if not text or not text.strip():
        st.caption(
            f"Enter an element above to search across all {df.shape[0]:,} rows and {df.shape[1]} columns of this dataset."
        )
        return

    query = text.strip()
    cells = df.astype(str)
    matches = cells.apply(lambda c: c.str.contains(query, case=False, na=False))
    matching_rows = matches.any(axis=1)
    hit_columns = list(df.columns[matches.any(axis=0)])

    if not matching_rows.any():
        st.warning(f"No records found containing '{query}' in this dataset.")
        return

    total_hits = int(matching_rows.sum())
    st.markdown(
        f"<span style='color:{GREEN}; font-weight:600;'>✓ Found {total_hits:,} rows</span> containing <code>{query}</code> across <b>{len(hit_columns)}</b> column(s): <i>{', '.join(hit_columns[:8])}{'...' if len(hit_columns) > 8 else ''}</i>",
        unsafe_allow_html=True,
    )

    col_choice = st.selectbox(
        "Select Column to Display (or choose 'All Columns'):",
        ["All Columns"] + list(df.columns),
        key=f"col_choice_{key}",
    )

    if col_choice == "All Columns":
        st.caption(f"Displaying all {df.shape[1]} columns in {total_hits:,} selected rows:")
        st.dataframe(df.loc[matching_rows].head(300), use_container_width=True)
    else:
        st.caption(f"Displaying column '{col_choice}' in {total_hits:,} selected rows:")
        st.dataframe(df.loc[matching_rows, [col_choice]].head(300), use_container_width=True)
        with st.expander(f"📄 View all {df.shape[1]} columns in these selected rows"):
            ordered_cols = [col_choice] + [c for c in df.columns if c != col_choice]
            st.dataframe(df.loc[matching_rows, ordered_cols].head(300), use_container_width=True)
