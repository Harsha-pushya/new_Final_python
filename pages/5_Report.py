import matplotlib

matplotlib.use("Agg")
import streamlit as st

from lib.theme import DIM, TITLE, apply_theme

st.set_page_config(page_title="Report · SNAKEFLOW", page_icon="📄", layout="wide")
apply_theme()

st.title("📄 Cross-Domain Security Report")
st.caption("Consolidated findings from all four cybersecurity analytical pillars.")

findings = [
    (
        "🛡️ CICIDS 2017 Intrusion (Harsh)",
        [
            "Executed through harsh_final_cicids.ipynb engine",
            "Normal traffic dominates the overall flow volume",
            "Attacks concentrate heavily on web ports (80 and 443)",
            "TCP flag anomalies (PSH/FIN) are key indicators for automated IDS",
        ],
    ),
    (
        "📑 Cyber Crime Typology (Abhinav)",
        [
            "Crime volumes increased steadily from 2016 to 2021",
            "Financial fraud and phishing carry the highest average loss",
            "High-risk incidents concentrate within specific categories",
        ],
    ),
    (
        "🗺️ State-Wise Distribution (Raju)",
        [
            "Uttar Pradesh, Maharashtra, and Karnataka lead in total volume",
            "Smaller states exhibit higher per-capita crime rates",
            "Consistent year-over-year growth across multiple states",
        ],
    ),
    (
        "🔒 SOC Threat Detection (Rithesh)",
        [
            "Alerts peak during standard business hours",
            "Critical alerts correlate with higher packet count and duration",
            "Automated status triage effectively handles majority of alerts",
        ],
    ),
]

st.header("📋 Key Findings Across Disciplines")
for c, (title, points) in zip(st.columns(2), findings[:2]):
    c.markdown(
        f"""
        <div class='card-box'>
            <h3 style='margin-top:0; color:{TITLE};'>{title}</h3>
            <ul style='color:{DIM}; font-size:0.85rem; padding-left:18px;'>
                {"".join(f"<li>{p}</li>" for p in points)}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
for c, (title, points) in zip(st.columns(2), findings[2:]):
    c.markdown(
        f"""
        <div class='card-box'>
            <h3 style='margin-top:0; color:{TITLE};'>{title}</h3>
            <ul style='color:{DIM}; font-size:0.85rem; padding-left:18px;'>
                {"".join(f"<li>{p}</li>" for p in points)}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.header("🏁 Conclusion")
st.caption(
    "SNAKEFLOW demonstrates how Python data analysis provides defense-grade cybersecurity intelligence. "
    "Through data unification in harsh_final_cicids.csv, in-depth exploratory analysis in harsh_final_cicids.ipynb, "
    "and clean dark visualization in Streamlit, security teams can evaluate network intrusions, "
    "track nationwide cyber incident vectors, and monitor threat alert trends."
)
