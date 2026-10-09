from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from linuxforge.backend import SearchHit, Source, install_local_deb, install_source, search_packages
from linuxforge.backend import ManagerStatus


class InstallWorker(QObject):
    log_line = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, source: Source | None = None, deb_path: str | None = None) -> None:
        super().__init__()
        self._source = source
        self._deb_path = deb_path

    def run(self) -> None:
        try:
            if self._deb_path:
                code = install_local_deb(self._deb_path, self.log_line.emit)
            elif self._source:
                code = install_source(self._source, self.log_line.emit)
            else:
                self.log_line.emit("Nothing to install.")
                code = 1
        except Exception as exc:  # noqa: BLE001 — surface unexpected errors in the log
            self.log_line.emit(f"Unexpected error: {exc}")
            code = 1
        self.finished.emit(code)


class SearchWorker(QObject):
    log_line = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, query: str, status: ManagerStatus) -> None:
        super().__init__()
        self._query = query
        self._status = status

    def run(self) -> None:
        try:
            hits = search_packages(self._query, self._status, self.log_line.emit)
        except Exception as exc:  # noqa: BLE001
            self.log_line.emit(f"Search failed: {exc}")
            hits = []
        self.finished.emit(hits)
