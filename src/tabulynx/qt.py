from __future__ import annotations

import json
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, QPoint, Qt, QSettings
from PySide6.QtGui import QAction, QCloseEvent, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QInputDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QMenu,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from tabulynx.core import ColumnFilter, ColumnStats, DatasetSession, QueryState, SortRule, open_dataset


PAGE_SIZE = 200
PRESETS_PATH = Path.home() / ".tabulynx" / "presets.json"
SQL_HISTORY_PATH = Path.home() / ".tabulynx" / "sql_history.json"
RECENTS_PATH = Path.home() / ".tabulynx" / "recent_files.json"
SESSION_PATH = Path.home() / ".tabulynx" / "last_session.json"
PINNED_PATH = Path.home() / ".tabulynx" / "pinned_files.json"
WINDOW_SETTINGS_ORG = "TabuLynx"
WINDOW_SETTINGS_APP = "Viewer"

SQL_EXAMPLES = {
    "Preview rows": "SELECT *\nFROM current\nLIMIT 50",
    "Count rows": "SELECT COUNT(*) AS row_count\nFROM current",
    "Group by first column": "SELECT <column>, COUNT(*) AS count\nFROM current\nGROUP BY <column>\nORDER BY count DESC",
    "Non-null values": "SELECT *\nFROM current\nWHERE <column> IS NOT NULL\nLIMIT 100",
}

FILTER_LABELS = {
    "contains": "contains",
    "starts_with": "starts with",
    "ends_with": "ends with",
    "equals": "equals",
    "gt": "gt",
    "gte": "gte",
    "lt": "lt",
    "lte": "lte",
    "is_empty": "is empty",
    "not_empty": "not empty",
}

FILTER_OPERATOR_SETS = {
    "text": ["contains", "starts_with", "ends_with", "equals", "is_empty", "not_empty"],
    "int": ["equals", "gt", "gte", "lt", "lte", "is_empty", "not_empty"],
    "float": ["equals", "gt", "gte", "lt", "lte", "is_empty", "not_empty"],
    "date": ["equals", "gt", "gte", "lt", "lte", "is_empty", "not_empty"],
    "datetime": ["equals", "gt", "gte", "lt", "lte", "is_empty", "not_empty"],
    "bool": ["equals", "is_empty", "not_empty"],
}


APP_STYLESHEET = """
QWidget {
    background-color: #020617;
    color: #e5edf7;
    font-family: "Segoe UI";
    font-size: 13px;
}
QLabel {
    background: transparent;
}
QMainWindow {
    background-color: #020617;
}
QTabWidget::pane {
    border: 0;
    background: #020617;
    margin-top: 6px;
}
QTabBar::tab {
    background: #06101f;
    color: #8ea0b8;
    border: 1px solid #132033;
    border-bottom: 0;
    padding: 9px 14px;
    margin-right: 6px;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    min-width: 110px;
}
QTabBar::tab:selected {
    background: #0b1526;
    color: #f8fbff;
    border-color: #22324a;
}
QTabBar::tab:hover:!selected {
    background: #091325;
    color: #dbe7f5;
}
QTabBar::close-button {
    image: none;
    subcontrol-position: right;
    margin-left: 8px;
}
QTabBar::close-button:hover {
    background: #132139;
    border-radius: 6px;
}
QStatusBar {
    background: #06101f;
    color: #8ea0b8;
    border-top: 1px solid #172235;
}
QPushButton, QComboBox {
    background: #0f1b2f;
    color: #e5edf7;
    border: 1px solid #22324a;
    border-radius: 10px;
    padding: 8px 12px;
}
QLineEdit {
    background: #0f1b2f;
    color: #e5edf7;
    border: 1px solid #22324a;
    border-radius: 10px;
    padding: 8px 12px;
}
QPushButton#toolbarButton, QPushButton#secondaryAction, QComboBox#toolbarSelect {
    padding: 6px 10px;
    border-radius: 9px;
    background: #0c172a;
}
QPushButton#toolbarButton {
    color: #dbe7f5;
}
QPushButton#primaryAction {
    padding: 6px 10px;
    border-radius: 9px;
    background: #132139;
    border-color: #29476a;
    color: #f8fbff;
}
QPushButton#primaryAction:hover {
    background: #17304f;
    border-color: #345987;
}
QPushButton#secondaryAction {
    color: #9fb3cb;
}
QLineEdit#topSearch {
    padding: 7px 12px;
    border-radius: 10px;
    background: #091325;
}
QComboBox#querySelect, QLineEdit#queryInput {
    padding: 7px 10px;
    border-radius: 9px;
}
QPlainTextEdit#sqlInput {
    background: #091325;
    color: #dbe7f5;
    border: 1px solid #22324a;
    border-radius: 10px;
    padding: 8px 10px;
    min-height: 38px;
    max-height: 54px;
}
QLabel#inlineCaption {
    color: #7f96b4;
    font-size: 11px;
    font-weight: 600;
}
QPushButton:hover, QComboBox:hover {
    background: #132139;
    border-color: #2d4361;
}
QLineEdit:focus, QComboBox:focus {
    border-color: #3b82f6;
}
QPushButton:pressed {
    background: #0b1628;
}
QComboBox::drop-down {
    border: 0;
    width: 24px;
}
QMenu {
    background: #06101f;
    color: #e5edf7;
    border: 1px solid #172235;
    padding: 6px;
}
QMenu::item {
    padding: 8px 12px;
    border-radius: 8px;
}
QMenu::item:selected {
    background: #132139;
}
QMenu::separator {
    height: 1px;
    background: #172235;
    margin: 6px 4px;
}
QLabel#eyebrow {
    color: #8fb4ff;
    font-size: 11px;
    font-weight: 600;
}
QFrame#heroCard {
    background: transparent;
    border: 0;
    border-bottom: 1px solid #132033;
}
QFrame#tableCard {
    background: transparent;
    border: 0;
}
QFrame#detailsCard {
    background: #050d19;
    border: 1px solid #132033;
    border-radius: 14px;
}
QFrame#topBar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06101f, stop:1 #081425);
    border: 1px solid #132033;
    border-radius: 14px;
}
QFrame#queryCard {
    background: #050d19;
    border: 1px solid #132033;
    border-radius: 14px;
}
QFrame#filterChip {
    background: #0f172a;
    border: 1px solid #22324a;
    border-radius: 999px;
}
QFrame#sortChip {
    background: #111a2d;
    border: 1px solid #2c3f5d;
    border-radius: 999px;
}
QWidget#chipsContainer {
    background: transparent;
}
QPushButton#chipRemove {
    background: transparent;
    border: 0;
    padding: 0 4px;
    min-width: 18px;
    color: #8ea0b8;
}
QPushButton#chipRemove:hover {
    color: #f8fbff;
}
QLabel#chipLabel {
    background: transparent;
    color: #dbe7f5;
    padding: 0;
}
QLabel#sectionLabel {
    color: #8ea0b8;
    font-size: 12px;
}
QLabel#title {
    font-size: 16px;
    font-weight: 700;
    color: #f8fbff;
}
QLabel#meta {
    color: #8ea0b8;
    font-size: 13px;
}
QLabel#subtleMeta {
    color: #6f86a3;
    font-size: 12px;
}
QLabel#detailsTitle {
    font-size: 14px;
    font-weight: 700;
    color: #f8fbff;
}
QLabel#detailsHint {
    color: #8ea0b8;
    font-size: 12px;
}
QListWidget#detailsList {
    background: transparent;
    border: 0;
    outline: 0;
}
QListWidget#detailsList::item {
    background: #08111f;
    border: 1px solid #172235;
    border-radius: 10px;
    margin: 0 0 8px 0;
    padding: 10px 12px;
}
QListWidget#detailsList::item:selected {
    background: #0d1728;
    border-color: #22324a;
}
QTableView {
    background: #08111f;
    alternate-background-color: #0b1526;
    gridline-color: #172235;
    border: 1px solid #172235;
    border-radius: 12px;
    padding: 0;
    selection-background-color: #17365d;
    selection-color: #eff6ff;
    outline: 0;
}
QHeaderView::section {
    background: #0d1728;
    color: #dbe7f5;
    padding: 10px 8px;
    border: 0;
    border-right: 1px solid #172235;
    border-bottom: 1px solid #172235;
    font-weight: 600;
}
"""


class DatasetTableModel(QAbstractTableModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._dataset: DatasetSession | None = None
        self._columns: list[str] = []
        self._total_row_count = 0
        self._page_size = PAGE_SIZE
        self._current_page = 0
        self._page_offset = 0
        self._rows: list[dict[str, Any]] = []

    def set_dataset(self, dataset: DatasetSession) -> None:
        self.beginResetModel()
        self._dataset = dataset
        self._columns = dataset.columns()
        self._current_page = 0
        self._refresh_page()
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.ToolTipRole):
            return None

        value = self._rows[index.row()].get(self._columns[index.column()])
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.isoformat(sep=" ", timespec="seconds")
        if isinstance(value, (date, time)):
            return value.isoformat()
        if isinstance(value, (dict, list)):
            return str(value)
        return value

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._columns[section] if 0 <= section < len(self._columns) else ""
        return str(self._page_offset + section + 1)

    def sort_state(self) -> tuple[str | None, bool]:
        if self._dataset is None:
            return (None, False)
        query = self._dataset.query_state()
        if not query.sorts:
            return (None, False)
        first = query.sorts[0]
        return (first.column, first.descending)

    def sort_by_column(self, column_index: int) -> None:
        if self._dataset is None or not (0 <= column_index < len(self._columns)):
            return

        column_name = self._columns[column_index]
        current_column, current_descending = self.sort_state()
        if current_column == column_name:
            descending = not current_descending
        else:
            descending = False
        self._dataset.set_sort(column_name, descending=descending)
        self.set_dataset(self._dataset)

    def set_page_size(self, page_size: int) -> None:
        page_size = max(1, page_size)
        if page_size == self._page_size:
            return
        self.beginResetModel()
        self._page_size = page_size
        self._current_page = 0
        self._refresh_page()
        self.endResetModel()

    def next_page(self) -> bool:
        if self._current_page + 1 >= self.page_count():
            return False
        self.beginResetModel()
        self._current_page += 1
        self._refresh_page()
        self.endResetModel()
        return True

    def previous_page(self) -> bool:
        if self._current_page <= 0:
            return False
        self.beginResetModel()
        self._current_page -= 1
        self._refresh_page()
        self.endResetModel()
        return True

    def page_count(self) -> int:
        if self._total_row_count == 0:
            return 1
        return ((self._total_row_count - 1) // self._page_size) + 1

    def current_page(self) -> int:
        return self._current_page

    def page_size(self) -> int:
        return self._page_size

    def range_summary(self) -> tuple[int, int, int]:
        if self._total_row_count == 0 or not self._rows:
            return (0, 0, self._total_row_count)
        start = self._page_offset + 1
        end = self._page_offset + len(self._rows)
        return (start, end, self._total_row_count)

    def _refresh_page(self) -> None:
        if self._dataset is None:
            self._rows = []
            self._total_row_count = 0
            self._page_offset = 0
            return
        self._total_row_count = self._dataset.row_count()
        max_page = max(self.page_count() - 1, 0)
        self._current_page = min(self._current_page, max_page)
        self._page_offset = self._current_page * self._page_size
        page = self._dataset.page(self._page_offset, self._page_size)
        self._rows = page.rows


class DatasetTab(QWidget):
    def __init__(
        self,
        dataset: DatasetSession | None = None,
        status_callback: Callable[[str, int], None] | None = None,
        title_changed_callback: Callable[[str], None] | None = None,
        sql_result_callback: Callable[[DatasetSession], None] | None = None,
    ) -> None:
        super().__init__()
        self._status_callback = status_callback
        self._title_changed_callback = title_changed_callback
        self._sql_result_callback = sql_result_callback
        self._dataset: DatasetSession | None = None
        self._model = DatasetTableModel(self)
        self._table = QTableView(self)
        self._sheet_picker = QComboBox(self)
        self._search_input = QLineEdit(self)
        self._sql_input = QPlainTextEdit(self)
        self._sql_toggle_button = QPushButton("SQL", self)
        self._sql_history_button = QPushButton("History", self)
        self._sql_history_menu = QMenu(self)
        self._sql_examples_button = QPushButton("Examples", self)
        self._sql_examples_menu = QMenu(self)
        self._history_back_button = QPushButton("Back", self)
        self._history_forward_button = QPushButton("Forward", self)
        self._filter_column = QComboBox(self)
        self._filter_operator = QComboBox(self)
        self._filter_value = QLineEdit(self)
        self._active_filters_container = QWidget(self)
        self._active_filters_container.setObjectName("chipsContainer")
        self._active_filters_layout = QHBoxLayout(self._active_filters_container)
        self._sort_column = QComboBox(self)
        self._sort_direction = QComboBox(self)
        self._active_sorts_container = QWidget(self)
        self._active_sorts_container.setObjectName("chipsContainer")
        self._active_sorts_layout = QHBoxLayout(self._active_sorts_container)
        self._page_size_picker = QComboBox(self)
        self._page_info_label = QLabel("0-0 of 0", self)
        self._columns_button = QPushButton("Columns", self)
        self._columns_menu = QMenu(self)
        self._column_actions: list[QAction] = []
        self._presets_button = QPushButton("Presets", self)
        self._presets_menu = QMenu(self)
        self._export_button = QPushButton("Export", self)
        self._sql_row_widget = QWidget(self)
        self._details_title = QLabel("Row details", self)
        self._details_hint = QLabel("Select a row to inspect all values.", self)
        self._details_list = QListWidget(self)
        self._file_label = QLabel("No file loaded", self)
        self._meta_label = QLabel("Open a CSV, XLSX, or Parquet file to begin.", self)
        self._top_sheet_label = QLabel("Sheet", self)
        self._selected_column_name: str | None = None
        self._history: list[dict[str, Any]] = []
        self._history_index = -1
        self._restoring_history = False
        self._open_shortcut = QShortcut("Ctrl+O", self)
        self._search_shortcut = QShortcut("Ctrl+F", self)
        self._clear_filters_shortcut = QShortcut("Escape", self)
        self._run_sql_shortcut = QShortcut("Ctrl+Enter", self)

        self._build_ui()
        self._connect_signals()

        if dataset is not None:
            self.load_dataset(dataset)

    def _build_ui(self) -> None:
        self.setStyleSheet(APP_STYLESHEET)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(10)

        top_bar = QFrame(self)
        top_bar.setObjectName("topBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.setSpacing(8)

        open_button_top = QPushButton("Open file", self)
        open_button_top.setObjectName("primaryAction")
        open_button_top.clicked.connect(self.open_file_dialog)
        top_layout.addWidget(open_button_top)

        self._history_back_button.clicked.connect(self._history_back)
        self._history_forward_button.clicked.connect(self._history_forward)
        self._history_back_button.setEnabled(False)
        self._history_forward_button.setEnabled(False)
        self._history_back_button.setObjectName("toolbarButton")
        self._history_forward_button.setObjectName("toolbarButton")
        top_layout.addWidget(self._history_back_button)
        top_layout.addWidget(self._history_forward_button)

        self._search_input.setPlaceholderText("Search across columns")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setMinimumWidth(360)
        self._search_input.setObjectName("topSearch")
        top_layout.addWidget(self._search_input, 1)

        self._columns_button.setMenu(self._columns_menu)
        self._columns_button.setObjectName("toolbarButton")
        top_layout.addWidget(self._columns_button)
        self._presets_button.setMenu(self._presets_menu)
        self._presets_button.setObjectName("toolbarButton")
        top_layout.addWidget(self._presets_button)
        self._export_button.setObjectName("toolbarButton")
        self._export_button.clicked.connect(self._export_current_view)
        top_layout.addWidget(self._export_button)
        self._sql_toggle_button.setObjectName("toolbarButton")
        self._sql_toggle_button.setCheckable(True)
        self._sql_toggle_button.toggled.connect(self._toggle_sql_panel)
        top_layout.addWidget(self._sql_toggle_button)

        self._top_sheet_label.setObjectName("inlineCaption")
        top_layout.addWidget(self._top_sheet_label)
        self._sheet_picker.setMinimumWidth(180)
        self._sheet_picker.setObjectName("toolbarSelect")
        top_layout.addWidget(self._sheet_picker)

        layout.addWidget(top_bar)
        query_card = QFrame(self)
        query_card.setObjectName("queryCard")
        query_layout = QVBoxLayout(query_card)
        query_layout.setContentsMargins(10, 10, 10, 10)
        query_layout.setSpacing(8)

        self._sql_input.setObjectName("sqlInput")
        self._sql_input.setPlaceholderText("SQL on current view, eg: SELECT * FROM current LIMIT 100")
        self._sql_input.setFixedHeight(54)
        run_sql_button = QPushButton("Run SQL", self)
        run_sql_button.setObjectName("primaryAction")
        run_sql_button.clicked.connect(self._run_sql_query)
        clear_sql_button = QPushButton("Clear", self)
        clear_sql_button.setObjectName("secondaryAction")
        clear_sql_button.clicked.connect(self._sql_input.clear)
        self._sql_examples_button.setObjectName("secondaryAction")
        self._sql_examples_button.setMenu(self._sql_examples_menu)
        self._sql_history_button.setObjectName("secondaryAction")
        self._sql_history_button.setMenu(self._sql_history_menu)
        self._rebuild_sql_examples_menu()
        self._rebuild_sql_history_menu()

        sql_row = QHBoxLayout(self._sql_row_widget)
        sql_row.setContentsMargins(0, 0, 0, 0)
        sql_row.setSpacing(8)
        sql_row.addWidget(self._sql_input, 1)
        sql_row.addWidget(self._sql_examples_button)
        sql_row.addWidget(self._sql_history_button)
        sql_row.addWidget(clear_sql_button)
        sql_row.addWidget(run_sql_button)
        self._sql_row_widget.hide()

        self._filter_column.setMinimumWidth(180)
        self._filter_operator.setMinimumWidth(120)
        self._filter_column.setObjectName("querySelect")
        self._filter_operator.setObjectName("querySelect")
        self._filter_value.setObjectName("queryInput")
        self._filter_value.setPlaceholderText("Filter value")
        apply_button = QPushButton("Add filter", self)
        apply_button.setObjectName("primaryAction")
        apply_button.clicked.connect(self._apply_filter)
        clear_button = QPushButton("Clear filters", self)
        clear_button.setObjectName("secondaryAction")
        clear_button.clicked.connect(self._clear_filter)

        filter_row = QHBoxLayout()
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(8)
        filter_row.addWidget(self._filter_column)
        filter_row.addWidget(self._filter_operator)
        filter_row.addWidget(self._filter_value, 1)
        filter_row.addWidget(apply_button)
        filter_row.addWidget(clear_button)

        self._active_filters_layout.setContentsMargins(0, 0, 0, 0)
        self._active_filters_layout.setSpacing(6)
        self._active_filters_layout.addStretch(1)
        self._active_filters_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._active_filters_row_widget = QWidget(self)
        active_filters_row = QHBoxLayout(self._active_filters_row_widget)
        active_filters_row.setContentsMargins(0, 0, 0, 0)
        active_filters_row.setSpacing(8)
        active_filters_label = QLabel("Filters", self)
        active_filters_label.setObjectName("inlineCaption")
        active_filters_row.addWidget(active_filters_label)
        active_filters_row.addWidget(self._active_filters_container, 1)
        self._active_filters_row_widget.hide()

        self._sort_column.setMinimumWidth(180)
        self._sort_direction.setMinimumWidth(120)
        self._sort_column.setObjectName("querySelect")
        self._sort_direction.setObjectName("querySelect")
        self._sort_direction.addItem("asc", False)
        self._sort_direction.addItem("desc", True)
        add_sort_button = QPushButton("Add sort", self)
        add_sort_button.setObjectName("primaryAction")
        add_sort_button.clicked.connect(self._add_sort)
        clear_sorts_button = QPushButton("Clear sorts", self)
        clear_sorts_button.setObjectName("secondaryAction")
        clear_sorts_button.clicked.connect(self._clear_sorts)

        sort_row = QHBoxLayout()
        sort_row.setContentsMargins(0, 0, 0, 0)
        sort_row.setSpacing(8)
        sort_row.addWidget(self._sort_column)
        sort_row.addWidget(self._sort_direction)
        sort_row.addWidget(add_sort_button)
        sort_row.addWidget(clear_sorts_button)
        sort_row.addStretch(1)

        self._active_sorts_layout.setContentsMargins(0, 0, 0, 0)
        self._active_sorts_layout.setSpacing(6)
        self._active_sorts_layout.addStretch(1)
        self._active_sorts_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._active_sorts_row_widget = QWidget(self)
        active_sorts_row = QHBoxLayout(self._active_sorts_row_widget)
        active_sorts_row.setContentsMargins(0, 0, 0, 0)
        active_sorts_row.setSpacing(8)
        active_sorts_label = QLabel("Sorts", self)
        active_sorts_label.setObjectName("inlineCaption")
        active_sorts_row.addWidget(active_sorts_label)
        active_sorts_row.addWidget(self._active_sorts_container, 1)
        self._active_sorts_row_widget.hide()

        query_layout.addWidget(self._sql_row_widget)
        query_layout.addLayout(filter_row)
        query_layout.addWidget(self._active_filters_row_widget)
        query_layout.addLayout(sort_row)
        query_layout.addWidget(self._active_sorts_row_widget)
        layout.addWidget(query_card)

        header = QFrame(self)
        header.setObjectName("tableCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        title_block = QVBoxLayout()
        title_block.setContentsMargins(0, 0, 0, 0)
        title_block.setSpacing(2)
        self._file_label.setObjectName("title")
        self._file_label.setStyleSheet("font-size: 20px;")
        self._meta_label.setObjectName("subtleMeta")
        title_block.addWidget(self._file_label)
        title_block.addWidget(self._meta_label)
        header_layout.addLayout(title_block)
        header_layout.addStretch(1)
        self._page_info_label.setObjectName("meta")
        header_layout.addWidget(self._page_info_label)
        self._page_size_picker.addItems(["25", "50", "100", "200", "500"])
        self._page_size_picker.setCurrentText(str(PAGE_SIZE))
        rows_label = QLabel("Rows", self)
        rows_label.setObjectName("sectionLabel")
        header_layout.addWidget(rows_label)
        header_layout.addWidget(self._page_size_picker)
        previous_button = QPushButton("Previous", self)
        previous_button.clicked.connect(self._previous_page)
        next_button = QPushButton("Next", self)
        next_button.clicked.connect(self._next_page)
        header_layout.addWidget(previous_button)
        header_layout.addWidget(next_button)

        layout.addWidget(header)

        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        self._table.verticalHeader().setDefaultSectionSize(34)
        self._table.verticalHeader().setStyleSheet(
            "background: #0d1728; color: #8ea0b8; border: 0; border-right: 1px solid #172235;"
        )
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.horizontalHeader().setDefaultSectionSize(180)
        self._table.horizontalHeader().setSortIndicatorShown(True)
        self._table.horizontalHeader().setSectionsClickable(True)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().sectionDoubleClicked.connect(self._autosize_column)
        self._table.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.horizontalHeader().customContextMenuRequested.connect(self._open_header_context_menu)
        self._table.setShowGrid(True)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(10)
        content_row.addWidget(self._table, 1)

        details_card = QFrame(self)
        details_card.setObjectName("detailsCard")
        details_card.setMinimumWidth(300)
        details_card.setMaximumWidth(360)
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(10, 10, 10, 10)
        details_layout.setSpacing(8)
        self._details_title.setObjectName("detailsTitle")
        self._details_hint.setObjectName("detailsHint")
        self._details_list.setObjectName("detailsList")
        self._details_list.setSelectionMode(QListWidget.NoSelection)
        details_layout.addWidget(self._details_title)
        details_layout.addWidget(self._details_hint)
        details_layout.addWidget(self._details_list, 1)
        content_row.addWidget(details_card)

        layout.addLayout(content_row, 1)

    def _connect_signals(self) -> None:
        self._sheet_picker.currentTextChanged.connect(self._on_sheet_changed)
        self._search_input.returnPressed.connect(self._apply_search)
        self._search_input.textChanged.connect(self._on_search_text_changed)
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self._table.selectionModel().selectionChanged.connect(self._on_table_selection_changed)
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._open_table_context_menu)
        self._filter_operator.currentIndexChanged.connect(
            lambda _: self._on_filter_operator_changed(self._filter_operator.currentData())
        )
        self._filter_column.currentTextChanged.connect(self._on_filter_column_changed)
        self._filter_value.returnPressed.connect(self._apply_filter)
        self._page_size_picker.currentTextChanged.connect(self._on_page_size_changed)
        self._open_shortcut.activated.connect(self.open_file_dialog)
        self._search_shortcut.activated.connect(self._focus_search)
        self._clear_filters_shortcut.activated.connect(self._clear_filter)
        self._run_sql_shortcut.activated.connect(self._run_sql_query)

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        if self._status_callback is not None:
            self._status_callback(message, timeout)

    def _update_tab_title(self) -> None:
        if self._title_changed_callback is None:
            return
        title = self._dataset.name if self._dataset is not None else "Untitled"
        self._title_changed_callback(title)

    def session_payload(self) -> dict[str, Any] | None:
        if self._dataset is None or self._dataset.is_transient:
            return None
        return {
            "path": str(self._dataset.path),
            "sheet": self._dataset.sheet,
            "query": self._dataset.query_state().to_dict(),
            "page_size": self._model.page_size(),
        }

    def open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open spreadsheet",
            str(Path.cwd()),
            "Data files (*.csv *.xlsx *.parquet)",
        )
        if path:
            self.load_dataset(open_dataset(path))

    def load_dataset(self, dataset: DatasetSession) -> None:
        self._dataset = dataset
        self._model.set_dataset(dataset)
        self._sheet_picker.blockSignals(True)
        self._sheet_picker.clear()
        self._sheet_picker.addItems(dataset.sheet_names())
        self._sheet_picker.setCurrentText(dataset.sheet)
        self._sheet_picker.setEnabled(dataset.suffix == ".xlsx")
        self._sheet_picker.blockSignals(False)
        self._filter_column.clear()
        self._filter_column.addItems(dataset.columns(all_columns=True))
        self._filter_column.setEnabled(True)
        self._sort_column.clear()
        self._sort_column.addItems(dataset.columns(all_columns=True))
        self._sort_column.setEnabled(True)
        self._search_input.blockSignals(True)
        self._search_input.setText(dataset.query_state().search_text or "")
        self._search_input.blockSignals(False)
        self._rebuild_columns_menu()
        self._rebuild_presets_menu()
        self._reset_history()

        self._file_label.setText(dataset.name)
        self._update_meta_label()
        self._update_tab_title()
        self._show_status(f"Loaded {dataset.name}", 4000)
        self._resize_columns()
        self._sync_sort_indicator()
        self._on_filter_column_changed(self._filter_column.currentText())
        self._on_filter_operator_changed(self._filter_operator.currentData())
        self._refresh_active_filters()
        self._refresh_active_sorts()
        self._update_pagination_label()
        self._refresh_row_details()
        self._push_history_state()

    def _on_sheet_changed(self, sheet: str) -> None:
        if not sheet or self._dataset is None or self._dataset.sheet == sheet:
            return
        try:
            self._dataset.set_sheet(sheet)
            self._model.set_dataset(self._dataset)
            self._filter_column.clear()
            self._filter_column.addItems(self._dataset.columns(all_columns=True))
            self._sort_column.clear()
            self._sort_column.addItems(self._dataset.columns(all_columns=True))
            self._rebuild_columns_menu()
            self._rebuild_presets_menu()
            self._update_meta_label()
            self._resize_columns()
            self._sync_sort_indicator()
            self._on_filter_column_changed(self._filter_column.currentText())
            self._refresh_active_filters()
            self._refresh_active_sorts()
            self._update_pagination_label()
            self._refresh_row_details()
        except Exception as exc:
            QMessageBox.critical(self, "Sheet error", str(exc))

    def _on_header_clicked(self, column_index: int) -> None:
        if self._dataset is None:
            return
        if 0 <= column_index < len(self._model._columns):
            self._selected_column_name = self._model._columns[column_index]
        self._model.sort_by_column(column_index)
        self._sync_sort_indicator()
        self._update_meta_label()
        self._refresh_active_sorts()
        self._update_pagination_label()
        self._refresh_row_details()
        sorts = self._dataset.query_state().sorts or []
        if sorts:
            self._show_status(
                "Sorted by " + " -> ".join(item.label(index + 1) for index, item in enumerate(sorts)),
                3000,
            )

    def _on_table_selection_changed(self, *_args: Any) -> None:
        if self._table.selectionModel().selectedRows():
            self._selected_column_name = None
        self._refresh_row_details()

    def _open_table_context_menu(self, position: QPoint) -> None:
        index = self._table.indexAt(position)
        if not index.isValid() or self._dataset is None:
            return

        column_name = self._model._columns[index.column()]
        row_data = self._model._rows[index.row()]
        raw_value = row_data.get(column_name)
        display_value = self._format_detail_value(raw_value)

        menu = QMenu(self)
        copy_cell_action = QAction("Copy cell", self)
        copy_cell_action.triggered.connect(lambda: self._copy_text(display_value, "Cell copied."))
        menu.addAction(copy_cell_action)

        copy_row_action = QAction("Copy row", self)
        copy_row_action.triggered.connect(lambda: self._copy_row(index.row()))
        menu.addAction(copy_row_action)

        menu.addSeparator()

        filter_equals_action = QAction(f"Filter {column_name} = {display_value}", self)
        filter_equals_action.triggered.connect(
            lambda: self._apply_quick_filter(column_name, raw_value, operator="equals")
        )
        menu.addAction(filter_equals_action)

        if self._dataset.column_type_name(column_name) == "text" and raw_value not in (None, ""):
            filter_contains_action = QAction(f"Filter {column_name} contains {display_value}", self)
            filter_contains_action.triggered.connect(
                lambda: self._apply_quick_filter(column_name, raw_value, operator="contains")
            )
            menu.addAction(filter_contains_action)

        hide_column_action = QAction(f"Hide column {column_name}", self)
        hide_column_action.triggered.connect(lambda: self._hide_column_from_context(column_name))
        menu.addAction(hide_column_action)

        menu.exec(self._table.viewport().mapToGlobal(position))

    def _open_header_context_menu(self, position: QPoint) -> None:
        if self._dataset is None:
            return

        header = self._table.horizontalHeader()
        column_index = header.logicalIndexAt(position)
        if not (0 <= column_index < len(self._model._columns)):
            return

        column_name = self._model._columns[column_index]
        column_type = self._dataset.column_type_name(column_name)
        menu = QMenu(self)

        search_action = QAction(f"Search in {column_name}", self)
        search_action.triggered.connect(lambda: self._prompt_column_search(column_name, column_type))
        menu.addAction(search_action)

        clear_column_filters_action = QAction(f"Clear filters on {column_name}", self)
        clear_column_filters_action.triggered.connect(lambda: self._clear_column_filters(column_name))
        menu.addAction(clear_column_filters_action)

        menu.addSeparator()

        sort_asc_action = QAction(f"Sort {column_name} asc", self)
        sort_asc_action.triggered.connect(lambda: self._set_single_sort(column_name, descending=False))
        menu.addAction(sort_asc_action)

        sort_desc_action = QAction(f"Sort {column_name} desc", self)
        sort_desc_action.triggered.connect(lambda: self._set_single_sort(column_name, descending=True))
        menu.addAction(sort_desc_action)

        menu.addSeparator()

        hide_column_action = QAction(f"Hide column {column_name}", self)
        hide_column_action.triggered.connect(lambda: self._hide_column_from_context(column_name))
        menu.addAction(hide_column_action)

        menu.exec(header.mapToGlobal(position))

    def _resize_columns(self) -> None:
        header = self._table.horizontalHeader()
        for column_index in range(min(self._model.columnCount(), 8)):
            header.resizeSection(column_index, 180)

    def _autosize_column(self, column_index: int) -> None:
        if 0 <= column_index < self._model.columnCount():
            self._table.resizeColumnToContents(column_index)
            self._show_status(f"Autosized column: {self._model._columns[column_index]}", 2000)

    def _focus_search(self) -> None:
        self._search_input.setFocus()
        self._search_input.selectAll()

    def _toggle_sql_panel(self, visible: bool) -> None:
        self._sql_row_widget.setVisible(visible)
        self._sql_toggle_button.setText("Hide SQL" if visible else "SQL")
        if visible:
            self._sql_input.setFocus()

    def _load_sql_history(self) -> list[str]:
        if not SQL_HISTORY_PATH.exists():
            return []
        try:
            payload = json.loads(SQL_HISTORY_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, str) and item.strip()]

    def _write_sql_history(self, queries: list[str]) -> None:
        SQL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        SQL_HISTORY_PATH.write_text(
            json.dumps(queries[:20], indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    def _record_sql_query(self, query: str) -> None:
        normalized = query.strip()
        if not normalized:
            return
        history = [item for item in self._load_sql_history() if item != normalized]
        history.insert(0, normalized)
        self._write_sql_history(history)
        self._rebuild_sql_history_menu()

    def _set_sql_text(self, query: str) -> None:
        self._sql_input.setPlainText(query)
        if not self._sql_toggle_button.isChecked():
            self._sql_toggle_button.setChecked(True)
        self._sql_input.setFocus()

    def _rebuild_sql_examples_menu(self) -> None:
        self._sql_examples_menu.clear()
        for label, query in SQL_EXAMPLES.items():
            action = QAction(label, self)
            action.triggered.connect(lambda _checked=False, sql=query: self._set_sql_text(sql))
            self._sql_examples_menu.addAction(action)

    def _rebuild_sql_history_menu(self) -> None:
        self._sql_history_menu.clear()
        history = self._load_sql_history()
        if not history:
            empty_action = QAction("No SQL history", self)
            empty_action.setEnabled(False)
            self._sql_history_menu.addAction(empty_action)
            self._sql_history_button.setEnabled(False)
            return

        self._sql_history_button.setEnabled(True)
        for query in history:
            label = " ".join(query.split())
            if len(label) > 80:
                label = label[:77] + "..."
            action = QAction(label, self)
            action.setToolTip(query)
            action.triggered.connect(lambda _checked=False, sql=query: self._set_sql_text(sql))
            self._sql_history_menu.addAction(action)

        self._sql_history_menu.addSeparator()
        clear_action = QAction("Clear SQL history", self)
        clear_action.triggered.connect(self._clear_sql_history)
        self._sql_history_menu.addAction(clear_action)

    def _clear_sql_history(self) -> None:
        self._write_sql_history([])
        self._rebuild_sql_history_menu()
        self._show_status("SQL history cleared.", 3000)

    def _run_sql_query(self) -> None:
        if self._dataset is None:
            self._show_status("Load a dataset before running SQL.", 3000)
            return

        query = self._sql_input.toPlainText().strip()
        if not query:
            self._show_status("Enter a SQL query first.", 3000)
            return

        try:
            result_frame = self._dataset.sql_query(query, table_name="current")
            result_name = f"SQL - {self._dataset.name}"
            result_name = f"SQL · {self._dataset.name}"
            result_name = f"SQL - {self._dataset.name}"
            result_dataset = DatasetSession.from_frame(result_frame, name=result_name)
            self._record_sql_query(query)
            if self._sql_result_callback is not None:
                self._sql_result_callback(result_dataset)
            self._show_status("SQL query executed.", 3000)
        except Exception as exc:
            QMessageBox.critical(self, "SQL error", str(exc))

    def _copy_text(self, text: str, status_message: str) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self._show_status(status_message, 2000)

    def _copy_row(self, row_index: int) -> None:
        if not (0 <= row_index < len(self._model._rows)):
            return
        row_data = self._model._rows[row_index]
        values = [self._format_detail_value(row_data.get(column)) for column in self._model._columns]
        self._copy_text("\t".join(values), "Row copied.")

    def _apply_quick_filter(self, column: str, value: Any, operator: str) -> None:
        if self._dataset is None:
            return
        filter_value = None if value is None else str(value)
        try:
            self._dataset.add_filter(ColumnFilter(column=column, operator=operator, value=filter_value))
            self._refresh_current_dataset_view()
            self._show_status(f"Quick filter added on {column}.", 3000)
        except Exception as exc:
            QMessageBox.critical(self, "Quick filter error", str(exc))

    def _hide_column_from_context(self, column: str) -> None:
        if self._dataset is None:
            return
        all_columns = self._dataset.columns(all_columns=True)
        visible_columns = list(self._dataset.query_state().visible_columns or all_columns)
        if column not in visible_columns:
            return
        if len(visible_columns) == 1:
            self._show_status("At least one column must stay visible.", 3000)
            return
        visible_columns = [item for item in visible_columns if item != column]
        self._dataset.set_visible_columns(visible_columns)
        self._refresh_current_dataset_view()
        self._show_status(f"Column hidden: {column}", 3000)

    def _prompt_column_search(self, column: str, column_type: str) -> None:
        if self._dataset is None:
            return

        placeholder_map = {
            "text": "Text to match",
            "int": "Integer value",
            "float": "Numeric value",
            "date": "YYYY-MM-DD",
            "datetime": "YYYY-MM-DD HH:MM:SS",
            "bool": "true / false",
        }
        operator_map = {
            "text": "contains",
            "int": "equals",
            "float": "equals",
            "date": "equals",
            "datetime": "equals",
            "bool": "equals",
        }

        value, accepted = QInputDialog.getText(
            self,
            f"Search in {column}",
            placeholder_map.get(column_type, "Value:"),
        )
        if not accepted or not value.strip():
            return

        self._apply_quick_filter(column, value.strip(), operator_map.get(column_type, "contains"))

    def _clear_column_filters(self, column: str) -> None:
        if self._dataset is None:
            return
        filters = [item for item in (self._dataset.query_state().filters or []) if item.column != column]
        self._dataset.set_filters(filters or None)
        self._refresh_current_dataset_view()
        self._show_status(f"Cleared filters on {column}.", 3000)

    def _set_single_sort(self, column: str, descending: bool) -> None:
        if self._dataset is None:
            return
        self._dataset.set_sort(column, descending=descending)
        self._refresh_current_dataset_view()
        self._show_status(f"Sorted {column} {'desc' if descending else 'asc'}.", 3000)

    def _sync_sort_indicator(self) -> None:
        current_column, descending = self._model.sort_state()
        header = self._table.horizontalHeader()
        if current_column is None:
            header.setSortIndicator(-1, Qt.AscendingOrder)
            return
        try:
            column_index = self._model._columns.index(current_column)
        except ValueError:
            header.setSortIndicator(-1, Qt.AscendingOrder)
            return
        header.setSortIndicator(
            column_index,
            Qt.DescendingOrder if descending else Qt.AscendingOrder,
        )

    def _on_filter_operator_changed(self, operator: str | None) -> None:
        operator = operator or ""
        needs_value = operator not in {"is_empty", "not_empty"}
        self._filter_value.setEnabled(needs_value)
        if not needs_value:
            self._filter_value.clear()

    def _on_filter_column_changed(self, column: str) -> None:
        if self._dataset is None or not column:
            return

        column_type = self._dataset.column_type_name(column)
        placeholder_map = {
            "text": "Text value",
            "int": "Integer value",
            "float": "Numeric value",
            "date": "YYYY-MM-DD",
            "datetime": "YYYY-MM-DD HH:MM:SS",
            "bool": "true / false",
        }

        current_operator = self._filter_operator.currentData()
        operators = FILTER_OPERATOR_SETS.get(column_type, FILTER_OPERATOR_SETS["text"])
        self._filter_operator.blockSignals(True)
        self._filter_operator.clear()
        for operator in operators:
            self._filter_operator.addItem(FILTER_LABELS[operator], operator)
        if current_operator in operators:
            self._filter_operator.setCurrentIndex(operators.index(current_operator))
        self._filter_operator.blockSignals(False)
        self._filter_value.setPlaceholderText(placeholder_map.get(column_type, "Filter value"))
        self._on_filter_operator_changed(self._filter_operator.currentData())

    def _apply_filter(self) -> None:
        if self._dataset is None:
            return

        operator = self._filter_operator.currentData()
        value = self._filter_value.text().strip()
        if operator not in {"is_empty", "not_empty"} and not value:
            self._show_status("Enter a filter value first.", 3000)
            return

        try:
            self._dataset.add_filter(
                ColumnFilter(
                    column=self._filter_column.currentText(),
                    operator=operator,
                    value=value or None,
                )
            )
            self._refresh_current_dataset_view()
            self._show_status("Filter added.", 3000)
        except Exception as exc:
            QMessageBox.critical(self, "Filter error", str(exc))

    def _clear_filter(self) -> None:
        if self._dataset is None:
            return
        self._dataset.clear_filters()
        self._filter_value.clear()
        self._refresh_current_dataset_view()
        self._show_status("Filters cleared.", 3000)

    def _refresh_current_dataset_view(self, push_history: bool = True) -> None:
        if self._dataset is None:
            return
        self._model.set_dataset(self._dataset)
        self._rebuild_columns_menu()
        self._rebuild_presets_menu()
        self._update_meta_label()
        self._sync_sort_indicator()
        self._refresh_active_filters()
        self._refresh_active_sorts()
        self._update_pagination_label()
        self._refresh_row_details()
        if push_history and not self._restoring_history:
            self._push_history_state()

    def _update_meta_label(self) -> None:
        if self._dataset is None:
            self._meta_label.setText("Open a CSV, XLSX, or Parquet file to begin.")
            return
        query = self._dataset.query_state()
        filter_count = len(query.filters or [])
        search_suffix = f"search: {query.search_text}" if query.search_text else "no search"
        filter_suffix = f"{filter_count} filters" if filter_count else "all rows"
        visible_count = len(self._dataset.columns())
        total_columns = len(self._dataset.columns(all_columns=True))
        source_suffix = "optimized workbook cache" if self._dataset.uses_excel_cache else "source file"
        row_count = self._model.range_summary()[2]
        self._meta_label.setText(
            f"{row_count:,} rows, {visible_count}/{total_columns} columns, "
            f"{filter_suffix}, {search_suffix}, {source_suffix}: {self._dataset.path}"
        )
        self._columns_button.setText(
            f"Columns {visible_count}/{total_columns}" if visible_count != total_columns else "Columns"
        )

    def _on_page_size_changed(self, value: str) -> None:
        if not value.strip():
            return
        self._model.set_page_size(int(value))
        self._update_pagination_label()
        if not self._restoring_history:
            self._push_history_state()

    def _previous_page(self) -> None:
        if self._model.previous_page():
            self._update_pagination_label()

    def _next_page(self) -> None:
        if self._model.next_page():
            self._update_pagination_label()

    def _update_pagination_label(self) -> None:
        start, end, total = self._model.range_summary()
        current_page = self._model.current_page() + 1
        total_pages = self._model.page_count()
        self._page_info_label.setText(f"{start}-{end} of {total}  |  page {current_page}/{total_pages}")

    def _refresh_active_filters(self) -> None:
        while self._active_filters_layout.count():
            item = self._active_filters_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if self._dataset is None:
            self._active_filters_row_widget.hide()
            return

        filters = self._dataset.query_state().filters or []
        if not filters:
            self._active_filters_row_widget.hide()
            return

        self._active_filters_row_widget.show()
        for index, item in enumerate(filters):
            chip = QFrame(self)
            chip.setObjectName("filterChip")
            chip.setAttribute(Qt.WA_StyledBackground, True)
            chip.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(12, 4, 6, 4)
            chip_layout.setSpacing(6)
            label = QLabel(item.label(), chip)
            label.setObjectName("chipLabel")
            remove = QPushButton("x", chip)
            remove.setObjectName("chipRemove")
            remove.clicked.connect(lambda _checked=False, idx=index: self._remove_filter_chip(idx))
            chip_layout.addWidget(label)
            chip_layout.addWidget(remove)
            self._active_filters_layout.addWidget(chip)

        self._active_filters_layout.addStretch(1)

    def _remove_filter_chip(self, index: int) -> None:
        if self._dataset is None:
            return
        self._dataset.remove_filter_at(index)
        self._refresh_current_dataset_view()
        self._show_status("Filter removed.", 3000)

    def _refresh_active_sorts(self) -> None:
        while self._active_sorts_layout.count():
            item = self._active_sorts_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if self._dataset is None:
            self._active_sorts_row_widget.hide()
            return

        sorts = self._dataset.query_state().sorts or []
        if not sorts:
            self._active_sorts_row_widget.hide()
            return

        self._active_sorts_row_widget.show()
        for index, item in enumerate(sorts):
            chip = QFrame(self)
            chip.setObjectName("sortChip")
            chip.setAttribute(Qt.WA_StyledBackground, True)
            chip.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(12, 4, 6, 4)
            chip_layout.setSpacing(6)
            label = QLabel(item.label(index + 1), chip)
            label.setObjectName("chipLabel")
            remove = QPushButton("x", chip)
            remove.setObjectName("chipRemove")
            remove.clicked.connect(lambda _checked=False, idx=index: self._remove_sort_chip(idx))
            chip_layout.addWidget(label)
            chip_layout.addWidget(remove)
            self._active_sorts_layout.addWidget(chip)

        self._active_sorts_layout.addStretch(1)

    def _remove_sort_chip(self, index: int) -> None:
        if self._dataset is None:
            return
        self._dataset.remove_sort_at(index)
        self._refresh_current_dataset_view()
        self._show_status("Sort removed.", 3000)

    def _add_sort(self) -> None:
        if self._dataset is None:
            return
        column = self._sort_column.currentText()
        if not column:
            return
        descending = bool(self._sort_direction.currentData())
        self._dataset.add_sort(column, descending=descending)
        self._refresh_current_dataset_view()
        self._show_status("Sort added.", 3000)

    def _clear_sorts(self) -> None:
        if self._dataset is None:
            return
        self._dataset.clear_sort()
        self._refresh_current_dataset_view()
        self._show_status("Sorts cleared.", 3000)

    def _apply_search(self) -> None:
        if self._dataset is None:
            return
        self._dataset.set_search_text(self._search_input.text())
        self._refresh_current_dataset_view()
        query = self._dataset.query_state()
        if query.search_text:
            self._show_status(f"Search applied: {query.search_text}", 3000)
        else:
            self._show_status("Search cleared.", 3000)

    def _on_search_text_changed(self, value: str) -> None:
        if self._dataset is None:
            return
        if value.strip():
            return
        if self._dataset.query_state().search_text is None:
            return
        self._dataset.clear_search_text()
        self._refresh_current_dataset_view()
        self._show_status("Search cleared.", 3000)

    def _rebuild_columns_menu(self) -> None:
        self._columns_menu.clear()
        self._column_actions.clear()
        if self._dataset is None:
            self._columns_button.setEnabled(False)
            return

        self._columns_button.setEnabled(True)
        all_columns = self._dataset.columns(all_columns=True)
        visible_columns = set(self._dataset.query_state().visible_columns or all_columns)

        show_all_action = QAction("Show all columns", self)
        show_all_action.triggered.connect(self._show_all_columns)
        self._columns_menu.addAction(show_all_action)
        self._columns_menu.addSeparator()

        for column in all_columns:
            action = QAction(column, self)
            action.setCheckable(True)
            action.setChecked(column in visible_columns)
            action.toggled.connect(lambda checked, name=column: self._toggle_column_visibility(name, checked))
            self._columns_menu.addAction(action)
            self._column_actions.append(action)

    def _rebuild_presets_menu(self) -> None:
        self._presets_menu.clear()
        save_action = QAction("Save current preset", self)
        save_action.triggered.connect(self._save_current_preset)
        self._presets_menu.addAction(save_action)

        presets = self._load_presets()
        if not presets:
            empty_action = QAction("No saved presets", self)
            empty_action.setEnabled(False)
            self._presets_menu.addAction(empty_action)
            return

        self._presets_menu.addSeparator()
        for name in sorted(presets):
            apply_action = QAction(name, self)
            apply_action.triggered.connect(lambda _checked=False, preset_name=name: self._apply_preset(preset_name))
            self._presets_menu.addAction(apply_action)

        self._presets_menu.addSeparator()
        for name in sorted(presets):
            delete_action = QAction(f"Delete: {name}", self)
            delete_action.triggered.connect(
                lambda _checked=False, preset_name=name: self._delete_preset(preset_name)
            )
            self._presets_menu.addAction(delete_action)

    def _show_all_columns(self) -> None:
        if self._dataset is None:
            return
        self._dataset.set_visible_columns(None)
        self._refresh_current_dataset_view()
        self._show_status("Showing all columns.", 3000)

    def _toggle_column_visibility(self, column: str, visible: bool) -> None:
        if self._dataset is None:
            return

        all_columns = self._dataset.columns(all_columns=True)
        current_visible = list(self._dataset.query_state().visible_columns or all_columns)
        if visible:
            if column not in current_visible:
                current_visible.append(column)
        else:
            current_visible = [item for item in current_visible if item != column]
            if not current_visible:
                self._show_status("At least one column must stay visible.", 3000)
                self._rebuild_columns_menu()
                return

        ordered_visible = [item for item in all_columns if item in current_visible]
        if len(ordered_visible) == len(all_columns):
            self._dataset.set_visible_columns(None)
        else:
            self._dataset.set_visible_columns(ordered_visible)
        self._refresh_current_dataset_view()

    def _load_presets(self) -> dict[str, dict[str, Any]]:
        if not PRESETS_PATH.exists():
            return {}
        try:
            return json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_presets(self, presets: dict[str, dict[str, Any]]) -> None:
        PRESETS_PATH.parent.mkdir(parents=True, exist_ok=True)
        PRESETS_PATH.write_text(json.dumps(presets, indent=2, ensure_ascii=True), encoding="utf-8")

    def _save_current_preset(self) -> None:
        if self._dataset is None:
            self._show_status("Load a dataset before saving a preset.", 3000)
            return

        name, accepted = QInputDialog.getText(self, "Save preset", "Preset name:")
        if not accepted or not name.strip():
            return

        preset_name = name.strip()
        presets = self._load_presets()
        presets[preset_name] = {
            "query": self._dataset.query_state().to_dict(),
            "page_size": self._model.page_size(),
        }
        self._write_presets(presets)
        self._rebuild_presets_menu()
        self._show_status(f"Preset saved: {preset_name}", 3000)

    def _apply_preset(self, preset_name: str) -> None:
        if self._dataset is None:
            return

        presets = self._load_presets()
        payload = presets.get(preset_name)
        if not payload:
            self._show_status("Preset not found.", 3000)
            self._rebuild_presets_menu()
            return

        try:
            state = QueryState.from_dict(payload.get("query", {}))
            self._dataset.apply_query_state(state)
            self._search_input.blockSignals(True)
            self._search_input.setText(state.search_text or "")
            self._search_input.blockSignals(False)
            page_size = int(payload.get("page_size", PAGE_SIZE))
            self._page_size_picker.setCurrentText(str(page_size))
            self._refresh_current_dataset_view()
            self._show_status(f"Preset applied: {preset_name}", 3000)
        except Exception as exc:
            QMessageBox.critical(self, "Preset error", str(exc))

    def _delete_preset(self, preset_name: str) -> None:
        presets = self._load_presets()
        if preset_name not in presets:
            return
        del presets[preset_name]
        self._write_presets(presets)
        self._rebuild_presets_menu()
        self._show_status(f"Preset deleted: {preset_name}", 3000)

    def _refresh_row_details(self) -> None:
        self._details_list.clear()
        if self._dataset is None:
            self._details_title.setText("Dataset summary")
            self._details_hint.setText("Open a dataset to inspect it.")
            return

        if self._selected_column_name:
            self._render_column_stats(self._selected_column_name)
            return

        if not self._model._rows:
            self._render_dataset_profile()
            return

        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            self._render_dataset_profile()
            return

        row_index = indexes[0].row()
        if not (0 <= row_index < len(self._model._rows)):
            self._render_dataset_profile()
            return

        row_data = self._model._rows[row_index]
        self._details_title.setText("Row details")
        self._details_hint.setText(
            f"Showing row {self._model._page_offset + row_index + 1} on this result set."
        )

        for column in self._model._columns:
            value = self._format_detail_value(row_data.get(column))
            item = QListWidgetItem(f"{column}\n{value}")
            self._details_list.addItem(item)

    def _render_column_stats(self, column: str) -> None:
        if self._dataset is None:
            return

        stats = self._dataset.column_stats(column)
        self._details_title.setText(f"Column: {column}")
        self._details_hint.setText("Click a row to switch back to row details.")

        for line in self._format_stats_lines(stats):
            self._details_list.addItem(QListWidgetItem(line))

    def _render_dataset_profile(self) -> None:
        if self._dataset is None:
            return

        self._details_title.setText("Dataset summary")
        self._details_hint.setText("Quick overview. Select a row for values or click a column for detailed stats.")
        for line in self._format_profile_lines():
            self._details_list.addItem(QListWidgetItem(line))

    def _format_stats_lines(self, stats: ColumnStats) -> list[str]:
        lines = [
            f"Type\n{stats.type_name}",
            f"Nulls\n{stats.null_count}",
            f"Non-null values\n{stats.non_null_count}",
            f"Distinct values\n{stats.distinct_count}",
            f"Minimum\n{self._format_detail_value(stats.min_value)}",
            f"Maximum\n{self._format_detail_value(stats.max_value)}",
        ]
        if stats.top_values:
            top_values = "\n".join(f"{value} ({count})" for value, count in stats.top_values)
            lines.append(f"Top values\n{top_values}")
        return lines

    def _format_profile_lines(self) -> list[str]:
        if self._dataset is None:
            return []

        columns = self._dataset.columns()
        type_counts: dict[str, int] = {}
        numeric_columns: list[str] = []
        temporal_columns: list[str] = []
        text_columns: list[str] = []
        boolean_columns: list[str] = []

        for column in columns:
            type_name = self._dataset.column_type_name(column)
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
            if type_name in {"int", "float"}:
                numeric_columns.append(column)
            elif type_name in {"date", "datetime"}:
                temporal_columns.append(column)
            elif type_name == "bool":
                boolean_columns.append(column)
            else:
                text_columns.append(column)

        type_summary = ", ".join(f"{name}: {count}" for name, count in sorted(type_counts.items()))
        row_count = self._model.range_summary()[2]
        lines = [
            f"Rows\n{row_count}",
            f"Columns\n{len(columns)}",
            f"Column types\n{type_summary or '-'}",
            f"Numeric columns\n{', '.join(numeric_columns[:8]) or '-'}",
            f"Temporal columns\n{', '.join(temporal_columns[:8]) or '-'}",
            f"Boolean columns\n{', '.join(boolean_columns[:8]) or '-'}",
            f"Text columns\n{', '.join(text_columns[:8]) or '-'}",
        ]
        return lines

    def _format_detail_value(self, value: Any) -> str:
        if value is None:
            return "-"
        if isinstance(value, datetime):
            return value.isoformat(sep=" ", timespec="seconds")
        if isinstance(value, (date, time)):
            return value.isoformat()
        if isinstance(value, (dict, list)):
            return str(value)
        return str(value)

    def _export_current_view(self) -> None:
        if self._dataset is None:
            self._show_status("Load a dataset before exporting.", 3000)
            return

        base_name = Path(self._dataset.name).stem + "_view"
        default_path = str(self._dataset.path.with_name(base_name + ".csv"))
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export current view",
            default_path,
            "CSV (*.csv);;Parquet (*.parquet)",
        )
        if not path:
            return

        chosen_path = Path(path)
        if not chosen_path.suffix:
            if "Parquet" in selected_filter:
                chosen_path = chosen_path.with_suffix(".parquet")
            else:
                chosen_path = chosen_path.with_suffix(".csv")

        try:
            exported_path = self._dataset.export_current_view(chosen_path)
            self._show_status(f"Exported current view to {exported_path}", 5000)
        except Exception as exc:
            QMessageBox.critical(self, "Export error", str(exc))

    def _snapshot_state(self) -> dict[str, Any]:
        if self._dataset is None:
            return {"query": None, "page_size": self._model.page_size()}
        return {
            "query": self._dataset.query_state().to_dict(),
            "page_size": self._model.page_size(),
        }

    def _reset_history(self) -> None:
        self._history = []
        self._history_index = -1
        self._update_history_buttons()

    def _push_history_state(self) -> None:
        snapshot = self._snapshot_state()
        if self._history_index >= 0 and self._history[self._history_index] == snapshot:
            self._update_history_buttons()
            return

        if self._history_index < len(self._history) - 1:
            self._history = self._history[: self._history_index + 1]

        self._history.append(snapshot)
        self._history_index = len(self._history) - 1
        self._update_history_buttons()

    def _update_history_buttons(self) -> None:
        self._history_back_button.setEnabled(self._history_index > 0)
        self._history_forward_button.setEnabled(0 <= self._history_index < len(self._history) - 1)

    def _history_back(self) -> None:
        if self._history_index <= 0:
            return
        self._history_index -= 1
        self._restore_history_state()

    def _history_forward(self) -> None:
        if self._history_index >= len(self._history) - 1:
            return
        self._history_index += 1
        self._restore_history_state()

    def _restore_history_state(self) -> None:
        if self._dataset is None or not (0 <= self._history_index < len(self._history)):
            return

        snapshot = self._history[self._history_index]
        query_payload = snapshot.get("query") or {}
        page_size = int(snapshot.get("page_size", PAGE_SIZE))

        self._restoring_history = True
        try:
            state = QueryState.from_dict(query_payload)
            self._dataset.apply_query_state(state)
            self._search_input.blockSignals(True)
            self._search_input.setText(state.search_text or "")
            self._search_input.blockSignals(False)
            self._page_size_picker.blockSignals(True)
            self._page_size_picker.setCurrentText(str(page_size))
            self._page_size_picker.blockSignals(False)
            self._model.set_page_size(page_size)
            self._refresh_current_dataset_view(push_history=False)
            self._show_status("History restored.", 2000)
        finally:
            self._restoring_history = False
            self._update_history_buttons()


class MainWindow(QMainWindow):
    def __init__(self, dataset: DatasetSession | None = None) -> None:
        super().__init__()
        self.setWindowTitle("TabuLynx")
        self.resize(1440, 900)
        self._settings = QSettings(WINDOW_SETTINGS_ORG, WINDOW_SETTINGS_APP)

        self._tabs = QTabWidget(self)
        self._tabs.setDocumentMode(True)
        self._tabs.setTabsClosable(True)
        self._tabs.tabCloseRequested.connect(self._close_tab)
        self._tabs.currentChanged.connect(lambda _index: self._rebuild_recent_menu())

        open_button = QPushButton("Open file", self)
        open_button.clicked.connect(self.open_file_dialog)
        recent_button = QPushButton("Recent", self)
        self._recent_menu = QMenu(self)
        recent_button.setMenu(self._recent_menu)

        corner_widget = QWidget(self)
        corner_layout = QHBoxLayout(corner_widget)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.setSpacing(8)
        corner_layout.addWidget(recent_button)
        corner_layout.addWidget(open_button)
        self._tabs.setCornerWidget(corner_widget, Qt.TopRightCorner)

        self.setCentralWidget(self._tabs)
        self.setStatusBar(QStatusBar(self))
        self._rebuild_recent_menu()
        self._restore_window_state()

        if dataset is not None:
            self._add_dataset_tab(dataset)
        elif not self._restore_last_session():
            self._add_dataset_tab(None)
        else:
            pass

    def _show_status(self, message: str, timeout: int = 3000) -> None:
        self.statusBar().showMessage(message, timeout)

    def _add_dataset_tab(self, dataset: DatasetSession | None) -> None:
        tab: DatasetTab | None = None

        def update_title(title: str) -> None:
            if tab is None:
                return
            index = self._tabs.indexOf(tab)
            if index >= 0:
                self._tabs.setTabText(index, title)

        tab = DatasetTab(
            dataset=dataset,
            status_callback=self._show_status,
            title_changed_callback=update_title,
            sql_result_callback=self._add_sql_result_tab,
        )
        title = dataset.name if dataset is not None else "Untitled"
        index = self._tabs.addTab(tab, title)
        self._tabs.setCurrentIndex(index)
        if dataset is not None and not dataset.is_transient:
            self._record_recent_dataset(dataset)

    def _add_sql_result_tab(self, dataset: DatasetSession) -> None:
        self._add_dataset_tab(dataset)

    def open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open spreadsheet",
            str(Path.cwd()),
            "Data files (*.csv *.xlsx *.parquet)",
        )
        if not path:
            return

        dataset = open_dataset(path)
        current_widget = self._tabs.currentWidget()
        if isinstance(current_widget, DatasetTab) and current_widget._dataset is None:
            current_widget.load_dataset(dataset)
            self._tabs.setTabText(self._tabs.currentIndex(), dataset.name)
            self._record_recent_dataset(dataset)
        else:
            self._add_dataset_tab(dataset)

    def _close_tab(self, index: int) -> None:
        widget = self._tabs.widget(index)
        self._tabs.removeTab(index)
        if widget is not None:
            widget.deleteLater()
        if self._tabs.count() == 0:
            self._add_dataset_tab(None)

    def _load_recent_files(self) -> list[dict[str, str]]:
        if not RECENTS_PATH.exists():
            return []
        try:
            payload = json.loads(RECENTS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, dict) and item.get("path")]

    def _write_recent_files(self, items: list[dict[str, str]]) -> None:
        RECENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        RECENTS_PATH.write_text(json.dumps(items[:12], indent=2, ensure_ascii=True), encoding="utf-8")

    def _load_pinned_files(self) -> list[dict[str, str]]:
        if not PINNED_PATH.exists():
            return []
        try:
            payload = json.loads(PINNED_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, dict) and item.get("path")]

    def _write_pinned_files(self, items: list[dict[str, str]]) -> None:
        PINNED_PATH.parent.mkdir(parents=True, exist_ok=True)
        PINNED_PATH.write_text(json.dumps(items[:12], indent=2, ensure_ascii=True), encoding="utf-8")

    def _record_recent_dataset(self, dataset: DatasetSession) -> None:
        items = self._load_recent_files()
        normalized_path = str(dataset.path)
        items = [item for item in items if item.get("path") != normalized_path]
        items.insert(
            0,
            {
                "path": normalized_path,
                "name": dataset.name,
                "sheet": dataset.sheet,
            },
        )
        self._write_recent_files(items)
        self._rebuild_recent_menu()

    def _rebuild_recent_menu(self) -> None:
        self._recent_menu.clear()
        current_widget = self._tabs.currentWidget()
        current_dataset = current_widget._dataset if isinstance(current_widget, DatasetTab) else None

        pin_action = QAction("Pin current file", self)
        pin_action.setEnabled(current_dataset is not None)
        pin_action.triggered.connect(self._pin_current_file)
        self._recent_menu.addAction(pin_action)

        unpin_action = QAction("Unpin current file", self)
        unpin_action.setEnabled(current_dataset is not None and self._is_pinned(str(current_dataset.path)))
        unpin_action.triggered.connect(self._unpin_current_file)
        self._recent_menu.addAction(unpin_action)

        self._recent_menu.addSeparator()

        pinned_items = self._load_pinned_files()
        if pinned_items:
            pinned_header = QAction("Pinned", self)
            pinned_header.setEnabled(False)
            self._recent_menu.addAction(pinned_header)
            for item in pinned_items:
                label = item.get("name") or Path(item["path"]).name
                action = QAction(label, self)
                action.setToolTip(item["path"])
                action.triggered.connect(
                    lambda _checked=False, payload=item: self._open_recent_file(payload)
                )
                self._recent_menu.addAction(action)
            self._recent_menu.addSeparator()

        items = self._load_recent_files()
        if not items:
            empty_action = QAction("No recent files", self)
            empty_action.setEnabled(False)
            self._recent_menu.addAction(empty_action)
            return

        for item in items:
            label = item.get("name") or Path(item["path"]).name
            action = QAction(label, self)
            action.setToolTip(item["path"])
            action.triggered.connect(
                lambda _checked=False, payload=item: self._open_recent_file(payload)
            )
            self._recent_menu.addAction(action)

        self._recent_menu.addSeparator()
        clear_action = QAction("Clear recent files", self)
        clear_action.triggered.connect(self._clear_recent_files)
        self._recent_menu.addAction(clear_action)

    def _is_pinned(self, path: str) -> bool:
        return any(item.get("path") == path for item in self._load_pinned_files())

    def _pin_current_file(self) -> None:
        current_widget = self._tabs.currentWidget()
        current_dataset = current_widget._dataset if isinstance(current_widget, DatasetTab) else None
        if current_dataset is None:
            return

        items = self._load_pinned_files()
        normalized_path = str(current_dataset.path)
        items = [item for item in items if item.get("path") != normalized_path]
        items.insert(
            0,
            {
                "path": normalized_path,
                "name": current_dataset.name,
                "sheet": current_dataset.sheet,
            },
        )
        self._write_pinned_files(items)
        self._rebuild_recent_menu()
        self._show_status(f"Pinned: {current_dataset.name}", 3000)

    def _unpin_current_file(self) -> None:
        current_widget = self._tabs.currentWidget()
        current_dataset = current_widget._dataset if isinstance(current_widget, DatasetTab) else None
        if current_dataset is None:
            return

        normalized_path = str(current_dataset.path)
        items = [item for item in self._load_pinned_files() if item.get("path") != normalized_path]
        self._write_pinned_files(items)
        self._rebuild_recent_menu()
        self._show_status(f"Unpinned: {current_dataset.name}", 3000)

    def _open_recent_file(self, payload: dict[str, str]) -> None:
        path = Path(payload["path"])
        if not path.exists():
            QMessageBox.warning(
                self,
                "Recent file missing",
                f"The file no longer exists:\n{path}",
            )
            items = [item for item in self._load_recent_files() if item.get("path") != str(path)]
            self._write_recent_files(items)
            self._rebuild_recent_menu()
            return

        dataset = open_dataset(path, sheet=payload.get("sheet") or None)
        self._add_dataset_tab(dataset)

    def _clear_recent_files(self) -> None:
        self._write_recent_files([])
        self._rebuild_recent_menu()
        self._show_status("Recent files cleared.", 3000)

    def _load_last_session(self) -> dict[str, Any] | None:
        if not SESSION_PATH.exists():
            return None
        try:
            payload = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
        return payload if isinstance(payload, dict) else None

    def _write_last_session(self, payload: dict[str, Any]) -> None:
        SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
        SESSION_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    def _restore_last_session(self) -> bool:
        payload = self._load_last_session()
        if not payload:
            return False

        restored_any = False
        current_index = int(payload.get("current_index", 0))
        for item in payload.get("tabs", []):
            path = Path(item.get("path", ""))
            if not path.exists():
                continue
            try:
                dataset = open_dataset(path, sheet=item.get("sheet") or None)
                query_payload = item.get("query") or {}
                dataset.apply_query_state(QueryState.from_dict(query_payload))
                tab = DatasetTab(
                    dataset=dataset,
                    status_callback=self._show_status,
                    title_changed_callback=lambda title, _tab_ref=None: None,
                    sql_result_callback=self._add_sql_result_tab,
                )
                page_size = int(item.get("page_size", PAGE_SIZE))
                tab._page_size_picker.setCurrentText(str(page_size))
                tab._model.set_page_size(page_size)

                def update_title(title: str, target=tab) -> None:
                    index = self._tabs.indexOf(target)
                    if index >= 0:
                        self._tabs.setTabText(index, title)

                tab._title_changed_callback = update_title
                index = self._tabs.addTab(tab, dataset.name)
                restored_any = True
            except Exception:
                continue

        if restored_any:
            safe_index = max(0, min(current_index, self._tabs.count() - 1))
            self._tabs.setCurrentIndex(safe_index)
        return restored_any

    def _save_last_session(self) -> None:
        tabs: list[dict[str, Any]] = []
        for index in range(self._tabs.count()):
            widget = self._tabs.widget(index)
            if not isinstance(widget, DatasetTab):
                continue
            payload = widget.session_payload()
            if payload is not None:
                tabs.append(payload)

        self._write_last_session(
            {
                "current_index": self._tabs.currentIndex(),
                "tabs": tabs,
            }
        )

    def _restore_window_state(self) -> None:
        geometry = self._settings.value("window_geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

    def _save_window_state(self) -> None:
        self._settings.setValue("window_geometry", self.saveGeometry())

    def closeEvent(self, event: QCloseEvent) -> None:
        self._save_window_state()
        self._save_last_session()
        super().closeEvent(event)


def launch_qt_app(dataset: DatasetSession | None = None) -> int:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(dataset=dataset)
    window.show()
    return app.exec()
