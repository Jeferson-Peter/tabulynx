# TabuLynx

TabuLynx is a local desktop spreadsheet-style viewer for tabular files. It is meant for opening, exploring, filtering, sorting, querying, and exporting local datasets without starting a web server or using a full spreadsheet suite.

It supports:

- CSV
- XLSX
- Parquet

The core is built on `polars`, and the desktop interface is built with `PySide6`.

## Features

- Native desktop table viewer for local tabular files
- Data-type aware filters for text, numbers, booleans, dates, and datetimes
- Multi-filter and multi-sort support
- Global search across columns
- Column visibility controls
- Explicit pagination with configurable page size
- Row details side panel
- Column statistics side panel
- Dataset summary side panel
- Export of the current view to CSV or Parquet
- SQL queries against the current view using Polars SQL
- Temporary SQL result tabs
- SQL examples, SQL clear action, and local SQL history
- Query presets
- Multiple files in tabs
- Recent files and pinned files
- Last-session restore
- Query history per tab with back/forward navigation
- Context menu actions on cells and headers
- Optimized XLSX browsing through cached Parquet conversion
- Keyboard shortcuts for common actions

## Quick Start

Install dependencies:

```bash
uv sync
```

Run the desktop app:

```bash
uv run tabulynx
```

Open a file directly:

```bash
uv run tabulynx open ./your-file.csv
```

You can also open:

```bash
uv run tabulynx open ./your-file.xlsx
uv run tabulynx open ./your-file.parquet
```

## Basic Workflow

1. Open a `csv`, `xlsx`, or `parquet` file.
2. Use the global search box to quickly reduce the visible rows.
3. Add filters and sorts from the query area.
4. Use the `Columns` menu to show or hide columns.
5. Select a row to inspect full row values in the side panel.
6. Click a column header to view column statistics.
7. Use `Export` to save the current view as CSV or Parquet.

The current view means the result after applying search, filters, sorts, and visible columns.

## SQL Support

The SQL panel uses Polars SQL and runs against the current tab's current view. The available table name is always `current`.

Example:

```sql
SELECT customer, revenue
FROM current
WHERE revenue > 100
ORDER BY revenue DESC
LIMIT 50
```

Supported today:

- Querying the current tab as `current`
- `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`, and common Polars SQL expressions supported by Polars
- Aggregations and grouping supported by Polars SQL
- SQL over the current view, so active search, filters, sorts, and visible columns are applied before the SQL query runs
- Opening SQL results as temporary result tabs
- Quick SQL examples
- Local SQL history

Not supported yet:

- Cross-tab SQL queries or joins between multiple open files
- Persistent SQL result tabs across app restarts
- SQL editing of source files
- Database features such as indexes, transactions, stored procedures, or user-defined SQL functions
- Full DuckDB/PostgreSQL-style SQL compatibility

## XLSX Handling

Excel files are handled differently from CSV and Parquet.

For `xlsx`, TabuLynx:

- Discovers sheet names up front
- Lets you switch sheets in the desktop UI
- Opens workbooks with a read-only ingestion path
- Converts the selected sheet into cached Parquet
- Uses the cached Parquet file for faster browsing, filtering, sorting, SQL, and pagination

This keeps the UI experience consistent while avoiding repeated direct Excel reads during exploration.

Important notes:

- The first open of a large sheet may take longer while the cache is created.
- The cache is invalidated when the source file metadata changes.
- Excel formulas are read as stored values when available.
- TabuLynx does not recalculate Excel formulas.
- TabuLynx does not preserve Excel formatting, formulas, merged cells, charts, or styles during export.

## Keyboard Shortcuts

- `Ctrl+O`: open file
- `Ctrl+F`: focus global search
- `Ctrl+Enter`: run SQL in the current tab
- `Esc`: clear filters in the current tab
- Double-click a column header divider: autosize the column

## Context Menus

Right-click a table cell for quick actions such as:

- Copy cell
- Copy row
- Filter by selected value
- Search/filter by selected text
- Hide the clicked column

Right-click a column header for quick column actions such as:

- Search in that column
- Clear filters for that column
- Sort ascending or descending
- Hide the column

## Presets, Recent Files, And Session State

TabuLynx stores local app state under `~/.tabulynx/`.

Current local state includes:

- Query presets
- SQL history
- Recent files
- Pinned files
- Last-session restore data
- XLSX Parquet cache

The app state is local to your machine and is not synced or uploaded by TabuLynx.

## Library Usage

You can also use the core library directly:

```python
from tabulynx import open_dataset

dataset = open_dataset("your-file.xlsx", sheet="Sheet1")

print(dataset.columns())
print(dataset.row_count())
print(dataset.page(0, 100))
```

Apply filters and sorts:

```python
from tabulynx.core import ColumnFilter, SortRule, open_dataset

dataset = open_dataset("your-file.parquet")
dataset.add_filter(ColumnFilter(column="revenue", operator="gte", value="100"))
dataset.set_sorts([SortRule(column="revenue", descending=True)])

page = dataset.page(offset=0, limit=50)
print(page.rows)
```

Run SQL from Python:

```python
dataset = open_dataset("your-file.csv")

result = dataset.sql_query(
    """
    SELECT customer, SUM(revenue) AS total_revenue
    FROM current
    GROUP BY customer
    ORDER BY total_revenue DESC
    """
)

print(result)
```

## Sample Data

Sample data for local testing lives in:

- `sample_data/filters_demo.csv`
- `sample_data/filters_demo.parquet`

Regenerate the sample files:

```bash
uv run python scripts/create_sample_data.py
```

Generate a larger sample:

```bash
uv run python scripts/create_sample_data.py --rows 20000
```

## Run Tests

Install development dependencies:

```bash
uv sync --group dev
```

Run the test suite:

```bash
uv run pytest -q
```

## Project Structure

```text
src/tabulynx/
  __init__.py
  __main__.py
  cli.py
  core.py
  qt.py
  viewer.py

sample_data/
  filters_demo.csv
  filters_demo.parquet

scripts/
  create_sample_data.py

tests/
  test_core.py
```

## Current Limitations

- TabuLynx is a viewer and exploration tool, not a full spreadsheet editor.
- It does not currently edit cells or save changes back into the original source file.
- XLSX support uses cached Parquet conversion per selected sheet; very large or irregular workbooks may take time on first open.
- Excel formulas are not recalculated by TabuLynx.
- Excel formatting, styles, merged cells, charts, and workbook-specific layout features are not preserved.
- SQL currently runs only against the current tab's current view as the table `current`.
- SQL result tabs are temporary and are not restored in the next session.
- Cross-tab SQL joins are not supported yet.
- Extremely large datasets may still depend on available memory and local disk cache.
- The UI is focused on desktop use and is not intended for browser or mobile workflows.

## Roadmap Ideas

- Cross-tab SQL queries
- Better SQL editor experience
- More test coverage for UI state and Excel edge cases
- More robust XLSX type inference for irregular workbooks
- Optional app packaging with PyInstaller or Nuitka
- Screenshots and release packaging documentation
