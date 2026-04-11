from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import polars as pl
from openpyxl import Workbook

import tabulynx.core as core
from tabulynx.core import ColumnFilter, QueryState, SortRule, open_dataset


def _write_csv(path: Path) -> None:
    frame = pl.DataFrame(
        {
            "customer": ["Acme", "Beta", "Acme", "Delta"],
            "orders": [3, 9, 2, 7],
            "revenue": [10.5, 42.0, 17.5, 33.3],
            "active": [True, False, True, True],
            "signup_date": [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)],
        }
    )
    frame.write_csv(path)


def _write_xlsx(path: Path) -> None:
    workbook = Workbook()
    ws1 = workbook.active
    ws1.title = "Sheet1"
    ws1.append(["customer", "orders", "revenue", "seen_at"])
    ws1.append(["Acme", 1, 12.5, datetime(2025, 1, 1, 10, 30, 0)])
    ws1.append(["Beta", 5, 17.0, datetime(2025, 1, 2, 11, 45, 0)])

    ws2 = workbook.create_sheet("Sheet2")
    ws2.append(["name", "score"])
    ws2.append(["Gamma", 99])
    ws2.append(["Delta", 75])
    workbook.save(path)


def _write_typed_parquet(path: Path) -> None:
    frame = pl.DataFrame(
        {
            "name": ["Acme", "Beta", "Gamma", None],
            "orders": [1, 5, 3, None],
            "revenue": [10.5, 17.0, 17.0, None],
            "active": [True, False, True, None],
            "signup_date": [
                date(2024, 1, 1),
                date(2024, 1, 2),
                date(2024, 1, 3),
                None,
            ],
            "seen_at": [
                datetime(2025, 1, 1, 10, 30, 0),
                datetime(2025, 1, 2, 11, 45, 0),
                datetime(2025, 1, 3, 9, 15, 0),
                None,
            ],
        }
    )
    frame.write_parquet(path)


def test_query_state_with_filters_search_sort_and_visible_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "demo.csv"
    _write_csv(csv_path)

    dataset = open_dataset(csv_path)
    dataset.set_search_text("Acme")
    dataset.set_filters([ColumnFilter(column="active", operator="equals", value="true")])
    dataset.set_sorts([SortRule(column="orders", descending=True)])
    dataset.set_visible_columns(["customer", "orders"])

    page = dataset.page(0, 10)

    assert page.row_count == 2
    assert page.columns == ["customer", "orders"]
    assert [row["orders"] for row in page.rows] == [3, 2]


def test_export_current_view_respects_query_state(tmp_path: Path) -> None:
    csv_path = tmp_path / "demo.csv"
    export_path = tmp_path / "filtered.parquet"
    _write_csv(csv_path)

    dataset = open_dataset(csv_path)
    dataset.add_filter(ColumnFilter(column="customer", operator="contains", value="Ac"))
    dataset.set_sorts([SortRule(column="revenue", descending=True)])
    dataset.export_current_view(export_path)

    exported = pl.read_parquet(export_path)
    assert exported.columns == ["customer", "orders", "revenue", "active", "signup_date"]
    assert exported.height == 2
    assert exported.get_column("revenue").to_list() == [17.5, 10.5]


def test_dataset_profile_and_column_stats(tmp_path: Path) -> None:
    csv_path = tmp_path / "demo.csv"
    _write_csv(csv_path)

    dataset = open_dataset(csv_path)
    profile = dataset.dataset_profile()
    stats = dataset.column_stats("orders")

    assert profile.row_count == 4
    assert profile.column_count == 5
    assert profile.type_counts["int"] == 1
    assert "orders" in profile.numeric_columns
    assert stats.type_name == "int"
    assert stats.min_value == 2
    assert stats.max_value == 9


def test_xlsx_uses_cached_parquet_and_sheet_switch(tmp_path: Path, monkeypatch) -> None:
    workbook_path = tmp_path / "demo.xlsx"
    cache_dir = tmp_path / "cache"
    _write_xlsx(workbook_path)
    monkeypatch.setattr(core, "TABULYNX_CACHE_DIR", cache_dir)

    dataset = open_dataset(workbook_path)

    assert dataset.uses_excel_cache is True
    assert dataset.sheet_names() == ["Sheet1", "Sheet2"]
    assert dataset.columns() == ["customer", "orders", "revenue", "seen_at"]
    assert any(cache_dir.rglob("data.parquet"))

    dataset.set_sheet("Sheet2")
    assert dataset.columns() == ["name", "score"]
    assert dataset.page(0, 10).row_count == 2


def test_sql_query_uses_current_view_and_creates_transient_dataset(tmp_path: Path, monkeypatch) -> None:
    csv_path = tmp_path / "demo.csv"
    cache_dir = tmp_path / "cache"
    _write_csv(csv_path)
    monkeypatch.setattr(core, "TABULYNX_CACHE_DIR", cache_dir)

    dataset = open_dataset(csv_path)
    dataset.add_filter(ColumnFilter(column="customer", operator="contains", value="Ac"))
    dataset.set_visible_columns(["customer", "revenue"])
    dataset.set_sorts([SortRule(column="revenue", descending=True)])

    result = dataset.sql_query(
        "SELECT customer, revenue FROM current WHERE revenue > 12 ORDER BY revenue DESC"
    )

    assert result.columns == ["customer", "revenue"]
    assert result.height == 1
    assert result.to_dicts() == [{"customer": "Acme", "revenue": 17.5}]

    transient = core.DatasetSession.from_frame(result, name="SQL result")
    assert transient.is_transient is True
    assert transient.name == "SQL result"
    assert transient.suffix == ".parquet"
    assert transient.preview() == [{"customer": "Acme", "revenue": 17.5}]


def test_query_state_roundtrip_serialization() -> None:
    state = QueryState(
        sorts=[SortRule(column="revenue", descending=True), SortRule(column="orders", descending=False)],
        visible_columns=["customer", "revenue"],
        filters=[
            ColumnFilter(column="customer", operator="contains", value="Ac"),
            ColumnFilter(column="active", operator="equals", value="true"),
        ],
        search_text="promo",
    )

    restored = QueryState.from_dict(state.to_dict())

    assert restored.to_dict() == state.to_dict()


def test_multi_sort_precedence_is_respected(tmp_path: Path) -> None:
    csv_path = tmp_path / "demo.csv"
    _write_csv(csv_path)

    dataset = open_dataset(csv_path)
    dataset.set_sorts(
        [
            SortRule(column="customer", descending=False),
            SortRule(column="revenue", descending=True),
        ]
    )

    rows = dataset.page(0, 10).rows

    assert [row["customer"] for row in rows] == ["Acme", "Acme", "Beta", "Delta"]
    assert [row["revenue"] for row in rows[:2]] == [17.5, 10.5]


def test_typed_filter_operators_cover_numeric_boolean_and_temporal_values(tmp_path: Path) -> None:
    parquet_path = tmp_path / "typed.parquet"
    _write_typed_parquet(parquet_path)

    dataset = open_dataset(parquet_path)

    dataset.set_filters([ColumnFilter(column="orders", operator="gt", value="2")])
    assert [row["orders"] for row in dataset.page(0, 10).rows] == [5, 3]

    dataset.set_filters([ColumnFilter(column="revenue", operator="gte", value="17")])
    assert [row["name"] for row in dataset.page(0, 10).rows] == ["Beta", "Gamma"]

    dataset.set_filters([ColumnFilter(column="active", operator="equals", value="true")])
    assert [row["name"] for row in dataset.page(0, 10).rows] == ["Acme", "Gamma"]

    dataset.set_filters([ColumnFilter(column="signup_date", operator="gte", value="2024-01-02")])
    assert [row["name"] for row in dataset.page(0, 10).rows] == ["Beta", "Gamma"]

    dataset.set_filters([ColumnFilter(column="seen_at", operator="lt", value="2025-01-03 00:00:00")])
    assert [row["name"] for row in dataset.page(0, 10).rows] == ["Acme", "Beta"]


def test_empty_and_text_filter_operators_work_for_null_and_string_values(tmp_path: Path) -> None:
    parquet_path = tmp_path / "typed.parquet"
    _write_typed_parquet(parquet_path)

    dataset = open_dataset(parquet_path)

    dataset.set_filters([ColumnFilter(column="name", operator="not_empty")])
    assert dataset.row_count() == 3

    dataset.set_filters([ColumnFilter(column="name", operator="is_empty")])
    assert dataset.page(0, 10).rows == [{"name": None, "orders": None, "revenue": None, "active": None, "signup_date": None, "seen_at": None}]

    dataset.set_filters([ColumnFilter(column="name", operator="starts_with", value="A")])
    assert [row["name"] for row in dataset.page(0, 10).rows] == ["Acme"]

    dataset.set_filters([ColumnFilter(column="name", operator="ends_with", value="a")])
    assert [row["name"] for row in dataset.page(0, 10).rows] == ["Beta", "Gamma"]
