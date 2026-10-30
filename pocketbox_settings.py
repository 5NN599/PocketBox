"""Shared user preferences for PocketBox applications."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SUPPORTED_LANGUAGES = {"en", "ko"}


def settings_file() -> Path:
    """Return the per-user settings path without requiring administrator rights."""
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else (Path.home() / ".config")
    return base / "PocketBox" / "settings.json"


def load_settings() -> dict[str, Any]:
    try:
        with settings_file().open("r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def get_language() -> str:
    language = load_settings().get("language", "en")
    if isinstance(language, str) and language in SUPPORTED_LANGUAGES:
        return language
    return "en"


def set_language(language: str) -> None:
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    path = settings_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    settings["language"] = language
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(settings, file, ensure_ascii=False, indent=2)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary, path)


_FORMAT_ERROR_TRANSLATIONS = {
    "비어 있는 파일 경로가 포함되어 있습니다.": "An empty file path was found.",
    "경로가 너무 깁니다(최대 ": "Path is too long (maximum ",
    "절대 경로 또는 잘못된 구분자가 포함되어 있습니다: ": "An absolute path or invalid separator was found: ",
    "드라이브 경로는 허용되지 않습니다: ": "Drive paths are not allowed: ",
    "상위 폴더 이동 또는 빈 경로 요소가 포함되어 있습니다: ": "Parent-directory traversal or an empty path component is not allowed: ",
    "Windows에서 모호한 파일 이름입니다: ": "Ambiguous Windows file name: ",
    "Windows에서 사용할 수 없는 문자가 포함되어 있습니다: ": "The name contains a character that is not allowed on Windows: ",
    "Windows 예약 장치 이름은 사용할 수 없습니다: ": "A reserved Windows device name cannot be used: ",
    "파일 이름이 너무 깁니다: ": "File name is too long: ",
    "원본 경로는 일반 폴더여야 하며 심볼릭 링크/정션이면 안 됩니다.": "The source must be a regular folder, not a symbolic link or junction.",
    "폴더를 읽을 수 없습니다: ": "Could not read folder: ",
    "파일 정보를 읽을 수 없습니다: ": "Could not read file metadata: ",
    "심볼릭 링크 또는 정션은 패키징할 수 없습니다: ": "Symbolic links and junctions cannot be packaged: ",
    "일반 파일/폴더가 아닌 항목은 패키징할 수 없습니다: ": "Only regular files and folders can be packaged: ",
    "항목이 너무 많습니다. 최대 ": "Too many entries. Maximum: ",
    "잘못된 작업 디렉터리 설정입니다.": "Invalid working-directory setting.",
    "시작 프로그램을 원본 폴더에서 찾을 수 없습니다: ": "The startup program was not found in the source folder: ",
    "시작 프로그램은 .exe 파일이어야 합니다.": "The startup program must be an .exe file.",
    "패키징 중 원본 파일이 변경되었습니다: ": "A source file changed while the package was being created: ",
    "파일 목록 정보가 너무 큽니다.": "The package manifest is too large.",
    "지원하지 않는 PocketBox 파일 형식입니다.": "Unsupported PocketBox package format.",
    "파일 목록이 잘못되었거나 너무 큽니다.": "The package entry list is invalid or too large.",
    "잘못된 파일 항목이 있습니다.": "An invalid file entry was found.",
    "대소문자만 다른 중복 경로가 있습니다: ": "Duplicate paths differ only by letter case: ",
    "Windows에서 충돌하는 경로 대소문자가 있습니다: ": "Paths conflict on Windows because of letter casing: ",
    "파일 크기 정보가 잘못되었습니다: ": "Invalid file size metadata: ",
    "파일 해시 정보가 잘못되었습니다: ": "Invalid file hash metadata: ",
    "파일 데이터 범위가 잘못되었습니다: ": "Invalid file data range: ",
    "알 수 없는 파일 항목 종류입니다: ": "Unknown file entry type: ",
    "파일을 폴더처럼 사용하는 잘못된 경로입니다: ": "A file is used as a folder in this path: ",
    "파일 데이터가 겹치거나 누락되었습니다: ": "File data overlaps or is missing: ",
    "사용되지 않는 데이터 또는 잘못된 파일 길이가 있습니다.": "Unused data or an invalid file length was found.",
    "시작 프로그램 경로가 .exe가 아닙니다.": "The startup program path is not an .exe file.",
    "시작 프로그램이 패키지에 포함되어 있지 않습니다.": "The startup program is not included in the package.",
    "작업 디렉터리 설정이 잘못되었습니다.": "Invalid working-directory metadata.",
    "패키지 헤더가 잘렸습니다.": "The package header is truncated.",
    "PocketBox 패키지가 아니거나 파일이 손상되었습니다.": "This is not a PocketBox package, or the file is corrupted.",
    "패키지 파일 목록 크기가 비정상적입니다.": "The package manifest size is invalid.",
    "패키지 파일 목록이 잘렸습니다.": "The package manifest is truncated.",
    "패키지 파일 목록을 해석할 수 없습니다.": "Could not parse the package manifest.",
    "패키지 파일 길이가 올바르지 않습니다.": "The package file length is invalid.",
    "압축된 파일 데이터가 잘렸습니다: ": "Compressed file data is truncated: ",
    "압축 해제 크기가 선언값을 초과합니다: ": "Decompressed data exceeds the declared size: ",
    "압축 데이터 구조가 올바르지 않습니다: ": "Invalid compressed data structure: ",
    "파일 크기가 일치하지 않습니다: ": "File size does not match: ",
    "파일 무결성 검사에 실패했습니다: ": "File integrity check failed: ",
}


def translate_error_text(error: object, language: str) -> str:
    """Translate known PocketBox core diagnostics while retaining unknown details."""
    value = str(error)
    if language != "en":
        return value
    for korean, english in _FORMAT_ERROR_TRANSLATIONS.items():
        if value.startswith(korean):
            return english + value[len(korean):]
    return value
