from __future__ import annotations

from pathlib import Path

from tabulynx.core import DatasetSession, open_dataset
from tabulynx.qt import launch_qt_app


def launch_viewer(path: str | Path | None = None, sheet: str | None = None) -> int:
    dataset: DatasetSession | None = None
    if path is not None:
        dataset = open_dataset(path, sheet=sheet)
    return launch_qt_app(dataset)
