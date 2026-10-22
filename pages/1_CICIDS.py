import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

from lib.crud_ui import render_crud, render_csv_files
from lib.csv_manager import AppError
from lib.managers import CICIDSManager
from lib.theme import (
    AMBER,
    BLUE,
    COLORS,
    GREEN,
    LINE,
    PANEL,
    PURPLE,
    RED,
    ROSE,
    TEAL,
    TEXT,
    apply_theme,
    bar,
    line,
    metrics,
    pie,
    search_table,
    show,
)

st.set_page_config(page_title="CICIDS · SNAKEFLOW", page_icon="🛡️", layout="wide")
apply_theme()

st.title("🛡️ CICIDS 2017 — Network Traffic Analysis")
st.caption("Attack patterns, packet behavior, port usage and flow characteristics powered by harsh_final_cicids.ipynb. Owner: Harsh. CSV: data/harsh_final_cicids.csv")

manager = CICIDSManager()
try:
    manager.load()
except AppError as exc:
    st.error(str(exc))
    st.stop()

attack_types = sorted(manager.data["Attack Type"].dropna().astype(str).unique().tolist()) or ["Normal Traffic"]
render_crud(
    manager,
    fields=[
        {"name": "Destination Port", "label": "Destination Port", "kind": "int"},
        {"name": "Flow Duration", "label": "Flow Duration", "kind": "float"},
        {"name": "Total Fwd Packets", "label": "Total Fwd Packets", "kind": "float"},
        {"name": "Average Packet Size", "label": "Average Packet Size", "kind": "float"},
        {"name": "Attack Type", "label": "Attack Type", "kind": "select", "options": attack_types},
    ],
    key_prefix="cicids",
)

df = manager.visualization_frame()
counts = df["Attack Type"].value_counts()
is_normal = df["Attack Type"] == "Normal Traffic"

st.header("📊 Overview Metrics")
metrics(
    [
        ("Total Records", f"{len(df):,}"),
        ("Attack Types", str(df["Attack Type"].nunique())),
        ("Attack Traffic", f"{(1 - is_normal.mean()) * 100:.1f}%"),
        ("Avg Packet Size", f"{df['Average Packet Size'].mean():.0f} B"),
    ]
)

st.header("🔍 Data Exploration")
t1, t2, t3, t4, t5 = st.tabs(
    [
        "📄 Preview",
        "📐 Statistics",
        "🎯 Attack Distribution",
        "🧹 Data Quality",
        "📓 Download Code File",
    ]
)

with t1:
    st.dataframe(df.head(20), use_container_width=True, height=360)
    st.caption(f"Dataset Dimensions: {df.shape[0]:,} rows × {df.shape[1]} columns")

with t2:
    st.dataframe(df.describe().T, use_container_width=True)

with t3:
    c1, c2 = st.columns(2)
    c1.dataframe(counts.rename("Count").reset_index(), use_container_width=True)
    c2.dataframe(
        (counts / counts.sum() * 100).round(2).rename("Percent (%)").reset_index(),
        use_container_width=True,
    )

with t4:
    c1, c2 = st.columns(2)
    c1.metric("Missing Values", int(df.isnull().sum().sum()))
    c1.metric("Duplicate Rows", int(df.duplicated().sum()))
    c2.metric("Total Columns", df.shape[1])
    c2.metric("Numeric Columns", len(df.select_dtypes("number").columns))

with t5:
    if os.path.exists("harsh_final_cicids.ipynb"):
        with open("harsh_final_cicids.ipynb", "rb") as f:
            st.download_button(
                label="⬇️ Download Code File",
                data=f,
                file_name="harsh_final_cicids.ipynb",
                mime="application/x-ipynb+json",
                key="dl_cicids_tab",
            )

search_table(df, "cicids", "CICIDS 2017 Dataset")
st.divider()

st.header("📈 Matplotlib Visualizations")
c1, c2 = st.columns(2)
with c1:
    bar(counts.index, counts.values, "Attack Type Count", color=BLUE)
with c2:
    pie(counts.index, counts.values, "Attack Type Share")

c3, c4 = st.columns(2)
with c3:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df["Flow Duration"], bins=40, color=GREEN)
    ax.set_xlabel("Flow Duration (µs)")
    ax.set_ylabel("Frequency")
    show("Flow Duration Histogram")
with c4:
    ports = df["Destination Port"].value_counts().head(10)
    bar(ports.index, ports.values, "Top 10 Destination Ports", BLUE, horizontal=True)

c_norm, c_size = st.columns(2)
with c_norm:
    label_counts = pd.Series({"Normal": is_normal.sum(), "Attack": (~is_normal).sum()})
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(label_counts.index, label_counts.values, color=[GREEN, RED], width=0.45)
    ax.set_ylabel("Count")
    for i, v in enumerate(label_counts.values):
        ax.text(i, v + 200, f"{v:,} ({(v/len(df)*100):.1f}%)", ha="center", color=TEXT, fontsize=9)
    show("Normal vs Attack Traffic")

with c_size:
    avg_size = df.groupby("Attack Type")["Average Packet Size"].mean().sort_values(ascending=False)
    line(avg_size.index, avg_size.values, "Average Packet Size by Attack Type", AMBER)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.scatter(df["Flow Duration"], df["Total Fwd Packets"], s=8, alpha=0.4, color=TEAL)
ax.set_xlabel("Flow Duration")
ax.set_ylabel("Total Forward Packets")
show("Flow Duration vs Forward Packets")

st.divider()
st.header("🔬 Seaborn Statistical Graphics")
c5, c6 = st.columns(2)
with c5:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(
        x="Attack Type",
        y="Average Packet Size",
        hue="Attack Type",
        data=df,
        palette=COLORS[: len(counts)],
        legend=False,
        ax=ax,
    )
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    show("Avg Packet Size by Attack Type")
with c6:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df["Flow Duration"], bins=35, kde=True, color=GREEN, ax=ax)
    show("Flow Duration with KDE")

c7, c8 = st.columns(2)
with c7:
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(
        df[["Flow Duration", "Total Fwd Packets", "Packet Length Mean", "Average Packet Size"]].corr(),
        annot=True,
        cmap="RdBu_r",
        center=0,
        fmt=".2f",
        ax=ax,
    )
    show("Feature Correlation")
with c8:
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.violinplot(
        x="Attack Type",
        y="Flow Packets/s",
        hue="Attack Type",
        data=df,
        palette=COLORS[: len(counts)],
        legend=False,
        inner="box",
        ax=ax,
    )
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    show("Flow Packets/s Distribution")

c9, c10 = st.columns(2)
with c9:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(
        x="Attack Type",
        hue="Attack Type",
        data=df,
        palette=COLORS[: len(counts)],
        legend=False,
        ax=ax,
    )
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    show("Attack Type Counts")
with c10:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(x=ports.index.astype(str), y=ports.values, color=AMBER, ax=ax)
    ax.set_xlabel("Port")
    ax.set_ylabel("Count")
    show("Top Ports")

c11, c12 = st.columns(2)
with c11:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.countplot(
        x="Destination Port",
        hue="Attack Type",
        data=df.head(5000),
        palette=COLORS[: len(counts)],
        ax=ax,
    )
    ax.legend(fontsize=8, facecolor=PANEL, edgecolor=LINE)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)
    show("Attack Type by Destination Port")
with c12:
    top5 = list(counts.index[:5])
    fig, ax = plt.subplots(figsize=(8, 5))
    for name, color in zip(top5, COLORS):
        sns.kdeplot(
            df.loc[df["Attack Type"] == name, "Packet Length Mean"],
            label=name,
            color=color,
            ax=ax,
        )
    ax.set_xlabel("Packet Length Mean")
    ax.legend(fontsize=8, facecolor=PANEL, edgecolor=LINE)
    show("Packet Length by Attack Type (KDE)")

st.divider()
st.header("⚡ Protocol & Flow Intrusion Dynamics")

c_add1, c_add2 = st.columns(2)
with c_add1:
    flag_cols = ["FIN Flag Count", "PSH Flag Count", "ACK Flag Count"]
    flags_mean = df.groupby("Attack Type")[flag_cols].mean()
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(flags_mean, annot=True, fmt=".3f", cmap="YlGnBu", ax=ax)
    show("TCP Flag Signatures (Mean FIN, PSH, ACK by Attack)")

with c_add2:
    fig, ax = plt.subplots(figsize=(8, 5))
    log_dur = np.log1p(df["Flow Duration"])
    sns.boxplot(
        x=df["Attack Type"],
        y=log_dur,
        hue=df["Attack Type"],
        palette="Spectral",
        legend=False,
        ax=ax,
    )
    ax.set_ylabel("log(Flow Duration + 1)")
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    show("Flow Duration Latency Profile (Log Scale)")

c_add3, c_add4 = st.columns(2)
with c_add3:
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(
        x="Attack Type",
        y="Flow Bytes/s",
        hue="Attack Type",
        data=df,
        estimator=np.mean,
        errorbar=None,
        palette="mako",
        legend=False,
        ax=ax,
    )
    ax.set_ylabel("Average Flow Bytes / s")
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    show("Network Throughput (Flow Bytes/s) by Attack Type")

with c_add4:
    lbl_series = np.where(df["Attack Type"] == "Normal Traffic", "Normal", "Attack")
    norm_metrics = df.groupby(lbl_series)[
        ["Flow Duration", "Total Fwd Packets", "Average Packet Size", "Idle Mean"]
    ].mean()
    norm_scaled = norm_metrics / norm_metrics.max()
    fig, ax = plt.subplots(figsize=(8, 5))
    norm_scaled.T.plot(
        kind="bar",
        ax=ax,
        color=[RED, GREEN],
        width=0.6,
    )
    ax.set_ylabel("Normalized Magnitude (0 - 1.0)")
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right", fontsize=9)
    ax.legend(title="Traffic Class", facecolor=PANEL, edgecolor=LINE)
    show("Normalized Metric Profile: Normal vs Malicious Traffic")

st.divider()
st.header("🎯 Deep Payload & Timing Characteristics")

c_extra1, c_extra2 = st.columns(2)
with c_extra1:
    win_mean = df.groupby("Attack Type")["Init_Win_bytes_forward"].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(win_mean.index, win_mean.values, color=BLUE, width=0.6)
    ax.set_ylabel("Mean Initial Window (Bytes)")
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    for i, v in enumerate(win_mean.values):
        ax.text(i, v + 400, f"{v:,.0f}", ha="center", fontsize=8, color=TEXT)
    show("TCP Initial Window Size (Init_Win_bytes_forward)")

with c_extra2:
    iat_log = np.log1p(df.groupby("Attack Type")["Flow IAT Mean"].mean().sort_values(ascending=False))
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(iat_log.index, iat_log.values, color=PURPLE, width=0.6)
    ax.set_ylabel("log(Mean Flow IAT + 1) [µs]")
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    for i, v in enumerate(iat_log.values):
        ax.text(i, v + 0.2, f"{v:.1f}", ha="center", fontsize=8, color=TEXT)
    show("Flow Inter-Arrival Time Dynamics (Log Scale IAT Mean)")

c_extra3, c_extra4 = st.columns(2)
with c_extra3:
    fwd_vol = df.groupby("Attack Type")["Total Length of Fwd Packets"].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(fwd_vol.index, fwd_vol.values, color=GREEN, width=0.6)
    ax.set_ylabel("Total Fwd Payload Length (Bytes)")
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    for i, v in enumerate(fwd_vol.values):
        ax.text(i, v + 35, f"{v:,.0f} B", ha="center", fontsize=8, color=TEXT)
    show("Forward Payload Volume by Attack Type")

with c_extra4:
    act_idle = np.log1p(df.groupby("Attack Type")[["Active Mean", "Idle Mean"]].mean())
    fig, ax = plt.subplots(figsize=(8, 4.8))
    act_idle.plot(kind="bar", ax=ax, color=[AMBER, ROSE], width=0.65)
    ax.set_ylabel("log(Duration + 1) [µs]")
    plt.setp(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
    ax.legend(title="State", facecolor=PANEL, edgecolor=LINE)
    show("Active vs Idle Connection Latency (Log Scale)")

st.divider()
render_csv_files(manager, "cicids")

st.divider()
if os.path.exists("harsh_final_cicids.ipynb"):
    with open("harsh_final_cicids.ipynb", "rb") as f:
        st.download_button(
            label="⬇️ Download Code File (harsh_final_cicids.ipynb)",
            data=f,
            file_name="harsh_final_cicids.ipynb",
            mime="application/x-ipynb+json",
            key="dl_cicids_end",
        )
