"""Student-owned dataset managers. Each class extends CSVManager."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from lib.csv_manager import CSVManager

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
INITIAL = DATA / "initial"
CLEANED = DATA / "cleaned"
UPDATED = DATA / "updated"


class CICIDSManager(CSVManager):
    """Harsh — CICIDS 2017 network traffic (data/harsh_final_cicids.csv)."""

    def __init__(self) -> None:
        super().__init__(
            filepath=str(DATA / "harsh_final_cicids.csv"),
            id_column="Record_ID",
            required_columns=["Record_ID", "Destination Port", "Attack Type"],
            dtypes={
                "Record_ID": int,
                "Destination Port": int,
                "Flow Duration": float,
                "Total Fwd Packets": float,
                "Average Packet Size": float,
            },
            initial_path=str(INITIAL / "cicids.csv"),
            cleaned_path=str(CLEANED / "cicids.csv"),
            final_path=str(UPDATED / "cicids.csv"),
            source_original=str(ROOT / "cicids_small.csv"),
        )

    def _after_load(self, df: pd.DataFrame) -> pd.DataFrame:
        if "Record_ID" not in df.columns:
            df.insert(0, "Record_ID", range(1, len(df) + 1))
        return df

    def extra_statistics(self, df: pd.DataFrame) -> dict:
        if df.empty or "Attack Type" not in df.columns:
            return {}
        is_normal = df["Attack Type"] == "Normal Traffic"
        mean_size = float(df["Average Packet Size"].mean(skipna=True)) if "Average Packet Size" in df else 0.0
        return {
            "mean_average_packet_size": round(mean_size, 2),
            "attack_type_count": int(df["Attack Type"].nunique()),
            "attack_traffic_percent": round(float((1 - is_normal.mean()) * 100), 2),
            "groupby_attack_counts": {
                str(k): int(v) for k, v in df.groupby("Attack Type").size().items()
            },
            "median_flow_duration": round(float(df["Flow Duration"].median(skipna=True)), 2),
            "std_packet_size": round(float(df["Average Packet Size"].std(skipna=True)), 2),
        }

    def pandas_enrich(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        frame = (self.data if df is None else df).copy()
        frame = frame.replace([np.inf, -np.inf], np.nan)
        num_cols = frame.select_dtypes(include=[np.number]).columns
        frame[num_cols] = frame[num_cols].apply(lambda s: s.fillna(s.median()))
        frame["Traffic_Class"] = np.where(
            frame["Attack Type"].eq("Normal Traffic"), "Normal", "Attack"
        )
        frame["Is_Web_Port"] = np.where(
            frame["Destination Port"].isin([80, 443]), "Web (80/443)", "Other"
        )
        frame["Port_Class"] = pd.cut(
            frame["Destination Port"],
            bins=[-1, 1023, 49151, 65535],
            labels=["Well-known", "Registered", "Dynamic"],
        )
        size = frame["Average Packet Size"].clip(lower=0)
        frame["Packet_Size_Quartile"] = pd.qcut(
            size.rank(method="first"), 4, labels=["Q1", "Q2", "Q3", "Q4"]
        )
        frame["Flow_Duration_Log"] = np.log1p(frame["Flow Duration"].clip(lower=0))
        frame["Packet_Size_vs_Type_Mean"] = frame["Average Packet Size"] - frame.groupby(
            "Attack Type"
        )["Average Packet Size"].transform("mean")
        frame["Attack_Type_Count"] = frame.groupby("Attack Type")["Attack Type"].transform("size")
        frame["Bytes_per_Fwd_Packet"] = (
            frame["Total Length of Fwd Packets"] / frame["Total Fwd Packets"].replace(0, np.nan)
        )
        return frame

    def pandas_tables(self, enriched: pd.DataFrame) -> dict[str, pd.DataFrame]:
        by_type = (
            enriched.groupby("Attack Type", as_index=False)
            .agg(
                flows=("Record_ID", "count"),
                mean_packet_size=("Average Packet Size", "mean"),
                median_duration=("Flow Duration", "median"),
                mean_fwd_packets=("Total Fwd Packets", "mean"),
                web_port_share=("Is_Web_Port", lambda s: (s == "Web (80/443)").mean()),
            )
            .sort_values("flows", ascending=False)
        )
        class_port = pd.crosstab(
            enriched["Traffic_Class"], enriched["Port_Class"], normalize="index"
        ).mul(100).round(2)
        quartile = (
            enriched.groupby(["Traffic_Class", "Packet_Size_Quartile"], observed=False)
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        return {
            "groupby_attack_type": by_type,
            "crosstab_class_vs_port": class_port.reset_index(),
            "counts_class_vs_quartile": quartile,
        }


class CrimeTypeManager(CSVManager):
    """Abhinav — types of cyber crime (data/types_of_cybercrime.csv)."""

    def __init__(self) -> None:
        super().__init__(
            filepath=str(DATA / "types_of_cybercrime.csv"),
            id_column="S. No",
            required_columns=["S. No", "Crime Type", "Category", "Risk Level"],
            dtypes={
                "S. No": int,
                "2016": int,
                "2017": int,
                "2018": int,
                "2019": int,
                "2020": int,
                "2021": int,
                "Percentage Share": float,
                "Avg Loss Lakhs": float,
            },
            initial_path=str(INITIAL / "crime.csv"),
            cleaned_path=str(CLEANED / "crime.csv"),
            final_path=str(UPDATED / "crime.csv"),
        )

    def extra_statistics(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {}
        return {
            "mean_avg_loss_lakhs": round(float(df["Avg Loss Lakhs"].mean(skipna=True)), 2),
            "sum_2021_cases": int(df["2021"].sum(skipna=True)),
            "groupby_risk_count": {
                str(k): int(v) for k, v in df.groupby("Risk Level").size().items()
            },
            "category_count": int(df["Category"].nunique()),
            "median_2021_cases": int(df["2021"].median(skipna=True)),
            "std_avg_loss": round(float(df["Avg Loss Lakhs"].std(skipna=True)), 2),
        }

    def pandas_enrich(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        frame = (self.data if df is None else df).copy()
        years = ["2016", "2017", "2018", "2019", "2020", "2021"]
        present = [y for y in years if y in frame.columns]
        frame[present] = frame[present].apply(pd.to_numeric, errors="coerce")
        frame["Total_Cases"] = frame[present].sum(axis=1, skipna=True)
        frame["Mean_Yearly_Cases"] = frame[present].mean(axis=1, skipna=True)
        base = frame["2016"].replace(0, np.nan) if "2016" in frame else np.nan
        frame["Growth_2016_to_2021_pct"] = ((frame["2021"] - frame["2016"]) / base * 100).round(2)
        frame["CAGR_5yr_pct"] = (((frame["2021"] / base) ** (1 / 5) - 1) * 100).round(2)
        frame["Loss_Band"] = pd.cut(
            frame["Avg Loss Lakhs"],
            bins=[-0.01, 10, 25, 1000],
            labels=["Low loss", "Medium loss", "High loss"],
        )
        frame["Share_Rank"] = frame["Percentage Share"].rank(ascending=False, method="min")
        frame["Category_Case_Share"] = (
            frame["2021"] / frame.groupby("Category")["2021"].transform("sum") * 100
        ).round(2)
        return frame

    def pandas_tables(self, enriched: pd.DataFrame) -> dict[str, pd.DataFrame]:
        by_cat = (
            enriched.groupby("Category", as_index=False)
            .agg(
                crime_types=("Crime Type", "nunique"),
                total_2021=("2021", "sum"),
                mean_loss=("Avg Loss Lakhs", "mean"),
                mean_growth=("Growth_2016_to_2021_pct", "mean"),
            )
            .sort_values("total_2021", ascending=False)
        )
        risk_loss = pd.crosstab(enriched["Risk Level"], enriched["Loss_Band"])
        yearly = (
            enriched[["2016", "2017", "2018", "2019", "2020", "2021"]]
            .sum()
            .rename("total_cases")
            .reset_index()
            .rename(columns={"index": "year"})
        )
        return {
            "groupby_category": by_cat,
            "crosstab_risk_vs_loss_band": risk_loss.reset_index(),
            "yearly_totals": yearly,
        }


class StateCrimeManager(CSVManager):
    """Raju — state-wise cyber crime (data/cyber_crimes.csv, tab-separated)."""

    def __init__(self) -> None:
        super().__init__(
            filepath=str(DATA / "cyber_crimes.csv"),
            id_column="S. No",
            required_columns=["S. No", "Category", "State/UT"],
            dtypes={
                "S. No": int,
                "2016": float,
                "2017": float,
                "2018": float,
            },
            sep="\t",
            initial_path=str(INITIAL / "state.csv"),
            cleaned_path=str(CLEANED / "state.csv"),
            final_path=str(UPDATED / "state.csv"),
            initial_sep="\t",
        )

    def extra_statistics(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {}
        rate_col = [c for c in df.columns if c.startswith("Rate")]
        rate_name = rate_col[0] if rate_col else None
        return {
            "sum_2018_cases": float(df["2018"].sum(skipna=True)),
            "mean_crime_rate": (
                round(float(df[rate_name].mean(skipna=True)), 2) if rate_name else 0.0
            ),
            "groupby_category_count": {
                str(k): int(v) for k, v in df.groupby("Category").size().items()
            },
            "state_count": int(df["State/UT"].nunique()) if "State/UT" in df.columns else int(len(df)),
            "median_2018": float(df["2018"].median(skipna=True)),
            "std_2018": round(float(df["2018"].std(skipna=True)), 2),
        }

    def analysis_frame(self) -> pd.DataFrame:
        """Keep original CSV columns, expose short names for existing charts."""
        d = self.visualization_frame()
        d = d[~d["State/UT"].astype(str).str.contains("Total", case=False, na=False)].copy()
        rename = {}
        for col in d.columns:
            if col == "S. No":
                rename[col] = "No"
            elif col == "Category":
                rename[col] = "Type"
            elif col == "State/UT":
                rename[col] = "State"
            elif "Percentage Share" in col:
                rename[col] = "Share"
            elif "Population" in col:
                rename[col] = "Population"
            elif col.startswith("Rate"):
                rename[col] = "Rate"
        return d.rename(columns=rename)

    def pandas_enrich(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        frame = (self.data if df is None else df).copy()
        frame = frame[~frame["State/UT"].astype(str).str.contains("Total", case=False, na=False)].copy()
        rate_col = next(c for c in frame.columns if c.startswith("Rate"))
        pop_col = next(c for c in frame.columns if "Population" in c)
        for year in ("2016", "2017", "2018"):
            frame[year] = pd.to_numeric(frame[year], errors="coerce")
        frame["Growth_2016_2018_pct"] = (
            (frame["2018"] - frame["2016"]) / frame["2016"].replace(0, np.nan) * 100
        ).round(2)
        frame["YoY_2017_pct"] = (
            (frame["2017"] - frame["2016"]) / frame["2016"].replace(0, np.nan) * 100
        ).round(2)
        frame["YoY_2018_pct"] = (
            (frame["2018"] - frame["2017"]) / frame["2017"].replace(0, np.nan) * 100
        ).round(2)
        frame["Case_Rank_2018"] = frame["2018"].rank(ascending=False, method="min")
        frame["Rate_Quartile"] = pd.qcut(
            pd.to_numeric(frame[rate_col], errors="coerce").rank(method="first"),
            4,
            labels=["Q1", "Q2", "Q3", "Q4"],
        )
        frame["Cases_per_Lakh"] = (
            frame["2018"] / pd.to_numeric(frame[pop_col], errors="coerce").replace(0, np.nan) * 100
        ).round(3)
        frame["National_Share_2018"] = (frame["2018"] / frame["2018"].sum() * 100).round(2)
        return frame

    def pandas_tables(self, enriched: pd.DataFrame) -> dict[str, pd.DataFrame]:
        by_cat = (
            enriched.groupby("Category", as_index=False)
            .agg(
                states=("State/UT", "nunique"),
                total_2018=("2018", "sum"),
                mean_growth=("Growth_2016_2018_pct", "mean"),
                median_2018=("2018", "median"),
            )
            .sort_values("total_2018", ascending=False)
        )
        top = (
            enriched.nlargest(10, "2018")[
                ["State/UT", "2016", "2017", "2018", "Growth_2016_2018_pct", "Case_Rank_2018"]
            ]
            .reset_index(drop=True)
        )
        rate_band = (
            enriched.groupby(["Category", "Rate_Quartile"], observed=False)
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        return {
            "groupby_category": by_cat,
            "top10_states_2018": top,
            "category_vs_rate_quartile": rate_band,
        }


class ThreatManager(CSVManager):
    """Rithesh — threat detection logs (data/threat_detection.csv)."""

    def __init__(self) -> None:
        super().__init__(
            filepath=str(DATA / "threat_detection.csv"),
            id_column="Alert ID",
            required_columns=["Alert ID", "Threat Type", "Severity", "Status"],
            dtypes={
                "Alert ID": int,
                "Hour": int,
                "Dest Port": int,
                "Packets": int,
                "Bytes": int,
                "Duration": int,
                "Threat Score": float,
                "Is Attack": int,
            },
            initial_path=str(INITIAL / "threat.csv"),
            cleaned_path=str(CLEANED / "threat.csv"),
            final_path=str(UPDATED / "threat.csv"),
        )

    def extra_statistics(self, df: pd.DataFrame) -> dict:
        if df.empty:
            return {}
        return {
            "mean_threat_score": round(float(df["Threat Score"].mean(skipna=True)), 2),
            "attack_rate_percent": round(float(df["Is Attack"].mean(skipna=True) * 100), 2),
            "groupby_severity_count": {
                str(k): int(v) for k, v in df.groupby("Severity").size().items()
            },
            "threat_type_count": int(df["Threat Type"].nunique()),
            "median_threat_score": round(float(df["Threat Score"].median(skipna=True)), 2),
            "std_packets": round(float(df["Packets"].std(skipna=True)), 2),
        }

    def pandas_enrich(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        frame = (self.data if df is None else df).copy()
        frame["Business_Hours"] = np.where(frame["Hour"].between(9, 18), "Business", "Off-hours")
        frame["Score_Band"] = pd.cut(
            frame["Threat Score"],
            bins=[-0.01, 25, 50, 75, 1000],
            labels=["Low", "Moderate", "High", "Extreme"],
        )
        severity_rank = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
        frame["Severity_Rank"] = frame["Severity"].map(severity_rank)
        frame["Bytes_per_Packet"] = (
            frame["Bytes"] / frame["Packets"].replace(0, np.nan)
        ).round(2)
        frame["Type_Mean_Score"] = frame.groupby("Threat Type")["Threat Score"].transform("mean")
        frame["Score_vs_Type_Mean"] = (frame["Threat Score"] - frame["Type_Mean_Score"]).round(2)
        frame["Attack_Label"] = np.where(frame["Is Attack"].eq(1), "Attack", "Benign")
        return frame

    def pandas_tables(self, enriched: pd.DataFrame) -> dict[str, pd.DataFrame]:
        by_type = (
            enriched.groupby("Threat Type", as_index=False)
            .agg(
                alerts=("Alert ID", "count"),
                mean_score=("Threat Score", "mean"),
                attack_rate=("Is Attack", "mean"),
                median_packets=("Packets", "median"),
            )
            .sort_values("alerts", ascending=False)
        )
        sev_hours = pd.crosstab(enriched["Severity"], enriched["Business_Hours"])
        status_attack = pd.crosstab(enriched["Status"], enriched["Attack_Label"], normalize="index").mul(100).round(2)
        return {
            "groupby_threat_type": by_type,
            "crosstab_severity_vs_hours": sev_hours.reset_index(),
            "crosstab_status_vs_attack_pct": status_attack.reset_index(),
        }
