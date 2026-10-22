import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from lib.crud_ui import render_crud, render_csv_files
from lib.csv_manager import AppError
from lib.managers import StateCrimeManager
from lib.theme import (
    AMBER,
    BLUE,
    COLORS,
    GREEN,
    LINE,
    PANEL,
    RED,
    TEAL,
    TEXT,
    apply_theme,
    bar,
    metrics,
    search_table,
    show,
)

st.set_page_config(page_title="State-Wise Crime · SNAKEFLOW", page_icon="🗺️", layout="wide")
apply_theme()

st.title("🗺️ State-Wise Cyber Crime")
st.caption("Cyber crime incidents across Indian states and union territories (2016–2018). Owner: Raju. CSV: data/cyber_crimes.csv")

manager = StateCrimeManager()
try:
    manager.load()
except AppError as exc:
    st.error(str(exc))
    st.stop()

raw = manager.data
categories = sorted(raw["Category"].dropna().astype(str).unique().tolist())
share_col = [c for c in raw.columns if "Percentage Share" in c][0]
pop_col = [c for c in raw.columns if "Population" in c][0]
rate_col = [c for c in raw.columns if c.startswith("Rate")][0]

render_crud(
    manager,
    fields=[
        {"name": "Category", "label": "Category", "kind": "select", "options": categories},
        {"name": "State/UT", "label": "State/UT", "kind": "text"},
        {"name": "2016", "label": "2016 cases", "kind": "float"},
        {"name": "2017", "label": "2017 cases", "kind": "float"},
        {"name": "2018", "label": "2018 cases", "kind": "float"},
        {"name": share_col, "label": share_col, "kind": "float"},
        {"name": pop_col, "label": pop_col, "kind": "float"},
        {"name": rate_col, "label": rate_col, "kind": "float"},
    ],
    key_prefix="state",
)

d = manager.analysis_frame()
YEARS = ["2016", "2017", "2018"]

st.header("📊 Overview Metrics")
top_state = d.sort_values("2018", ascending=False).iloc[0]["State"]
metrics(
    [
        ("States / UTs", str(len(d))),
        ("Total 2018 Cases", f"{d['2018'].sum():,.0f}"),
        ("Avg Crime Rate", f"{d['Rate'].mean():.2f}"),
        ("Top State", top_state),
    ]
)

st.header("🔍 Data Exploration")
t1, t2, t3 = st.tabs(["📄 Preview", "📐 Statistics", "📓 Download Code File"])
with t1:
    st.dataframe(d, use_container_width=True)
    st.caption(f"{d.shape[0]} rows × {d.shape[1]} columns")
with t2:
    st.dataframe(d[YEARS + ["Share", "Population", "Rate"]].describe().T, use_container_width=True)
with t3:
    if os.path.exists("raju.ipynb"):
        with open("raju.ipynb", "rb") as f:
            st.download_button(
                label="⬇️ Download Code File",
                data=f,
                file_name="raju.ipynb",
                mime="application/x-ipynb+json",
                key="dl_state_tab",
            )

c1, c2 = st.columns(2)
c1.dataframe(d[YEARS].sum().rename("Total Cases").reset_index(), use_container_width=True)
c2.dataframe(d["Type"].value_counts().rename("Count").reset_index(), use_container_width=True)

search_table(d, "state", "State-Wise Crime Dataset")
st.divider()

st.header("📈 Matplotlib Charts")
c3, c4 = st.columns(2)
with c3:
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(YEARS, d[YEARS].sum().values, color=[BLUE, GREEN, AMBER], width=0.5)
    ax.set_ylabel("Cases")
    show("Total Cases by Year")
with c4:
    top10 = d.sort_values("2018", ascending=False).head(10)
    bar(top10["State"], top10["2018"], "Top 10 States — 2018", AMBER, horizontal=True, figure=(8, 4))

top_rate = d.sort_values("Rate", ascending=False).head(12)
bar(
    top_rate["State"],
    top_rate["Rate"],
    "Crime Rate per Lakh Population (2018)",
    RED,
    horizontal=True,
    figure=(10, 5),
)

trend = d.sort_values("2018", ascending=False).head(5)
fig, ax = plt.subplots(figsize=(9, 5))
for _, row in trend.iterrows():
    ax.plot(YEARS, row[YEARS], marker="o", label=row["State"], linewidth=2)
ax.set_ylabel("Cases")
ax.legend(fontsize=8, facecolor=PANEL, edgecolor=LINE)
show("Yearly Trend — Top 5 States")

st.divider()
st.header("🔬 Seaborn Charts")
c5, c6 = st.columns(2)
with c5:
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.scatterplot(
        x="Population",
        y="2018",
        hue="Type",
        data=d,
        s=70,
        palette=COLORS[: d["Type"].nunique()],
        ax=ax,
    )
    ax.legend(fontsize=8, facecolor=PANEL, edgecolor=LINE)
    show("Population vs 2018 Cases")
with c6:
    fig, ax = plt.subplots(figsize=(6, 6))
    sns.heatmap(
        d.set_index("State")[YEARS].head(12),
        annot=True,
        fmt=".0f",
        cmap="YlOrRd",
        ax=ax,
    )
    show("Cases Heatmap — Top 12")

fig, ax = plt.subplots(figsize=(7, 5))
sns.heatmap(
    d[YEARS + ["Share", "Population", "Rate"]].corr(),
    annot=True,
    cmap="coolwarm",
    center=0,
    fmt=".2f",
    ax=ax,
)
show("Feature Correlation")

st.divider()
st.header("📈 Regional Growth Trajectory")
d_growth = d.copy()
d_growth["Growth_%"] = (
    (d_growth["2018"] - d_growth["2016"]) / d_growth["2016"].replace(0, 1) * 100
)
top_growth = d_growth.sort_values("2018", ascending=False).head(10)
fig, ax = plt.subplots(figsize=(8.5, 4.5))
bars_g = ax.barh(
    top_growth["State"],
    top_growth["Growth_%"],
    color=TEAL,
    height=0.6,
)
ax.invert_yaxis()
ax.set_xlabel("Growth % (2016 to 2018)")
for bar_item in bars_g:
    w = bar_item.get_width()
    ax.text(
        w + 2,
        bar_item.get_y() + bar_item.get_height() / 2.0,
        f"{w:+.1f}%",
        va="center",
        fontsize=8,
        color=TEXT,
    )
show("Top 10 States: 3-Year Cyber Crime Growth Rate (%)")

st.divider()
render_csv_files(manager, "state")

st.divider()
if os.path.exists("raju.ipynb"):
    with open("raju.ipynb", "rb") as f:
        st.download_button(
            label="⬇️ Download Code File (raju.ipynb)",
            data=f,
            file_name="raju.ipynb",
            mime="application/x-ipynb+json",
            key="dl_state_end",
        )
