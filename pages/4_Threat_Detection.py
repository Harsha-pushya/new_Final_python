import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from lib.crud_ui import render_crud, render_csv_files
from lib.csv_manager import AppError
from lib.managers import ThreatManager
from lib.theme import (
    AMBER,
    BLUE,
    COLORS,
    GREEN,
    LINE,
    PANEL,
    PURPLE,
    RED,
    TEAL,
    apply_theme,
    bar,
    metrics,
    pie,
    search_table,
    show,
)

st.set_page_config(page_title="Threat Detection · SNAKEFLOW", page_icon="🔒", layout="wide")
apply_theme()

st.title("🔒 Threat Detection Analysis")
st.caption("Network threat alerts — types, severity, timing and correlations. Owner: Rithesh. CSV: data/threat_detection.csv")

manager = ThreatManager()
try:
    manager.load()
except AppError as exc:
    st.error(str(exc))
    st.stop()

raw = manager.data
protocols = sorted(raw["Protocol"].dropna().astype(str).unique().tolist())
sources = sorted(raw["Source Type"].dropna().astype(str).unique().tolist())
threats = sorted(raw["Threat Type"].dropna().astype(str).unique().tolist())
severities = ["Low", "Medium", "High", "Critical"]
for s in raw["Severity"].dropna().astype(str).unique():
    if s not in severities:
        severities.append(s)
statuses = sorted(raw["Status"].dropna().astype(str).unique().tolist())

render_crud(
    manager,
    fields=[
        {"name": "Hour", "label": "Hour", "kind": "int"},
        {"name": "Protocol", "label": "Protocol", "kind": "select", "options": protocols},
        {"name": "Dest Port", "label": "Dest Port", "kind": "int"},
        {"name": "Packets", "label": "Packets", "kind": "int"},
        {"name": "Bytes", "label": "Bytes", "kind": "int"},
        {"name": "Duration", "label": "Duration", "kind": "int"},
        {"name": "Source Type", "label": "Source Type", "kind": "select", "options": sources},
        {"name": "Threat Type", "label": "Threat Type", "kind": "select", "options": threats},
        {"name": "Severity", "label": "Severity", "kind": "select", "options": severities},
        {"name": "Status", "label": "Status", "kind": "select", "options": statuses},
        {"name": "Threat Score", "label": "Threat Score", "kind": "float"},
        {"name": "Is Attack", "label": "Is Attack (0/1)", "kind": "int"},
    ],
    key_prefix="threat",
)

df = manager.visualization_frame()
counts = df["Threat Type"].value_counts()

st.header("📊 Overview Metrics")
metrics(
    [
        ("Total Alerts", f"{len(df):,}"),
        ("Threat Types", str(df["Threat Type"].nunique())),
        ("Attack Rate", f"{df['Is Attack'].mean() * 100:.1f}%"),
        ("Avg Threat Score", f"{df['Threat Score'].mean():.1f}"),
    ]
)

st.header("🔍 Data Exploration")
t1, t2, t3 = st.tabs(["📄 Preview", "📐 Statistics", "📓 Download Code File"])
with t1:
    st.dataframe(df.head(20), use_container_width=True, height=360)
    st.caption(f"{df.shape[0]:,} rows × {df.shape[1]} columns")
with t2:
    st.dataframe(df.describe().T, use_container_width=True)
with t3:
    if os.path.exists("rithesh.ipynb"):
        with open("rithesh.ipynb", "rb") as f:
            st.download_button(
                label="⬇️ Download Code File",
                data=f,
                file_name="rithesh.ipynb",
                mime="application/x-ipynb+json",
                key="dl_threat_tab",
            )

c1, c2 = st.columns(2)
c1.dataframe(counts.rename("Count").reset_index(), use_container_width=True)
c2.dataframe(df["Severity"].value_counts().rename("Count").reset_index(), use_container_width=True)

search_table(df, "threat", "Threat Detection Logs Dataset")
st.divider()

st.header("📈 Matplotlib Charts")
c3, c4 = st.columns(2)
with c3:
    bar(counts.index, counts.values, "Threat Type Count", color=PURPLE)
with c4:
    pie(counts.index, counts.values, "Threat Type Share")

by_hour = df["Hour"].value_counts().sort_index()
bar(by_hour.index, by_hour.values, "Alerts by Hour of Day", BLUE, figure=(10, 4))

status_counts = df["Status"].value_counts()
bar(status_counts.index, status_counts.values, "Alert Handling Status", TEAL, horizontal=True)

st.divider()
st.header("🔬 Seaborn Charts")
c5, c6 = st.columns(2)
with c5:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(
        x="Severity",
        hue="Severity",
        data=df,
        order=["Low", "Medium", "High", "Critical"],
        palette=[GREEN, AMBER, RED, PURPLE],
        legend=False,
        ax=ax,
    )
    show("Severity Distribution")
with c6:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(
        x="Threat Type",
        y="Threat Score",
        hue="Threat Type",
        data=df,
        palette=COLORS[: len(counts)],
        legend=False,
        ax=ax,
    )
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    show("Threat Score by Type")

fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(
    df[["Hour", "Packets", "Bytes", "Duration", "Threat Score", "Is Attack"]].corr(),
    annot=True,
    cmap="RdBu_r",
    center=0,
    fmt=".2f",
    ax=ax,
)
show("Feature Correlation")

st.divider()
st.header("🛡️ Severity Distribution by Threat Type")
fig, ax = plt.subplots(figsize=(9, 4.8))
sns.countplot(
    x="Threat Type",
    hue="Severity",
    data=df,
    hue_order=["Low", "Medium", "High", "Critical"],
    palette=[GREEN, AMBER, RED, PURPLE],
    ax=ax,
)
plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
ax.legend(title="Severity Tier", facecolor=PANEL, edgecolor=LINE)
show("Severity Breakdown Across Threat Categories")

st.divider()
render_csv_files(manager, "threat")

st.divider()
if os.path.exists("rithesh.ipynb"):
    with open("rithesh.ipynb", "rb") as f:
        st.download_button(
            label="⬇️ Download Code File (rithesh.ipynb)",
            data=f,
            file_name="rithesh.ipynb",
            mime="application/x-ipynb+json",
            key="dl_threat_end",
        )
