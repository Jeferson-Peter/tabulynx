from __future__ import annotations

from pathlib import Path

from tabulynx.core import DatasetSession, open_dataset

__all__ = ["__version__", "DatasetSession", "launch_viewer", "open_dataset"]

__version__ = "0.1.1"


def launch_viewer(path: str | Path | None = None, sheet: str | None = None) -> int:
    from tabulynx.viewer import launch_viewer as _launch_viewer

    return _launch_viewer(path=path, sheet=sheet)
