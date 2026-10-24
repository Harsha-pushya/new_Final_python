# SNAKEFLOW — Cyber Threat Analysis

Python Streamlit web app for **22AIE205 Introduction to Python** (term project).

Theme: cybersecurity intelligence — network intrusions, cyber-crime types, state-wise crime, and SOC threat alerts.

Core loop: **Input data → Update CSV → Read / Analyze / View → Visualize**

## Setup (Python 3.10+)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501). Use the sidebar to open each student's page.

All file paths are **relative to the project root**. CSV files live in `/data`.

## Who owns which page / CSV

| Student | Page | CSV | Notebook |
|---|---|---|---|
| Harsh | `pages/1_CICIDS.py` | `data/harsh_final_cicids.csv` | `harsh_final_cicids.ipynb` |
| Abhinav | `pages/2_Types_of_Cyber_Crime.py` | `data/types_of_cybercrime.csv` | `abhinab.ipynb` |
| Raju | `pages/3_State_Wise_Crime.py` | `data/cyber_crimes.csv` | `raju.ipynb` |
| Rithesh | `pages/4_Threat_Detection.py` | `data/threat_detection.csv` | `rithesh.ipynb` |

Landing page: `app.py`. Cross-domain write-up: `pages/5_Report.py`.

Shared OOP: `lib/csv_manager.py` (`CSVManager`) extended by each student class in `lib/managers.py`.


## Notes

- Each page loads **only** its own CSV and never writes a teammate's file.
- Writes use a temp file then `os.replace` so a crash cannot leave a corrupted CSV.
- Missing values (NaN) are excluded from statistics; charts impute numeric NaN with 0.
