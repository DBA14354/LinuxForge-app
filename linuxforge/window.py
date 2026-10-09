from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from linuxforge.backend import (
    MANAGER_LABELS,
    ManagerStatus,
    SearchHit,
    clear_status_cache,
    detect_managers,
    is_installed,
    pick_source,
    source_from_hit,
)
from linuxforge.catalog import CATEGORIES, CATALOG, CatalogApp
from linuxforge.workers import InstallWorker, SearchWorker

STYLESHEET = """
QMainWindow, QWidget {
    background: #f4f4f4;
    color: #1a1a1a;
    font-size: 13px;
}
QListWidget {
    background: #ececec;
    border: none;
    padding: 8px 0;
    outline: none;
}
QListWidget::item {
    padding: 12px 18px;
}
QListWidget::item:selected {
    background: #2b2b2b;
    color: #ffffff;
}
QLineEdit, QComboBox, QPlainTextEdit, QTableWidget {
    background: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 6px 8px;
    selection-background-color: #2b2b2b;
    selection-color: #ffffff;
}
QPushButton {
    background: #2b2b2b;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 8px 14px;
}
QPushButton:hover {
    background: #111111;
}
QPushButton:disabled {
    background: #b5b5b5;
    color: #f5f5f5;
}
QPushButton#secondary {
    background: #ffffff;
    color: #1a1a1a;
    border: 1px solid #c8c8c8;
}
QPushButton#secondary:hover {
    background: #f0f0f0;
}
QFrame#card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
}
QLabel#title {
    font-size: 22px;
    font-weight: 600;
}
QLabel#muted {
    color: #5c5c5c;
}
QLabel#badge {
    color: #3a3a3a;
    font-size: 12px;
}
QHeaderView::section {
    background: #f7f7f7;
    border: none;
    border-bottom: 1px solid #d8d8d8;
    padding: 6px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LinuxForge")
        self.resize(980, 680)
        self.setStyleSheet(STYLESHEET)

        self.status = detect_managers()
        self._busy = False
        self._thread: QThread | None = None
        self._worker: QWidget | object | None = None
        self._cards: dict[str, AppCard] = {}

        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.nav = QListWidget()
        self.nav.setFixedWidth(168)
        for label in ("Apps", "Search", "Install .deb"):
            self.nav.addItem(QListWidgetItem(label))
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self._on_nav)
        layout.addWidget(self.nav)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 16, 20, 12)
        right_layout.setSpacing(12)
        layout.addWidget(right, 1)

        header = QHBoxLayout()
        title = QLabel("LinuxForge")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        self.manager_label = QLabel(self.status.summary())
        self.manager_label.setObjectName("muted")
        header.addWidget(self.manager_label)
        right_layout.addLayout(header)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_apps_page())
        self.stack.addWidget(self._build_search_page())
        self.stack.addWidget(self._build_deb_page())
        right_layout.addWidget(self.stack, 1)

        log_label = QLabel("Activity")
        log_label.setObjectName("muted")
        right_layout.addWidget(log_label)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setFixedHeight(140)
        self.log.setFont(QFont("monospace", 10))
        right_layout.addWidget(self.log)

        self._append_log(self.status.summary())
        if not self.status.available_names():
            QMessageBox.warning(
                self,
                "LinuxForge",
                "LinuxForge could not find apt, snap, or Flatpak on this computer.",
            )

    def _build_apps_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        tools = QHBoxLayout()
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter apps…")
        self.filter_edit.textChanged.connect(self._refresh_catalog)
        self.category = QComboBox()
        self.category.addItems(CATEGORIES)
        self.category.currentTextChanged.connect(self._refresh_catalog)
        tools.addWidget(self.filter_edit, 1)
        tools.addWidget(self.category)
        layout.addLayout(tools)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.catalog_host = QWidget()
        self.catalog_grid = QGridLayout(self.catalog_host)
        self.catalog_grid.setContentsMargins(0, 8, 0, 8)
        self.catalog_grid.setSpacing(10)
        scroll.setWidget(self.catalog_host)
        layout.addWidget(scroll)
        self._refresh_catalog()
        return page

    def _build_search_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)

        intro = QLabel("Search APT, Snap, and Flatpak for any package.")
        intro.setObjectName("muted")
        layout.addWidget(intro)

        row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Package name, for example vlc")
        self.search_edit.returnPressed.connect(self._run_search)
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._run_search)
        row.addWidget(self.search_edit, 1)
        row.addWidget(search_btn)
        layout.addLayout(row)

        self.results = QTableWidget(0, 4)
        self.results.setHorizontalHeaderLabels(("Name", "Source", "Description", ""))
        self.results.verticalHeader().setVisible(False)
        self.results.setSelectionBehavior(self.results.SelectionBehavior.SelectRows)
        self.results.setEditTriggers(self.results.EditTrigger.NoEditTriggers)
        self.results.horizontalHeader().setStretchLastSection(True)
        self.results.setColumnWidth(0, 180)
        self.results.setColumnWidth(1, 110)
        layout.addWidget(self.results)
        return page

    def _build_deb_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        intro = QLabel(
            "If you already downloaded a .deb file, choose it here. "
            "LinuxForge will install it with APT and pull in any missing pieces."
        )
        intro.setWordWrap(True)
        intro.setObjectName("muted")
        layout.addWidget(intro)

        picker = QHBoxLayout()
        self.deb_path = QLineEdit()
        self.deb_path.setPlaceholderText("/path/to/package.deb")
        browse = QPushButton("Browse")
        browse.setObjectName("secondary")
        browse.clicked.connect(self._browse_deb)
        picker.addWidget(self.deb_path, 1)
        picker.addWidget(browse)
        layout.addLayout(picker)

        self.deb_install = QPushButton("Install package")
        self.deb_install.clicked.connect(self._install_deb)
        layout.addWidget(self.deb_install, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        return page

    def _refresh_catalog(self) -> None:
        while self.catalog_grid.count():
            item = self.catalog_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._cards.clear()

        query = self.filter_edit.text().strip().lower()
        category = self.category.currentText()
        apps = []
        for app in CATALOG:
            if category != "All" and app.category != category:
                continue
            haystack = f"{app.name} {app.summary} {app.category}".lower()
            if query and query not in haystack:
                continue
            apps.append(app)

        if not apps:
            empty = QLabel("No apps match that filter.")
            empty.setObjectName("muted")
            self.catalog_grid.addWidget(empty, 0, 0)
            return

        columns = 2
        for index, app in enumerate(apps):
            card = AppCard(app, self.status, self._install_catalog_app)
            self._cards[app.id] = card
            self.catalog_grid.addWidget(card, index // columns, index % columns)
        self.catalog_grid.setRowStretch((len(apps) - 1) // columns + 1, 1)

    def _on_nav(self, row: int) -> None:
        self.stack.setCurrentIndex(row)

    def _browse_deb(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose a .deb package",
            str(Path.home() / "Downloads"),
            "Debian packages (*.deb)",
        )
        if path:
            self.deb_path.setText(path)

    def _install_catalog_app(self, app: CatalogApp) -> None:
        source = pick_source(app, self.status)
        if source is None:
            QMessageBox.information(
                self,
                "LinuxForge",
                f"None of the install methods for {app.name} are available on this computer.",
            )
            return
        method = MANAGER_LABELS.get(source.manager, source.manager)
        confirm = QMessageBox.question(
            self,
            "Install",
            f"Install {app.name} using {method}?\n\nYou may be asked for your password.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._append_log(f"Installing {app.name} ({method})…")
        self._start_install(InstallWorker(source=source))

    def _install_deb(self) -> None:
        path = self.deb_path.text().strip()
        if not path:
            QMessageBox.information(self, "LinuxForge", "Choose a .deb file first.")
            return
        confirm = QMessageBox.question(
            self,
            "Install",
            f"Install {Path(path).name}?\n\nYou may be asked for your password.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._start_install(InstallWorker(deb_path=path))

    def _install_search_hit(self, hit: SearchHit) -> None:
        method = MANAGER_LABELS.get(hit.manager, hit.manager)
        confirm = QMessageBox.question(
            self,
            "Install",
            f"Install {hit.name} from {method}?\n\nYou may be asked for your password.",
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._start_install(InstallWorker(source=source_from_hit(hit)))

    def _run_search(self) -> None:
        if self._busy:
            return
        query = self.search_edit.text().strip()
        if len(query) < 2:
            QMessageBox.information(self, "LinuxForge", "Type at least two letters to search.")
            return
        self._set_busy(True)
        self.results.setRowCount(0)
        worker = SearchWorker(query, self.status)
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.log_line.connect(self._append_log)
        worker.finished.connect(self._on_search_done)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_search_done(self, hits: list) -> None:
        self._set_busy(False)
        self._append_log(f"Found {len(hits)} result(s).")
        self.results.setRowCount(len(hits))
        for row, hit in enumerate(hits):
            self.results.setItem(row, 0, QTableWidgetItem(hit.name))
            self.results.setItem(row, 1, QTableWidgetItem(MANAGER_LABELS.get(hit.manager, hit.manager)))
            self.results.setItem(row, 2, QTableWidgetItem(hit.description))
            button = QPushButton("Install")
            button.clicked.connect(lambda _=False, item=hit: self._install_search_hit(item))
            self.results.setCellWidget(row, 3, button)
            self.results.setRowHeight(row, 38)

    def _start_install(self, worker: InstallWorker) -> None:
        if self._busy:
            QMessageBox.information(self, "LinuxForge", "Wait for the current task to finish.")
            return
        self._set_busy(True)
        thread = QThread()
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.log_line.connect(self._append_log)
        worker.finished.connect(self._on_install_done)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_install_done(self, code: int) -> None:
        self._set_busy(False)
        clear_status_cache()
        self.status = detect_managers()
        self.manager_label.setText(self.status.summary())
        self._refresh_catalog()
        if code == 0:
            self._append_log("Done.")
            QMessageBox.information(self, "LinuxForge", "Install finished.")
        else:
            self._append_log(f"Finished with exit code {code}.")
            QMessageBox.warning(
                self,
                "LinuxForge",
                "Install did not finish successfully. Check the activity log.",
            )

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.nav.setEnabled(not busy)
        self.stack.setEnabled(not busy)

    def _append_log(self, line: str) -> None:
        self.log.appendPlainText(line)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())


class AppCard(QFrame):
    def __init__(self, app: CatalogApp, status: ManagerStatus, on_install) -> None:
        super().__init__()
        self.setObjectName("card")
        self.setMinimumHeight(118)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)

        top = QHBoxLayout()
        name = QLabel(app.name)
        name_font = QFont()
        name_font.setBold(True)
        name.setFont(name_font)
        top.addWidget(name)
        top.addStretch()
        layout.addLayout(top)

        summary = QLabel(app.summary)
        summary.setWordWrap(True)
        summary.setObjectName("muted")
        layout.addWidget(summary)

        bottom = QHBoxLayout()
        source = pick_source(app, status)
        installed = is_installed(app, status)
        if source:
            method = MANAGER_LABELS.get(source.manager, source.manager)
            badge = QLabel(f"Installed · {method}" if installed else method)
        else:
            badge = QLabel("Unavailable")
        badge.setObjectName("badge")
        bottom.addWidget(badge)
        bottom.addStretch()
        button = QPushButton("Installed" if installed else "Install")
        button.setEnabled(not installed and source is not None)
        button.clicked.connect(lambda: on_install(app))
        bottom.addWidget(button)
        layout.addLayout(bottom)
