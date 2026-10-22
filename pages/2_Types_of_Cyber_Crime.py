import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import streamlit as st

from lib.crud_ui import render_crud, render_csv_files
from lib.csv_manager import AppError
from lib.managers import CrimeTypeManager
from lib.theme import (
    AMBER,
    BLUE,
    COLORS,
    GREEN,
    LINE,
    PANEL,
    RED,
    TEXT,
    apply_theme,
    bar,
    line,
    metrics,
    pie,
    search_table,
    show,
)

st.set_page_config(page_title="Cyber Crime Types · SNAKEFLOW", page_icon="📑", layout="wide")
apply_theme()

st.title("📑 Types of Cyber Crime")
st.caption("Crime categories, yearly trends, risk levels and financial impact. Owner: Abhinav. CSV: data/types_of_cybercrime.csv")

manager = CrimeTypeManager()
try:
    manager.load()
except AppError as exc:
    st.error(str(exc))
    st.stop()

df_raw = manager.data
categories = sorted(df_raw["Category"].dropna().astype(str).unique().tolist())
risks = ["Low", "Medium", "High"]
for r in df_raw["Risk Level"].dropna().astype(str).unique():
    if r not in risks:
        risks.append(r)

render_crud(
    manager,
    fields=[
        {"name": "Crime Type", "label": "Crime Type", "kind": "text"},
        {"name": "Category", "label": "Category", "kind": "select", "options": categories},
        {"name": "2016", "label": "2016 cases", "kind": "int"},
        {"name": "2017", "label": "2017 cases", "kind": "int"},
        {"name": "2018", "label": "2018 cases", "kind": "int"},
        {"name": "2019", "label": "2019 cases", "kind": "int"},
        {"name": "2020", "label": "2020 cases", "kind": "int"},
        {"name": "2021", "label": "2021 cases", "kind": "int"},
        {"name": "Percentage Share", "label": "Percentage Share", "kind": "float"},
        {"name": "Avg Loss Lakhs", "label": "Avg Loss Lakhs", "kind": "float"},
        {"name": "Risk Level", "label": "Risk Level", "kind": "select", "options": risks},
    ],
    key_prefix="crime",
)

df = manager.visualization_frame()
years = ["2016", "2017", "2018", "2019", "2020", "2021"]

st.header("📊 Overview Metrics")
metrics(
    [
        ("Crime Types", str(len(df))),
        ("Categories", str(df["Category"].nunique())),
        ("Total 2021 Cases", f"{df['2021'].sum():,}"),
        ("Avg Loss (Lakhs)", f"{df['Avg Loss Lakhs'].mean():.1f} ₹"),
    ]
)

st.header("🔍 Data Exploration")
t1, t2, t3 = st.tabs(["📄 Preview", "📐 Statistics", "📓 Download Code File"])
with t1:
    st.dataframe(df, use_container_width=True)
    st.caption(f"{df.shape[0]} rows × {df.shape[1]} columns")
with t2:
    st.dataframe(df.describe().T, use_container_width=True)
with t3:
    if os.path.exists("abhinab.ipynb"):
        with open("abhinab.ipynb", "rb") as f:
            st.download_button(
                label="⬇️ Download Code File",
                data=f,
                file_name="abhinab.ipynb",
                mime="application/x-ipynb+json",
                key="dl_crime_tab",
            )

c1, c2 = st.columns(2)
c1.dataframe(df["Category"].value_counts().rename("Count").reset_index(), use_container_width=True)
c2.dataframe(df["Risk Level"].value_counts().rename("Count").reset_index(), use_container_width=True)

search_table(df, "crime", "Types of Cyber Crime Dataset")
st.divider()

st.header("📈 Matplotlib Charts")
by_cases = df.sort_values("2021", ascending=False)
bar(by_cases["Crime Type"], by_cases["2021"], "2021 Cases by Crime Type", color=BLUE)

cat_sum = df.groupby("Category")["2021"].sum()
pie(cat_sum.index, cat_sum.values, "Category Share 2021")
line(years, df[years].sum().values, "Total Cases Over Years", RED)

cat_year = df.groupby("Category")[years].sum().T
fig, ax = plt.subplots(figsize=(9, 5))
bottom = np.zeros(len(years))
for cat, color in zip(cat_year.columns, COLORS):
    ax.bar(cat_year.index, cat_year[cat], bottom=bottom, label=cat, color=color)
    bottom += cat_year[cat].values
ax.legend(fontsize=8, facecolor=PANEL, edgecolor=LINE)
ax.set_ylabel("Cases")
show("Yearly Cases by Category")

st.divider()
st.header("🔬 Seaborn Charts")
c3, c4 = st.columns(2)
with c3:
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.countplot(
        x="Risk Level",
        hue="Risk Level",
        data=df,
        order=["Low", "Medium", "High"],
        palette=[GREEN, AMBER, RED],
        legend=False,
        ax=ax,
    )
    show("Risk Level Distribution")
with c4:
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.scatterplot(
        x="2021",
        y="Avg Loss Lakhs",
        hue="Category",
        data=df,
        s=80,
        palette=COLORS[: df["Category"].nunique()],
        ax=ax,
    )
    ax.legend(fontsize=8, facecolor=PANEL, edgecolor=LINE)
    show("Cases vs Financial Loss")

fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(
    df[years + ["Percentage Share", "Avg Loss Lakhs"]].corr(),
    annot=True,
    cmap="RdBu_r",
    center=0,
    fmt=".2f",
    ax=ax,
)
show("Feature Correlation")

st.divider()
st.header("💰 Financial Impact Analysis")
fig, ax = plt.subplots(figsize=(7, 4.2))
sns.barplot(
    x="Risk Level",
    y="Avg Loss Lakhs",
    hue="Risk Level",
    data=df,
    order=["Low", "Medium", "High"],
    palette=[GREEN, AMBER, RED],
    legend=False,
    ax=ax,
)
ax.set_ylabel("Average Loss (Lakhs ₹)")
for p in ax.patches:
    h = p.get_height()
    if not np.isnan(h) and h > 0:
        ax.annotate(
            f"₹ {h:.1f}L",
            (p.get_x() + p.get_width() / 2.0, h + 0.5),
            ha="center",
            fontsize=8.5,
            color=TEXT,
        )
show("Average Financial Loss by Risk Tier")

st.divider()
render_csv_files(manager, "crime")

st.divider()
if os.path.exists("abhinab.ipynb"):
    with open("abhinab.ipynb", "rb") as f:
        st.download_button(
            label="⬇️ Download Code File (abhinab.ipynb)",
            data=f,
            file_name="abhinab.ipynb",
            mime="application/x-ipynb+json",
            key="dl_crime_end",
        )
