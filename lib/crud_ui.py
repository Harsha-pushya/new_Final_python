"""Reusable CRUD + report UI. Each page still owns its manager class and CSV."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from lib.csv_manager import AppError, CSVManager


Field = dict[str, Any]


def _widget(field: Field, key: str, value=None):
    kind = field.get("kind", "text")
    label = field["label"]
    options = field.get("options") or []
    if kind == "int":
        default = int(value) if value not in (None, "") else int(field.get("default", 0))
        return st.number_input(label, value=default, step=1, key=key)
    if kind == "float":
        default = float(value) if value not in (None, "") else float(field.get("default", 0.0))
        return st.number_input(label, value=default, key=key)
    if kind == "select":
        opts = list(options)
        if value not in opts and value not in (None, ""):
            opts = [value] + opts
        index = opts.index(value) if value in opts else 0
        return st.selectbox(label, opts, index=index if opts else 0, key=key)
    default = "" if value is None else str(value)
    return st.text_input(label, value=default, key=key)


def render_crud(manager: CSVManager, fields: list[Field], key_prefix: str) -> None:
    st.header("🧩 CRUD — Create / Read / Update / Delete")
    st.caption(
        "Input data → validate → write CSV (temp file then replace) → reload → analyze / visualize. "
        "This page only reads and writes its own CSV in /data."
    )

    try:
        df = manager.load()
    except AppError as exc:
        st.error(str(exc))
        return

    miss = manager.missing_report(df)
    st.info(f"**NaN handling:** {miss['policy']} | Missing cells in current CSV: **{miss['missing_cells']}**")

    stats = manager.summary_statistics(df)
    st.subheader("📊 Summary statistics (Pandas / NumPy)")
    metric_items = [
        ("Rows", f"{stats.get('row_count', 0):,}"),
        ("Columns", str(stats.get("column_count", 0))),
        ("Numeric mean", f"{stats.get('numeric_mean_of_means', 0):.2f}"),
    ]
    extra_keys = [k for k in stats if k not in {"row_count", "column_count", "numeric_mean_of_means", "groupby_attack_counts", "groupby_risk_count", "groupby_category_count", "groupby_severity_count"}]
    for name in extra_keys[:1]:
        metric_items.append((name.replace("_", " ").title(), str(stats[name])))
    cols = st.columns(len(metric_items))
    for col, (label, value) in zip(cols, metric_items):
        col.metric(label, value)
    with st.expander("All computed statistics"):
        st.json(stats)

    tab_c, tab_r, tab_u, tab_d, tab_x = st.tabs(
        ["➕ Create", "📖 Read / Search / Sort", "✏️ Update", "🗑️ Delete", "📤 Export Report"]
    )
    id_col = manager.id_column

    with tab_c:
        st.markdown("Add a new record. Required fields are validated; duplicate IDs are rejected.")
        created = {}
        created[id_col] = st.number_input(
            f"{id_col} (auto next ID, change if needed)",
            value=int(manager.next_id()),
            step=1,
            key=f"{key_prefix}_new_id",
        )
        for field in fields:
            if field["name"] == id_col:
                continue
            created[field["name"]] = _widget(field, key=f"{key_prefix}_c_{field['name']}")
        if st.button("Append to CSV", key=f"{key_prefix}_create_btn"):
            try:
                message = manager.create(created)
            except AppError as exc:
                st.error(str(exc))
            else:
                st.success(message)
                st.rerun()

    with tab_r:
        query = st.text_input("Search / filter (any column)", key=f"{key_prefix}_q")
        sort_col = st.selectbox("Sort by column", ["(no sort)"] + list(df.columns), key=f"{key_prefix}_sort")
        ascending = st.checkbox("Ascending", value=True, key=f"{key_prefix}_asc")
        try:
            view = manager.read(
                query=query,
                sort_column=None if sort_col == "(no sort)" else sort_col,
                ascending=ascending,
            )
        except AppError as exc:
            st.error(str(exc))
            view = df
        st.caption(f"{len(view):,} rows after search/filter/sort (showing up to 300).")
        st.dataframe(view.head(300), use_container_width=True)

    with tab_u:
        ids = df[id_col].astype(str).tolist()
        if not ids:
            st.warning("No records to update.")
        else:
            chosen = st.selectbox(f"Select {id_col}", ids, key=f"{key_prefix}_uid")
            current = df.loc[df[id_col].astype(str) == str(chosen)].iloc[0]
            updates: dict[str, Any] = {}
            for field in fields:
                if field["name"] == id_col:
                    continue
                raw = current[field["name"]] if field["name"] in current.index else ""
                updates[field["name"]] = _widget(field, key=f"{key_prefix}_u_{field['name']}", value=raw)
            if st.button("Write update to CSV", key=f"{key_prefix}_update_btn"):
                try:
                    message = manager.update(chosen, updates)
                except AppError as exc:
                    st.error(str(exc))
                else:
                    st.success(message)
                    st.rerun()

    with tab_d:
        ids = df[id_col].astype(str).tolist()
        if not ids:
            st.warning("No records to delete.")
        else:
            chosen = st.selectbox(f"Select {id_col} to delete", ids, key=f"{key_prefix}_did")
            preview = df.loc[df[id_col].astype(str) == str(chosen)]
            st.dataframe(preview, use_container_width=True)
            confirmed = st.checkbox("Yes, delete this record", key=f"{key_prefix}_yes")
            if st.button("Delete from CSV", key=f"{key_prefix}_delete_btn"):
                try:
                    message = manager.delete(chosen, confirmed=confirmed)
                except AppError as exc:
                    st.error(str(exc))
                else:
                    st.success(message)
                    st.rerun()

    with tab_x:
        query = st.text_input("Filters to record in the report", key=f"{key_prefix}_rep_q")
        try:
            view = manager.read(query=query)
        except AppError as exc:
            st.error(str(exc))
            view = df
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_report = manager.export_report_text(view, query)
        csv_report = manager.export_report_csv(view, query)
        st.text(text_report)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "Download TXT report",
                data=text_report,
                file_name=f"{key_prefix}_report_{stamp}.txt",
                mime="text/plain",
                key=f"{key_prefix}_dl_txt",
            )
        with c2:
            st.download_button(
                "Download CSV report",
                data=csv_report,
                file_name=f"{key_prefix}_report_{stamp}.csv",
                mime="text/csv",
                key=f"{key_prefix}_dl_csv",
            )


def render_pandas_tables(tables: dict[str, pd.DataFrame]) -> None:
    st.header("🐼 Extra Pandas analysis")
    st.caption(
        "groupby.agg, crosstab, rank, qcut/cut, and transform columns computed with Pandas "
        "from the current CSV (including any CRUD edits)."
    )
    names = list(tables.keys())
    tabs = st.tabs([name.replace("_", " ") for name in names])
    for tab, name in zip(tabs, names):
        with tab:
            frame = tables[name]
            st.dataframe(frame, use_container_width=True)
            st.caption(f"{frame.shape[0]} rows × {frame.shape[1]} columns")


def render_csv_files(manager: CSVManager, key_prefix: str) -> None:
    """Last section on each student page: initial, cleaned, updated CSV downloads."""
    st.header("CSV files")
    st.caption("Three files: 1) initial dataset  2) cleaned dataset  3) updated dataset after our edits")
    try:
        initial, cleaned, updated = manager.three_csvs()
    except AppError as exc:
        st.error(str(exc))
        return

    extra_cols = [c for c in updated.columns if c not in cleaned.columns]
    row_delta = int(len(updated) - len(cleaned))

    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("1. Initial")
        st.caption(f"{initial.shape[0]:,} rows × {initial.shape[1]} columns")
        st.dataframe(initial.head(20), use_container_width=True, height=280)
        st.download_button(
            "Download initial.csv",
            data=initial.to_csv(index=False),
            file_name=f"{key_prefix}_initial.csv",
            mime="text/csv",
            key=f"{key_prefix}_dl_initial",
            use_container_width=True,
        )
    with c2:
        st.subheader("2. Cleaned")
        st.caption(f"{cleaned.shape[0]:,} rows × {cleaned.shape[1]} columns")
        st.dataframe(cleaned.head(20), use_container_width=True, height=280)
        st.download_button(
            "Download cleaned.csv",
            data=cleaned.to_csv(index=False),
            file_name=f"{key_prefix}_cleaned.csv",
            mime="text/csv",
            key=f"{key_prefix}_dl_cleaned",
            use_container_width=True,
        )
    with c3:
        st.subheader("3. Updated")
        change_note = "no extra CRUD rows" if row_delta == 0 else f"{row_delta:+d} rows vs cleaned"
        st.caption(f"{updated.shape[0]:,} rows × {updated.shape[1]} columns · {change_note}")
        st.dataframe(updated.head(20), use_container_width=True, height=280)
        st.download_button(
            "Download updated.csv",
            data=updated.to_csv(index=False),
            file_name=f"{key_prefix}_updated.csv",
            mime="text/csv",
            key=f"{key_prefix}_dl_updated",
            use_container_width=True,
        )

    if extra_cols:
        st.info("Columns added in updated.csv: " + ", ".join(extra_cols))


def render_initial_vs_final(manager: CSVManager, key_prefix: str, **_kwargs) -> None:
    render_csv_files(manager, key_prefix)
