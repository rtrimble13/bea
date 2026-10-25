"""Flatten :class:`~bea.models.Series` into tidy records and optional wide tables.

The *long* layout has one row per (series, period). Core columns always come
first and in a fixed order so downstream consumers (spreadsheets, agents, jq)
can rely on them; the dataset-specific dimension columns (``table_name``,
``line_number``, ``geo_fips``, ``industry``, ...) are appended after them.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from datetime import date
from typing import Any

from bea.models import Series

Record = dict[str, Any]

CORE_COLUMNS: tuple[str, ...] = (
    "dataset",
    "series_id",
    "series_title",
    "date",
    "year",
    "period",
    "frequency",
    "value",
    "unit",
    "unit_mult",
    "note_ref",
)


def to_records(
    series: Iterable[Series],
    *,
    dataset: str,
    include_notes: bool = False,
    note_text: Callable[[str], str] | None = None,
) -> list[Record]:
    """Convert series into a list of flat dictionaries (long layout)."""
    records: list[Record] = []
    for s in series:
        for o in s.data:
            info = o.period_info
            rec: Record = {
                "dataset": dataset,
                "series_id": s.series_id,
                "series_title": s.title,
                "date": info.start_date(),
                "year": info.year,
                "period": o.period,
                "frequency": info.frequency.value,
                "value": o.value,
                "unit": o.unit,
                "unit_mult": o.unit_mult,
                "note_ref": o.note_ref,
            }
            if include_notes:
                rec["notes"] = note_text(o.note_ref) if note_text and o.note_ref else ""
            for k, v in s.attributes.items():
                rec.setdefault(k, v)
            records.append(rec)
    return records


def column_order(records: Sequence[Record]) -> list[str]:
    """Stable column order: core, then extra columns in first-seen order."""
    seen: dict[str, None] = {}
    for rec in records:
        for key in rec:
            seen.setdefault(key, None)
    if "value" not in seen or "series_id" not in seen:
        return list(seen)  # not data records: keep first-seen order
    core = [c for c in CORE_COLUMNS if c in seen]
    rest = [c for c in seen if c not in CORE_COLUMNS]
    if "notes" in rest:  # keep the resolved notes next to note_ref
        rest.remove("notes")
        core.append("notes")
    return core + rest


def to_wide(records: Sequence[Record], value_column: str = "value") -> list[Record]:
    """Pivot long records to one row per period with a column per series."""
    rows: dict[tuple[date, int, str], Record] = {}
    series_ids: dict[str, None] = {}
    for rec in records:
        key = (rec["date"], rec["year"], rec["period"])
        row = rows.setdefault(
            key, {"date": rec["date"], "year": rec["year"], "period": rec["period"]}
        )
        row[rec["series_id"]] = rec.get(value_column)
        series_ids.setdefault(rec["series_id"], None)
    out: list[Record] = []
    for key in sorted(rows):
        row = rows[key]
        for sid in series_ids:
            row.setdefault(sid, None)
        out.append(row)
    return out


def jsonable(value: Any) -> Any:
    """Make a record value JSON/CSV friendly."""
    if isinstance(value, date):
        return value.isoformat()
    return value


def stringify(value: Any) -> str:
    """Render a value for CSV / table output."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (list, dict)):
        return json.dumps(value, separators=(",", ":"))
    if isinstance(value, float):
        return f"{value:.10g}" if abs(value) >= 1e15 else repr(value)
    return str(value)
