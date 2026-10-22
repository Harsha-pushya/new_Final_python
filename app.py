import os

import matplotlib

matplotlib.use("Agg")
import streamlit as st

from lib.theme import apply_theme, BLUE, GREEN, AMBER, RED, TITLE, DIM

st.set_page_config(
    page_title="SNAKEFLOW · Cyber Analysis Dashboard",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()

with st.sidebar:
    st.title("🐍 SNAKEFLOW")
    st.caption("Intrusion, Crime & Threat Intelligence")
    st.divider()
    st.markdown(
        """
        <div style='font-size:0.75rem; color:#8da2b5; line-height: 1.5;'>
            🐍 <b>Platform:</b> SNAKEFLOW<br/>
            📊 <b>Analysis:</b> Pandas · Seaborn<br/>
            🧩 <b>Pattern:</b> Input → CSV → Analyze → Visualize<br/>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.title("🐍 SNAKEFLOW — Cyber Threat Analysis")
st.caption(
    "A unified data-driven study of network traffic intrusions, cyber crime patterns, and threat detection logs. "
    "Core loop: Input data → Update CSV → Read / Analyze / View → Visualize."
)

st.header("👥 The Analyst Team")
team = [
    ("Harsh", "CICIDS 2017 network traffic analysis (harsh_final_cicids.ipynb) — page 1_CICIDS, CSV data/harsh_final_cicids.csv", BLUE, "🛡️"),
    ("Abhinav", "Types of cyber crime, category analysis (abhinab.ipynb) — page 2_Types_of_Cyber_Crime, CSV data/types_of_cybercrime.csv", GREEN, "📑"),
    ("Raju", "State-wise cyber crime, regional comparison (raju.ipynb) — page 3_State_Wise_Crime, CSV data/cyber_crimes.csv", AMBER, "🗺️"),
    ("Rithesh", "Threat detection, alert and severity analysis (rithesh.ipynb) — page 4_Threat_Detection, CSV data/threat_detection.csv", RED, "🔒"),
]
cols = st.columns(4)
for col, (name, work, color, sym) in zip(cols, team):
    col.markdown(
        f"""
        <div class='card-box' style='border-top: 3px solid {color};'>
            <h3 style='margin:0; color:{TITLE};'>{sym} {name}</h3>
            <p style='margin-top:6px; font-size:0.85rem; color:{DIM};'>{work}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.info("Open each student's page from the **sidebar**. Each page owns its own CSV with full CRUD, statistics, charts, and a downloadable report.")

st.header("🛠️ Tools & Libraries")
tools = [
    ("Pandas", "Data wrangling, cleaning and statistical aggregations", "🐼"),
    ("Matplotlib", "Line, bar, scatter and pie chart visualizations", "📊"),
    ("Seaborn", "Statistical distributions, boxplots, KDE and heatmaps", "📈"),
    ("Streamlit", "Clean and responsive dark web dashboard", "🌐"),
]
cols2 = st.columns(4)
for col, (tool, use, sym) in zip(cols2, tools):
    col.markdown(
        f"""
        <div class='card-box'>
            <h3 style='margin:0; color:{TITLE};'>{sym} {tool}</h3>
            <p style='margin-top:6px; font-size:0.85rem; color:{DIM};'>{use}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.header("📁 Project Datasets")
datasets = [
    ("CICIDS 2017 Traffic", "harsh_final_cicids.csv", "🛡️", BLUE),
    ("Types of Cyber Crime", "types_of_cybercrime.csv", "📑", GREEN),
    ("State-Wise Cyber Crime", "cyber_crimes.csv", "🗺️", AMBER),
    ("Threat Detection Logs", "threat_detection.csv", "🔒", RED),
]
cols3 = st.columns(4)
for col, (dname, fname, sym, color) in zip(cols3, datasets):
    with col:
        st.markdown(
            f"""
            <div class='card-box' style='border-top: 3px solid {color}; margin-bottom: 8px;'>
                <h3 style='margin:0; color:{TITLE};'>{sym} {dname}</h3>
                <p style='margin-top:6px; font-size:0.82rem; color:{DIM}; font-family:monospace;'>{fname}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        data_path = os.path.join("data", fname)
        source = data_path if os.path.exists(data_path) else fname
        if os.path.exists(source):
            with open(source, "rb") as f:
                st.download_button(
                    label="⬇️ Download CSV",
                    data=f,
                    file_name=fname,
                    mime="text/csv",
                    key=f"dl_csv_{fname}",
                    use_container_width=True,
                )



