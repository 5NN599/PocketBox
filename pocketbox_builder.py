"""PocketBox Builder - create .pbox packages without modifying source files."""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from pocketbox_format import build_payload, scan_source_tree
from pocketbox_settings import get_language, set_language, translate_error_text

APP_TITLE = "PocketBox Builder"
APP_VERSION = "0.3.1"

TEXT = {
    "en": {
        "subtitle": "Bundle a folder into one .pbox file and launch it with a double-click.",
        "source_title": "01  Source folder",
        "source_subtitle": "Choose the folder containing the program EXE, DLLs, data, and subfolders. The source is never modified.",
        "choose_folder": "Browse...",
        "source_placeholder": r"Example: D:\Games\MyGame",
        "target_title": "02  Startup program",
        "target_subtitle": "Choose the EXE that should start when this .pbox package is opened.",
        "working_directory": "Use the startup EXE's folder as the working directory",
        "output_title": "03  Output .pbox package",
        "output_subtitle": "This creates a data package. The PocketBox launcher must be installed to open .pbox files.",
        "output_placeholder": "Choose where to save the .pbox package",
        "save_location": "Browse...",
        "create": "Create .pbox",
        "logs": "Build log",
        "footer": "Original files are preserved. A temporary working copy is extracted when the package runs and removed after its tracked process tree exits. PocketBox is not a security sandbox.",
        "ready": "Ready. Choose a source folder to begin.",
        "select_source_dialog": "Select source folder",
        "no_exe_title": "No startup program found",
        "no_exe": "No .exe file was found in the selected folder.",
        "scan_failed": "Could not scan the folder",
        "source_prefix": "Source folder: {path}",
        "candidate_count": "Found {count} possible startup program(s).",
        "save_dialog": "Save .pbox package",
        "file_filter": "PocketBox package (*.pbox)",
        "need_source_title": "Source folder required",
        "need_source": "Choose a source folder first.",
        "need_target_title": "Startup program required",
        "need_target": "Choose the EXE to launch.",
        "need_output_title": "Output path required",
        "need_output": "Choose where to save the .pbox package.",
        "output_inside_title": "Invalid output location",
        "output_inside": "Save the .pbox package outside the source folder.",
        "overwrite_title": "Confirm overwrite",
        "overwrite": "The following package already exists. Overwrite it?\n\n{path}",
        "build_start": "Starting package creation: {path}",
        "build_done": "Created: {path}",
        "success_title": "PocketBox package created",
        "success": ".pbox package created successfully.\n\n{path}\n\nThe original folder and files are unchanged.\nDouble-click the .pbox file to open it with the registered PocketBox launcher.",
        "failure_title": "Package creation failed",
        "failure_log": "Error: {error}",
        "worker_start": "[1/2] Reading the source folder and creating the .pbox package...",
        "source_kept": "  The original files will not be moved or deleted.",
        "adding": "  Adding: {path}",
        "included": "  Included {count:,} file(s) / {size:,} uncompressed bytes",
        "language": "Language",
        "language_save_failed": "Could not save the language preference: {error}",
    },
    "ko": {
        "subtitle": "폴더를 하나의 .pbox 파일로 묶고 더블클릭으로 실행합니다.",
        "source_title": "01  원본 폴더",
        "source_subtitle": "프로그램 EXE, DLL, 데이터 및 하위 폴더가 들어 있는 폴더를 선택하세요. 원본은 변경되지 않습니다.",
        "choose_folder": "찾아보기...",
        "source_placeholder": r"예: D:\Games\MyGame",
        "target_title": "02  시작 프로그램",
        "target_subtitle": "이 .pbox 패키지를 열었을 때 실행할 EXE를 선택하세요.",
        "working_directory": "시작 EXE가 있는 폴더를 작업 디렉터리로 사용",
        "output_title": "03  결과 .pbox 패키지",
        "output_subtitle": "데이터 패키지를 생성합니다. .pbox 파일을 열려면 PocketBox 런처가 설치되어 있어야 합니다.",
        "output_placeholder": ".pbox 패키지를 저장할 위치를 선택하세요",
        "save_location": "찾아보기...",
        "create": ".pbox 만들기",
        "logs": "작업 로그",
        "footer": "원본 파일은 보존됩니다. 패키지 실행 시 임시 작업용 복사본을 추출하고 추적 중인 프로세스 트리가 종료되면 삭제합니다. PocketBox는 보안 샌드박스가 아닙니다.",
        "ready": "준비되었습니다. 원본 폴더를 선택하세요.",
        "select_source_dialog": "원본 폴더 선택",
        "no_exe_title": "시작 프로그램을 찾지 못함",
        "no_exe": "선택한 폴더에서 .exe 파일을 찾지 못했습니다.",
        "scan_failed": "폴더 검사 실패",
        "source_prefix": "원본 폴더: {path}",
        "candidate_count": "시작 프로그램 후보 {count}개를 찾았습니다.",
        "save_dialog": ".pbox 패키지 저장",
        "file_filter": "PocketBox 패키지 (*.pbox)",
        "need_source_title": "원본 폴더 필요",
        "need_source": "먼저 원본 폴더를 선택하세요.",
        "need_target_title": "시작 프로그램 필요",
        "need_target": "실행할 EXE를 선택하세요.",
        "need_output_title": "저장 경로 필요",
        "need_output": "결과 .pbox 패키지를 저장할 위치를 선택하세요.",
        "output_inside_title": "저장 위치 오류",
        "output_inside": "원본 폴더 바깥에 .pbox 패키지를 저장하세요.",
        "overwrite_title": "덮어쓰기 확인",
        "overwrite": "다음 패키지가 이미 존재합니다. 덮어쓸까요?\n\n{path}",
        "build_start": "패키징 시작: {path}",
        "build_done": "생성 완료: {path}",
        "success_title": "PocketBox 패키지 생성 완료",
        "success": ".pbox 패키지를 성공적으로 생성했습니다.\n\n{path}\n\n원본 폴더와 파일은 변경되지 않았습니다.\n.pbox 파일을 더블클릭하면 등록된 PocketBox 런처로 열립니다.",
        "failure_title": "패키징 실패",
        "failure_log": "오류: {error}",
        "worker_start": "[1/2] 원본 폴더를 읽어 .pbox 패키지를 만듭니다...",
        "source_kept": "  원본 파일은 이동하거나 삭제하지 않습니다.",
        "adding": "  추가 중: {path}",
        "included": "  포함 완료: 파일 {count:,}개 / 압축 전 크기 {size:,}바이트",
        "language": "언어",
        "language_save_failed": "언어 설정을 저장할 수 없습니다: {error}",
    },
}


def tr(language: str, key: str, **values: object) -> str:
    template = TEXT.get(language, TEXT["en"])[key]
    return template.format(**values)


def resource_path(relative_path: str) -> Path:
    """Resolve bundled resources in both source and PyInstaller builds."""
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return bundle_root / relative_path


class BuildWorker(QThread):
    log = Signal(str)
    progress = Signal(int)
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, source: Path, target_relative: str, output: Path,
                 workdir_is_target: bool, language: str, parent=None):
        super().__init__(parent)
        self.source = source
        self.target_relative = target_relative
        self.output = output
        self.workdir_is_target = workdir_is_target
        self.language = language

    def run(self) -> None:
        temporary_output = self.output.with_name(
            f".{self.output.name}.{uuid.uuid4().hex}.building"
        )
        try:
            self.log.emit(tr(self.language, "worker_start"))
            self.log.emit(tr(self.language, "source_kept"))

            def on_progress(done: int, total: int, relative: str) -> None:
                self.progress.emit(int(done * 95 / max(total, 1)))
                self.log.emit(tr(self.language, "adding", path=relative))

            file_count, total_size = build_payload(
                self.source,
                self.target_relative,
                temporary_output,
                working_directory=("target_dir" if self.workdir_is_target else "bundle_root"),
                progress=on_progress,
            )
            self.log.emit(tr(self.language, "included", count=file_count, size=total_size))
            self.progress.emit(97)
            self.output.parent.mkdir(parents=True, exist_ok=True)
            os.replace(temporary_output, self.output)
            self.progress.emit(100)
            self.succeeded.emit(str(self.output))
        except Exception as exc:
            try:
                temporary_output.unlink(missing_ok=True)
            except OSError:
                pass
            self.failed.emit(translate_error_text(exc, self.language))


class Card(QFrame):
    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(18, 16, 18, 16)
        self.layout_box.setSpacing(10)
        self.heading = QLabel(title)
        self.heading.setObjectName("CardTitle")
        self.layout_box.addWidget(self.heading)
        self.sub = QLabel(subtitle)
        self.sub.setObjectName("Muted")
        self.sub.setWordWrap(True)
        self.layout_box.addWidget(self.sub)

    def set_text(self, title: str, subtitle: str) -> None:
        self.heading.setText(title)
        self.sub.setText(subtitle)
        self.sub.setVisible(bool(subtitle))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.language = get_language()
        self.setWindowIcon(QIcon(str(resource_path("assets/pocketbox.ico"))))
        self.setMinimumSize(790, 710)
        self.resize(920, 800)
        self.source_dir: Path | None = None
        self.worker: BuildWorker | None = None

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(26, 24, 26, 24)
        root.setSpacing(14)

        header = QHBoxLayout()
        brand = QLabel("PB")
        brand.setObjectName("BrandIcon")
        brand.setAlignment(Qt.AlignCenter)
        brand.setFixedSize(54, 54)
        header.addWidget(brand)
        title_col = QVBoxLayout()
        self.app_title_label = QLabel("PocketBox")
        self.app_title_label.setObjectName("AppTitle")
        self.subtitle_label = QLabel()
        self.subtitle_label.setObjectName("Muted")
        title_col.addWidget(self.app_title_label)
        title_col.addWidget(self.subtitle_label)
        header.addLayout(title_col)
        header.addStretch(1)
        self.version_label = QLabel(f"BUILDER  v{APP_VERSION}")
        self.version_label.setObjectName("Version")
        header.addWidget(self.version_label, alignment=Qt.AlignTop)
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("한국어", "ko")
        self.language_combo.setMinimumWidth(112)
        self.language_combo.setCurrentIndex(0 if self.language == "en" else 1)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        header.addWidget(self.language_combo, alignment=Qt.AlignTop)
        root.addLayout(header)

        self.source_card = Card("", "")
        source_row = QHBoxLayout()
        self.source_edit = QLineEdit()
        self.source_edit.setReadOnly(True)
        self.source_button = QPushButton()
        self.source_button.clicked.connect(self.choose_source)
        source_row.addWidget(self.source_edit, 1)
        source_row.addWidget(self.source_button)
        self.source_card.layout_box.addLayout(source_row)
        root.addWidget(self.source_card)

        self.target_card = Card("", "")
        self.target_combo = QComboBox()
        self.target_combo.setMinimumHeight(40)
        self.target_combo.setEnabled(False)
        self.target_card.layout_box.addWidget(self.target_combo)
        self.workdir_check = QCheckBox()
        self.workdir_check.setChecked(True)
        self.target_card.layout_box.addWidget(self.workdir_check)
        root.addWidget(self.target_card)

        self.output_card = Card("", "")
        output_row = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_button = QPushButton()
        self.output_button.clicked.connect(self.choose_output)
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(self.output_button)
        self.output_card.layout_box.addLayout(output_row)
        root.addWidget(self.output_card)

        action_row = QHBoxLayout()
        self.build_button = QPushButton()
        self.build_button.setObjectName("PrimaryButton")
        self.build_button.setMinimumHeight(48)
        self.build_button.clicked.connect(self.start_build)
        action_row.addWidget(self.build_button)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(18)
        action_row.addWidget(self.progress_bar, 1)
        root.addLayout(action_row)

        self.log_card = Card("", "")
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(1000)
        self.log_view.setMinimumHeight(170)
        self.log_card.layout_box.addWidget(self.log_view)
        root.addWidget(self.log_card, 1)

        self.footer = QLabel()
        self.footer.setObjectName("WarningText")
        self.footer.setWordWrap(True)
        root.addWidget(self.footer)

        self.setCentralWidget(central)
        self.apply_style()
        self.retranslate_ui()
        self.log(tr(self.language, "ready"))

    def apply_style(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background: #10151d; color: #e8edf5; font-family: 'Segoe UI'; font-size: 10pt; }
            QLabel#AppTitle { font-size: 23pt; font-weight: 700; color: #f4f7fb; }
            QLabel#BrandIcon { background: #2867b2; color: white; border-radius: 14px; font-size: 18pt; font-weight: 800; }
            QLabel#Muted { color: #98a6b8; }
            QLabel#Version { color: #7f91a8; font-size: 8pt; font-weight: 700; }
            QFrame#Card { background: #171f2b; border: 1px solid #293647; border-radius: 13px; }
            QLabel#CardTitle { color: #eaf1fb; font-size: 11pt; font-weight: 700; }
            QLineEdit, QComboBox, QPlainTextEdit { background: #0e141c; border: 1px solid #344459; border-radius: 8px; padding: 10px; color: #edf3fb; selection-background-color: #2867b2; }
            QComboBox::drop-down { border: 0; width: 28px; }
            QPushButton { background: #263548; border: 1px solid #3a4d64; border-radius: 8px; padding: 9px 15px; color: #eef4fb; font-weight: 600; }
            QPushButton:hover { background: #31445c; }
            QPushButton:disabled { color: #78879a; background: #1c2734; border-color: #2a3543; }
            QPushButton#PrimaryButton { background: #2867b2; border: 1px solid #3f82d2; font-size: 11pt; }
            QPushButton#PrimaryButton:hover { background: #3479ca; }
            QCheckBox { spacing: 9px; color: #cbd5e2; }
            QCheckBox::indicator { width: 17px; height: 17px; }
            QProgressBar { background: #0c1219; border: 1px solid #344459; border-radius: 7px; text-align: center; color: #dce8f6; }
            QProgressBar::chunk { background: #2d80d3; border-radius: 6px; }
            QLabel#WarningText { color: #e5bd76; font-size: 9pt; padding: 2px 3px; }
        """)

    def retranslate_ui(self) -> None:
        language = self.language
        self.setWindowTitle(f"PocketBox Builder {APP_VERSION}")
        self.subtitle_label.setText(tr(language, "subtitle"))
        self.source_card.set_text(tr(language, "source_title"), tr(language, "source_subtitle"))
        self.source_edit.setPlaceholderText(tr(language, "source_placeholder"))
        self.source_button.setText(tr(language, "choose_folder"))
        self.target_card.set_text(tr(language, "target_title"), tr(language, "target_subtitle"))
        self.workdir_check.setText(tr(language, "working_directory"))
        self.output_card.set_text(tr(language, "output_title"), tr(language, "output_subtitle"))
        self.output_edit.setPlaceholderText(tr(language, "output_placeholder"))
        self.output_button.setText(tr(language, "save_location"))
        self.build_button.setText(tr(language, "create"))
        self.log_card.set_text(tr(language, "logs"), "")
        self.footer.setText(tr(language, "footer"))
        self.language_combo.setToolTip(tr(language, "language"))

    def log(self, text: str) -> None:
        self.log_view.appendPlainText(text)

    def change_language(self, _index: int) -> None:
        language = self.language_combo.currentData()
        if language not in ("en", "ko") or language == self.language:
            return
        self.language = language
        try:
            set_language(language)
        except OSError as exc:
            QMessageBox.warning(
                self, "PocketBox",
                tr(self.language, "language_save_failed", error=exc),
            )
        self.retranslate_ui()

    def choose_source(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, tr(self.language, "select_source_dialog"))
        if not folder:
            return
        source = Path(folder)
        try:
            items = scan_source_tree(source)
            executables = [item["path"] for item in items
                           if item["kind"] == "file" and item["path"].lower().endswith(".exe")]
            if not executables:
                QMessageBox.warning(self, tr(self.language, "no_exe_title"), tr(self.language, "no_exe"))
                return
        except Exception as exc:
            QMessageBox.critical(self, tr(self.language, "scan_failed"), translate_error_text(exc, self.language))
            return

        self.source_dir = source.resolve()
        self.source_edit.setText(str(self.source_dir))
        self.target_combo.clear()
        for relative in executables:
            self.target_combo.addItem(relative, relative)
        self.target_combo.setEnabled(True)
        self.target_combo.setCurrentIndex(
            next((i for i, rel in enumerate(executables) if "/" not in rel), 0)
        )
        self.output_edit.setText(str(self.source_dir.parent / f"{self.source_dir.name}.pbox"))
        self.log(tr(self.language, "source_prefix", path=self.source_dir))
        self.log(tr(self.language, "candidate_count", count=len(executables)))

    def choose_output(self) -> None:
        default = self.output_edit.text().strip()
        path, _ = QFileDialog.getSaveFileName(
            self, tr(self.language, "save_dialog"), default, tr(self.language, "file_filter")
        )
        if path:
            if not path.lower().endswith(".pbox"):
                path += ".pbox"
            self.output_edit.setText(path)

    def _set_busy(self, busy: bool) -> None:
        for widget in (self.source_button, self.target_combo, self.output_button,
                       self.build_button, self.workdir_check, self.language_combo):
            widget.setEnabled(not busy)

    def start_build(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        if not self.source_dir or not self.source_dir.is_dir():
            QMessageBox.warning(self, tr(self.language, "need_source_title"), tr(self.language, "need_source"))
            return
        target = self.target_combo.currentData()
        if not target:
            QMessageBox.warning(self, tr(self.language, "need_target_title"), tr(self.language, "need_target"))
            return
        output_text = self.output_edit.text().strip().strip('"')
        if not output_text:
            QMessageBox.warning(self, tr(self.language, "need_output_title"), tr(self.language, "need_output"))
            return
        output = Path(output_text).expanduser().resolve()
        if output.suffix.lower() != ".pbox":
            output = output.with_suffix(".pbox")
            self.output_edit.setText(str(output))
        try:
            output.relative_to(self.source_dir)
            output_inside_source = True
        except ValueError:
            output_inside_source = False
        if output_inside_source:
            QMessageBox.warning(self, tr(self.language, "output_inside_title"), tr(self.language, "output_inside"))
            return
        if output.exists():
            answer = QMessageBox.question(
                self, tr(self.language, "overwrite_title"),
                tr(self.language, "overwrite", path=output),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        self.log("=" * 58)
        self.log(tr(self.language, "build_start", path=output))
        self.progress_bar.setValue(0)
        self._set_busy(True)
        self.worker = BuildWorker(
            self.source_dir, str(target), output, self.workdir_check.isChecked(), self.language, self
        )
        self.worker.log.connect(self.log)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.succeeded.connect(self.build_succeeded)
        self.worker.failed.connect(self.build_failed)
        self.worker.start()

    def build_succeeded(self, output: str) -> None:
        self._set_busy(False)
        self.log(tr(self.language, "build_done", path=output))
        QMessageBox.information(
            self, tr(self.language, "success_title"), tr(self.language, "success", path=output)
        )

    def build_failed(self, error: str) -> None:
        self._set_busy(False)
        self.log(tr(self.language, "failure_log", error=error))
        QMessageBox.critical(self, tr(self.language, "failure_title"), error)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setWindowIcon(QIcon(str(resource_path("assets/pocketbox.ico"))))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
