"""Shared CSV persistence layer.

Every student manager extends CSVManager. Encapsulation is shown via the
protected `_data` attribute and a public `@property`. Every read/write uses
try/except/else/finally. Writes go to a temp file then replace the target so a
crash cannot leave a half-written CSV.
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd


class AppError(Exception):
    """Friendly, on-page error (never shown as a raw traceback)."""


class CSVManager:
    """Base class for CSV CRUD, validation, stats, and report export."""

    def __init__(
        self,
        filepath: str,
        id_column: str,
        required_columns: list[str] | None = None,
        dtypes: dict[str, type] | None = None,
        sep: str = ",",
        nan_policy: str = (
            "Missing values (NaN) are excluded from summary statistics "
            "(Pandas/NumPy skipna). Visualizations impute remaining numeric "
            "NaN with 0 so charts never crash."
        ),
        initial_path: str | None = None,
        cleaned_path: str | None = None,
        final_path: str | None = None,
        initial_sep: str | None = None,
        source_original: str | None = None,
    ) -> None:
        self._filepath = filepath
        self._id_column = id_column
        self._required_columns = required_columns or [id_column]
        self._dtypes = dtypes or {}
        self._sep = sep
        self._data = pd.DataFrame()
        self._last_error: str | None = None
        self._io_ok = False
        self._nan_policy = nan_policy
        self._initial_path = initial_path
        self._cleaned_path = cleaned_path
        self._final_path = final_path
        self._initial_sep = sep if initial_sep is None else initial_sep
        self._source_original = source_original
        self.ensure_initial()

    @property
    def data(self) -> pd.DataFrame:
        """Public copy of the protected dataset (encapsulation)."""
        return self._data.copy()

    @property
    def id_column(self) -> str:
        return self._id_column

    @property
    def filepath(self) -> str:
        return self._filepath

    @property
    def nan_policy(self) -> str:
        return self._nan_policy

    @property
    def last_error(self) -> str | None:
        return self._last_error

    def load(self) -> pd.DataFrame:
        """Load this student's CSV fresh. Never crashes: raises AppError instead."""
        self._io_ok = False
        self._last_error = None
        added_id = False
        try:
            if not os.path.exists(self._filepath):
                raise FileNotFoundError(f"CSV file missing: {self._filepath}")
            if os.path.getsize(self._filepath) == 0:
                raise ValueError("CSV file is empty")
            df = pd.read_csv(self._filepath, sep=self._sep)
            if df.empty:
                raise ValueError("CSV file has headers but no data rows")
            df.columns = [str(c).strip() for c in df.columns]
            added_id = False
            if self._id_column not in df.columns:
                df.insert(0, self._id_column, range(1, len(df) + 1))
                added_id = True
            df = self._after_load(df)
        except FileNotFoundError as exc:
            self._last_error = str(exc)
            self._data = pd.DataFrame()
            raise AppError(
                f"File missing. Place this student's CSV in the /data folder. ({exc})"
            ) from exc
        except (pd.errors.EmptyDataError, ValueError) as exc:
            self._last_error = str(exc)
            self._data = pd.DataFrame()
            raise AppError(f"Empty or unreadable CSV: {exc}") from exc
        except AppError:
            raise
        except Exception as exc:
            self._last_error = str(exc)
            self._data = pd.DataFrame()
            raise AppError(f"Could not read CSV: {exc}") from exc
        else:
            self._data = df
            self._io_ok = True
            if added_id:
                self._atomic_save(df)
            return self.data
        finally:
            if not isinstance(self._data, pd.DataFrame):
                self._data = pd.DataFrame()

    def _after_load(self, df: pd.DataFrame) -> pd.DataFrame:
        """Hook for subclasses (column aliases, extra IDs, etc.)."""
        return df

    def _atomic_save(self, df: pd.DataFrame) -> None:
        folder = os.path.dirname(self._filepath) or "."
        tmp_path = os.path.join(folder, f".{os.path.basename(self._filepath)}.tmp")
        self._io_ok = False
        try:
            df.to_csv(tmp_path, index=False, sep=self._sep)
            os.replace(tmp_path, self._filepath)
        except Exception as exc:
            self._last_error = str(exc)
            raise AppError(f"Could not write CSV safely: {exc}") from exc
        else:
            self._data = df
            self._io_ok = True
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def _ids_as_str(self, df: pd.DataFrame | None = None) -> pd.Series:
        source = self._data if df is None else df
        return source[self._id_column].astype(str).str.strip()

    def _find_row(self, record_id: Any) -> pd.Series:
        if record_id is None or str(record_id).strip() == "":
            raise AppError("Record ID is required.")
        matches = self._data.loc[self._ids_as_str() == str(record_id).strip()]
        if matches.empty:
            raise AppError(f"Invalid record ID for {self._id_column}: {record_id}")
        return matches.iloc[0]

    def _coerce_record(self, record: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for key, value in record.items():
            if key not in self._dtypes or value in (None, ""):
                cleaned[key] = value
                continue
            caster = self._dtypes[key]
            try:
                if caster is int:
                    cleaned[key] = int(float(value))
                elif caster is float:
                    cleaned[key] = float(value)
                else:
                    cleaned[key] = caster(value)
            except (TypeError, ValueError) as exc:
                raise AppError(
                    f"Wrong column type for '{key}': expected {caster.__name__}, got '{value}'."
                ) from exc
        return cleaned

    def _require_fields(self, record: dict[str, Any]) -> None:
        missing = [
            col
            for col in self._required_columns
            if col not in record or record[col] in (None, "")
        ]
        if missing:
            raise AppError(f"Required fields missing: {', '.join(missing)}")

    def _complete_columns(self, record: dict[str, Any]) -> dict[str, Any]:
        if self._data.empty:
            return record
        row: dict[str, Any] = {}
        for col in self._data.columns:
            if col in record and record[col] not in (None, ""):
                row[col] = record[col]
            elif pd.api.types.is_numeric_dtype(self._data[col]):
                row[col] = 0
            else:
                row[col] = ""
        return row

    def next_id(self) -> int:
        try:
            values = pd.to_numeric(self._data[self._id_column], errors="coerce")
            if values.dropna().empty:
                return 1
            return int(values.max()) + 1
        except Exception:
            return len(self._data) + 1

    def create(self, record: dict[str, Any]) -> str:
        try:
            self.load()
            record = self._coerce_record(record)
            self._require_fields(record)
            record = self._complete_columns(record)
            new_id = str(record[self._id_column]).strip()
            if new_id in set(self._ids_as_str()):
                raise AppError(f"Duplicate {self._id_column}: {new_id} already exists.")
            updated = pd.concat([self._data, pd.DataFrame([record])], ignore_index=True)
            self._atomic_save(updated)
        except AppError:
            raise
        except Exception as exc:
            raise AppError(f"Create failed: {exc}") from exc
        else:
            return f"Created record {self._id_column}={new_id}."
        finally:
            self._io_ok = self._io_ok and self._last_error is None

    def read(
        self,
        query: str = "",
        sort_column: str | None = None,
        ascending: bool = True,
    ) -> pd.DataFrame:
        try:
            self.load()
            df = self._data.copy()
            applied = query.strip()
            if applied:
                cells = df.astype(str)
                mask = cells.apply(lambda c: c.str.contains(applied, case=False, na=False))
                df = df.loc[mask.any(axis=1)]
            if sort_column and sort_column in df.columns:
                df = df.sort_values(sort_column, ascending=ascending, kind="mergesort")
        except AppError:
            raise
        except Exception as exc:
            raise AppError(f"Read/search failed: {exc}") from exc
        else:
            return df
        finally:
            self._io_ok = True

    def update(self, record_id: Any, fields: dict[str, Any]) -> str:
        try:
            self.load()
            self._find_row(record_id)
            fields = self._coerce_record(fields)
            idx = self._data.index[self._ids_as_str() == str(record_id).strip()]
            for key, value in fields.items():
                if key == self._id_column:
                    continue
                if key not in self._data.columns:
                    raise AppError(f"Unknown column: {key}")
                self._data.loc[idx, key] = value
            self._atomic_save(self._data)
        except AppError:
            raise
        except Exception as exc:
            raise AppError(f"Update failed: {exc}") from exc
        else:
            return f"Updated record {self._id_column}={record_id}."
        finally:
            self._io_ok = True

    def delete(self, record_id: Any, confirmed: bool) -> str:
        try:
            self.load()
            if not confirmed:
                raise AppError("Deletion not confirmed. Tick “Yes, delete” first.")
            self._find_row(record_id)
            remaining = self._data.loc[self._ids_as_str() != str(record_id).strip()].copy()
            self._atomic_save(remaining.reset_index(drop=True))
        except AppError:
            raise
        except Exception as exc:
            raise AppError(f"Delete failed: {exc}") from exc
        else:
            return f"Deleted record {self._id_column}={record_id}."
        finally:
            self._io_ok = True

    def summary_statistics(self, df: pd.DataFrame | None = None) -> dict[str, Any]:
        """At least three Pandas/NumPy stats; subclasses add dataset-specific ones."""
        frame = self._data if df is None else df
        numeric = frame.select_dtypes(include=[np.number])
        stats: dict[str, Any] = {
            "row_count": int(len(frame)),
            "column_count": int(frame.shape[1]),
            "numeric_mean_of_means": (
                float(numeric.mean(skipna=True).mean()) if not numeric.empty else 0.0
            ),
            "numeric_median_of_medians": (
                float(numeric.median(skipna=True).median()) if not numeric.empty else 0.0
            ),
            "numeric_std_of_stds": (
                float(numeric.std(skipna=True, ddof=0).mean()) if not numeric.empty else 0.0
            ),
            "duplicate_rows": int(frame.duplicated().sum()),
            "missing_cell_percent": round(
                float(frame.isna().mean().mean() * 100) if len(frame.columns) else 0.0, 3
            ),
        }
        stats.update(self.extra_statistics(frame))
        return stats

    def extra_statistics(self, df: pd.DataFrame) -> dict[str, Any]:
        return {}

    def missing_report(self, df: pd.DataFrame | None = None) -> dict[str, Any]:
        frame = self._data if df is None else df
        missing = int(frame.isna().sum().sum())
        return {
            "missing_cells": missing,
            "policy": self._nan_policy,
        }

    def export_report_text(self, df: pd.DataFrame, filters: str) -> str:
        stats = self.summary_statistics(df)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "SNAKEFLOW Dataset Report",
            f"Timestamp: {stamp}",
            f"CSV file: {os.path.basename(self._filepath)}",
            f"Row count (after filters): {len(df)}",
            f"Full CSV row count: {len(self._data)}",
            f"Filters applied: {filters or '(none)'}",
            f"NaN policy: {self._nan_policy}",
            "",
            "Summary statistics:",
        ]
        for key, value in stats.items():
            lines.append(f"  - {key}: {value}")
        return "\n".join(lines)

    def export_report_csv(self, df: pd.DataFrame, filters: str) -> str:
        stats = self.summary_statistics(df)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rows = [
            {"metric": "timestamp", "value": stamp},
            {"metric": "row_count", "value": len(df)},
            {"metric": "full_csv_row_count", "value": len(self._data)},
            {"metric": "filters_applied", "value": filters or "(none)"},
        ]
        for key, value in stats.items():
            rows.append({"metric": key, "value": value})
        return pd.DataFrame(rows).to_csv(index=False)

    def visualization_frame(self) -> pd.DataFrame:
        """Copy used by charts: numeric NaN imputed with 0."""
        df = self.data
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan).fillna(0)
        return df

    def pandas_enrich(self, df: pd.DataFrame | None = None) -> pd.DataFrame:
        """Add analysis columns with Pandas. Subclasses override."""
        frame = self.data if df is None else df.copy()
        return frame

    def pandas_tables(self, enriched: pd.DataFrame) -> dict[str, pd.DataFrame]:
        """Named Pandas tables (groupby, crosstab, describe) for the page."""
        numeric = enriched.select_dtypes(include=[np.number])
        return {
            "describe": numeric.describe().T.reset_index().rename(columns={"index": "column"}),
        }

    def ensure_initial(self) -> None:
        """Keep a frozen copy of the original dataset (never overwritten by CRUD)."""
        if not self._initial_path:
            return
        folder = os.path.dirname(self._initial_path) or "."
        os.makedirs(folder, exist_ok=True)
        if os.path.exists(self._initial_path):
            return
        src = None
        if self._source_original and os.path.exists(self._source_original):
            src = self._source_original
        elif os.path.exists(self._filepath):
            src = self._filepath
        if src:
            shutil.copy2(src, self._initial_path)

    def load_initial(self) -> pd.DataFrame:
        self.ensure_initial()
        if not self._initial_path:
            raise AppError("Initial CSV path is not set.")
        try:
            if not os.path.exists(self._initial_path):
                raise FileNotFoundError(self._initial_path)
            df = pd.read_csv(self._initial_path, sep=self._initial_sep)
            if df.empty:
                raise ValueError("Initial CSV is empty")
            df.columns = [str(c).strip() for c in df.columns]
        except Exception as exc:
            self._last_error = str(exc)
            raise AppError(f"Could not read initial CSV: {exc}") from exc
        else:
            return df
        finally:
            self._io_ok = True

    def make_cleaned(self) -> pd.DataFrame:
        """Initial data after cleaning: strip names, IDs, types, fill missing."""
        df = self.load_initial().copy()
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.drop_duplicates().reset_index(drop=True)
        if self._id_column not in df.columns:
            df.insert(0, self._id_column, range(1, len(df) + 1))
        for col, caster in self._dtypes.items():
            if col not in df.columns:
                continue
            if caster in (int, float):
                df[col] = pd.to_numeric(df[col], errors="coerce")
                fill = df[col].median()
                if pd.isna(fill):
                    fill = 0
                df[col] = df[col].fillna(fill)
                if caster is int:
                    df[col] = df[col].round().astype("int64")
            else:
                df[col] = df[col].astype(str).replace({"nan": "", "None": ""})
        num_cols = df.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            if df[col].isna().any():
                fill = df[col].median()
                df[col] = df[col].fillna(0 if pd.isna(fill) else fill)
        obj_cols = df.select_dtypes(include=["object"]).columns
        df[obj_cols] = df[obj_cols].fillna("")
        return df

    def _write_copy(self, path: str, df: pd.DataFrame) -> str:
        folder = os.path.dirname(path) or "."
        os.makedirs(folder, exist_ok=True)
        tmp_path = os.path.join(folder, f".{os.path.basename(path)}.tmp")
        try:
            df.to_csv(tmp_path, index=False)
            os.replace(tmp_path, path)
        except Exception as exc:
            self._last_error = str(exc)
            raise AppError(f"Could not write CSV {os.path.basename(path)}: {exc}") from exc
        else:
            return path
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def save_cleaned(self, df: pd.DataFrame) -> str:
        if not self._cleaned_path:
            raise AppError("Cleaned CSV path is not set.")
        return self._write_copy(self._cleaned_path, df)

    def save_updated(self, df: pd.DataFrame) -> str:
        if not self._final_path:
            raise AppError("Updated CSV path is not set.")
        return self._write_copy(self._final_path, df)

    def save_final(self, df: pd.DataFrame) -> str:
        return self.save_updated(df)

    def three_csvs(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Initial, cleaned, and updated (current rows + analysis columns)."""
        initial = self.load_initial()
        cleaned = self.make_cleaned()
        self.save_cleaned(cleaned)
        try:
            self.load()
        except AppError:
            pass
        updated = self.pandas_enrich()
        self.save_updated(updated)
        return initial, cleaned, updated

    @property
    def initial_path(self) -> str | None:
        return self._initial_path

    @property
    def cleaned_path(self) -> str | None:
        return self._cleaned_path

    @property
    def final_path(self) -> str | None:
        return self._final_path

    @property
    def updated_path(self) -> str | None:
        return self._final_path
