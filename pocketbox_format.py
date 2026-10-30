"""PocketBox .pbox container format and safe extraction helpers.

A .pbox file stores a manifest followed by individually zlib-compressed files.
The shared PocketBox launcher reads this format at runtime.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import struct
import zlib
from pathlib import Path, PurePosixPath
from typing import Callable, Iterable

MAGIC = b"PBOXPK01"
HEADER = struct.Struct("<8sQ")
CHUNK_SIZE = 1024 * 1024
MAX_MANIFEST_SIZE = 64 * 1024 * 1024
MAX_ENTRIES = 250_000
MAX_RELATIVE_PATH = 160

_INVALID_WIN_CHARS = set('<>:"|?*')
_RESERVED_WIN_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

ProgressCallback = Callable[[int, int, str], None]


def validate_relative_path(value: str) -> str:
    """Validate a portable relative path that is safe on Windows."""
    if not isinstance(value, str) or not value:
        raise ValueError("비어 있는 파일 경로가 포함되어 있습니다.")
    if len(value) > MAX_RELATIVE_PATH:
        raise ValueError(f"경로가 너무 깁니다(최대 {MAX_RELATIVE_PATH}자): {value[:80]}")
    if value.startswith(("/", "\\")) or "\\" in value:
        raise ValueError(f"절대 경로 또는 잘못된 구분자가 포함되어 있습니다: {value}")
    if re.match(r"^[A-Za-z]:", value):
        raise ValueError(f"드라이브 경로는 허용되지 않습니다: {value}")

    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"상위 폴더 이동 또는 빈 경로 요소가 포함되어 있습니다: {value}")

    for part in parts:
        if part.endswith((".", " ")):
            raise ValueError(f"Windows에서 모호한 파일 이름입니다: {part}")
        if any(ord(ch) < 32 or ch in _INVALID_WIN_CHARS for ch in part):
            raise ValueError(f"Windows에서 사용할 수 없는 문자가 포함되어 있습니다: {part}")
        base_name = part.split(".", 1)[0].upper()
        if base_name in _RESERVED_WIN_NAMES:
            raise ValueError(f"Windows 예약 장치 이름은 사용할 수 없습니다: {part}")
        if len(part) > 255:
            raise ValueError(f"파일 이름이 너무 깁니다: {part[:80]}")
    return value


def _is_reparse_or_link(path: Path) -> bool:
    st = path.lstat()
    if stat.S_ISLNK(st.st_mode):
        return True
    attrs = getattr(st, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400)
    return bool(attrs & reparse_flag)


def scan_source_tree(source: Path) -> list[dict]:
    """Return a deterministic list of directories and regular files.

    Symlinks and Windows reparse points are rejected rather than followed.
    """
    source = Path(source).absolute()
    if not source.is_dir() or _is_reparse_or_link(source):
        raise ValueError("원본 경로는 일반 폴더여야 하며 심볼릭 링크/정션이면 안 됩니다.")
    source = source.resolve(strict=True)

    result: list[dict] = []
    stack: list[tuple[Path, str]] = [(source, "")]
    while stack:
        directory, rel_parent = stack.pop()
        try:
            with os.scandir(directory) as iterator:
                children = sorted(iterator, key=lambda e: e.name.casefold(), reverse=True)
        except OSError as exc:
            raise OSError(f"폴더를 읽을 수 없습니다: {directory}\n{exc}") from exc

        for child in children:
            child_path = Path(child.path)
            rel = f"{rel_parent}/{child.name}" if rel_parent else child.name
            rel = validate_relative_path(rel)
            try:
                child_stat = child.stat(follow_symlinks=False)
            except OSError as exc:
                raise OSError(f"파일 정보를 읽을 수 없습니다: {child_path}\n{exc}") from exc

            if stat.S_ISLNK(child_stat.st_mode) or (
                getattr(child_stat, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x0400)
            ):
                raise ValueError(f"심볼릭 링크 또는 정션은 패키징할 수 없습니다: {rel}")

            if stat.S_ISDIR(child_stat.st_mode):
                result.append({"path": rel, "kind": "dir", "source": child_path})
                stack.append((child_path, rel))
            elif stat.S_ISREG(child_stat.st_mode):
                result.append({"path": rel, "kind": "file", "source": child_path})
            else:
                raise ValueError(f"일반 파일/폴더가 아닌 항목은 패키징할 수 없습니다: {rel}")

    result.sort(key=lambda item: (item["path"].casefold(), item["path"]))
    if len(result) > MAX_ENTRIES:
        raise ValueError(f"항목이 너무 많습니다. 최대 {MAX_ENTRIES:,}개까지 지원합니다.")
    return result


def build_payload(
    source: Path,
    target_relative: str,
    output_path: Path,
    working_directory: str = "target_dir",
    progress: ProgressCallback | None = None,
) -> tuple[int, int]:
    """Create a PBOX payload using streaming compression and hashing.

    Returns (file_count, total_uncompressed_bytes).
    """
    source = source.resolve(strict=True)
    target_relative = validate_relative_path(target_relative.replace("\\", "/"))
    if working_directory not in ("target_dir", "bundle_root"):
        raise ValueError("잘못된 작업 디렉터리 설정입니다.")

    entries = scan_source_tree(source)
    file_entries = [item for item in entries if item["kind"] == "file"]
    target_matches = [item for item in file_entries if item["path"].casefold() == target_relative.casefold()]
    if not target_matches:
        raise ValueError(f"시작 프로그램을 원본 폴더에서 찾을 수 없습니다: {target_relative}")
    actual_target = target_matches[0]["path"]
    if not actual_target.lower().endswith(".exe"):
        raise ValueError("시작 프로그램은 .exe 파일이어야 합니다.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    data_path = output_path.with_suffix(output_path.suffix + ".data.tmp")
    data_path.unlink(missing_ok=True)

    file_count = len(file_entries)
    total_uncompressed = 0
    manifest_entries: list[dict] = []
    completed = 0

    try:
        with data_path.open("wb") as data_out:
            for item in entries:
                rel = item["path"]
                if item["kind"] == "dir":
                    manifest_entries.append({"path": rel, "kind": "dir"})
                    continue

                file_path: Path = item["source"]
                before = file_path.stat()
                offset = data_out.tell()
                digest = hashlib.sha256()
                uncompressed_size = 0
                compressor = zlib.compressobj(level=6)

                with file_path.open("rb") as src:
                    while True:
                        block = src.read(CHUNK_SIZE)
                        if not block:
                            break
                        uncompressed_size += len(block)
                        digest.update(block)
                        compressed = compressor.compress(block)
                        if compressed:
                            data_out.write(compressed)
                    tail = compressor.flush()
                    if tail:
                        data_out.write(tail)

                after = file_path.stat()
                if (
                    uncompressed_size != before.st_size
                    or before.st_size != after.st_size
                    or before.st_mtime_ns != after.st_mtime_ns
                ):
                    raise RuntimeError(f"패키징 중 원본 파일이 변경되었습니다: {rel}")

                compressed_size = data_out.tell() - offset
                manifest_entries.append({
                    "path": rel,
                    "kind": "file",
                    "size": uncompressed_size,
                    "offset": offset,
                    "compressed_size": compressed_size,
                    "sha256": digest.hexdigest(),
                })
                total_uncompressed += uncompressed_size
                completed += 1
                if progress:
                    progress(completed, max(file_count, 1), rel)

        manifest = {
            "format_version": 1,
            "target": actual_target,
            "working_directory": working_directory,
            "entries": manifest_entries,
        }
        manifest_bytes = json.dumps(
            manifest, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        if len(manifest_bytes) > MAX_MANIFEST_SIZE:
            raise ValueError("파일 목록 정보가 너무 큽니다.")

        temp_output = output_path.with_suffix(output_path.suffix + ".tmp")
        try:
            with temp_output.open("wb") as final_out:
                final_out.write(HEADER.pack(MAGIC, len(manifest_bytes)))
                final_out.write(manifest_bytes)
                with data_path.open("rb") as data_in:
                    while True:
                        block = data_in.read(CHUNK_SIZE)
                        if not block:
                            break
                        final_out.write(block)
                final_out.flush()
                os.fsync(final_out.fileno())
            os.replace(temp_output, output_path)
        finally:
            temp_output.unlink(missing_ok=True)
    finally:
        data_path.unlink(missing_ok=True)

    return file_count, total_uncompressed


def _validate_manifest(manifest: object, data_size: int) -> tuple[dict, list[dict]]:
    if not isinstance(manifest, dict) or manifest.get("format_version") != 1:
        raise ValueError("지원하지 않는 PocketBox 파일 형식입니다.")

    entries = manifest.get("entries")
    if not isinstance(entries, list) or len(entries) > MAX_ENTRIES:
        raise ValueError("파일 목록이 잘못되었거나 너무 큽니다.")

    normalized: list[dict] = []
    paths: dict[str, dict] = {}
    component_spellings: dict[tuple[str, ...], str] = {}
    file_segments: list[tuple[int, int, dict]] = []

    for raw in entries:
        if not isinstance(raw, dict):
            raise ValueError("잘못된 파일 항목이 있습니다.")
        rel = validate_relative_path(raw.get("path"))
        folded = rel.casefold()
        if folded in paths:
            raise ValueError(f"대소문자만 다른 중복 경로가 있습니다: {rel}")

        parts = rel.split("/")
        for idx, part in enumerate(parts):
            parent_key = tuple(p.casefold() for p in parts[:idx])
            component_key = (parent_key, part.casefold())
            previous = component_spellings.get(component_key)
            if previous is not None and previous != part:
                raise ValueError(f"Windows에서 충돌하는 경로 대소문자가 있습니다: {rel}")
            component_spellings[component_key] = part

        kind = raw.get("kind")
        if kind == "dir":
            item = {"path": rel, "kind": "dir"}
        elif kind == "file":
            size = raw.get("size")
            offset = raw.get("offset")
            compressed_size = raw.get("compressed_size")
            sha256 = raw.get("sha256")
            if any(isinstance(v, bool) or not isinstance(v, int) or v < 0
                   for v in (size, offset, compressed_size)):
                raise ValueError(f"파일 크기 정보가 잘못되었습니다: {rel}")
            if not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", sha256):
                raise ValueError(f"파일 해시 정보가 잘못되었습니다: {rel}")
            if offset + compressed_size > data_size:
                raise ValueError(f"파일 데이터 범위가 잘못되었습니다: {rel}")
            item = {
                "path": rel, "kind": "file", "size": size,
                "offset": offset, "compressed_size": compressed_size,
                "sha256": sha256,
            }
            file_segments.append((offset, offset + compressed_size, item))
        else:
            raise ValueError(f"알 수 없는 파일 항목 종류입니다: {rel}")

        paths[folded] = item
        normalized.append(item)

    # A file cannot also be the parent of another entry.
    for item in normalized:
        parts = item["path"].split("/")
        for idx in range(1, len(parts)):
            parent = "/".join(parts[:idx]).casefold()
            parent_item = paths.get(parent)
            if parent_item and parent_item["kind"] != "dir":
                raise ValueError(f"파일을 폴더처럼 사용하는 잘못된 경로입니다: {item['path']}")

    file_segments.sort(key=lambda segment: segment[0])
    cursor = 0
    for start, end, item in file_segments:
        if start != cursor or end < start:
            raise ValueError(f"파일 데이터가 겹치거나 누락되었습니다: {item['path']}")
        cursor = end
    if cursor != data_size:
        raise ValueError("사용되지 않는 데이터 또는 잘못된 파일 길이가 있습니다.")

    target = manifest.get("target")
    target = validate_relative_path(target)
    if not target.lower().endswith(".exe"):
        raise ValueError("시작 프로그램 경로가 .exe가 아닙니다.")
    target_item = paths.get(target.casefold())
    if not target_item or target_item["kind"] != "file":
        raise ValueError("시작 프로그램이 패키지에 포함되어 있지 않습니다.")

    working_directory = manifest.get("working_directory", "target_dir")
    if working_directory not in ("target_dir", "bundle_root"):
        raise ValueError("작업 디렉터리 설정이 잘못되었습니다.")

    return manifest, normalized


def extract_payload(payload_path: Path, destination: Path) -> tuple[Path, Path]:
    """Validate and extract the payload. Returns (bundle_root, target_exe)."""
    payload_path = Path(payload_path)
    destination = Path(destination)
    with payload_path.open("rb") as payload:
        header = payload.read(HEADER.size)
        if len(header) != HEADER.size:
            raise ValueError("패키지 헤더가 잘렸습니다.")
        magic, manifest_size = HEADER.unpack(header)
        if magic != MAGIC:
            raise ValueError("PocketBox 패키지가 아니거나 파일이 손상되었습니다.")
        if manifest_size <= 0 or manifest_size > MAX_MANIFEST_SIZE:
            raise ValueError("패키지 파일 목록 크기가 비정상적입니다.")
        manifest_bytes = payload.read(manifest_size)
        if len(manifest_bytes) != manifest_size:
            raise ValueError("패키지 파일 목록이 잘렸습니다.")
        try:
            manifest_obj = json.loads(manifest_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("패키지 파일 목록을 해석할 수 없습니다.") from exc

        data_start = HEADER.size + manifest_size
        data_size = payload_path.stat().st_size - data_start
        if data_size < 0:
            raise ValueError("패키지 파일 길이가 올바르지 않습니다.")
        manifest, entries = _validate_manifest(manifest_obj, data_size)

        destination.mkdir(parents=True, exist_ok=False)
        # Create explicitly stored directories first; parent directories are also
        # created as needed for archives that omit redundant directory entries.
        dirs = [item for item in entries if item["kind"] == "dir"]
        dirs.sort(key=lambda item: (item["path"].count("/"), item["path"].casefold()))
        for item in dirs:
            (destination / Path(*item["path"].split("/"))).mkdir(parents=True, exist_ok=True)

        files = [item for item in entries if item["kind"] == "file"]
        for item in files:
            out_path = destination / Path(*item["path"].split("/"))
            out_path.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            written = 0
            decompressor = zlib.decompressobj()
            remaining = item["compressed_size"]
            payload.seek(data_start + item["offset"])

            with out_path.open("xb") as out_file:
                while remaining:
                    compressed_block = payload.read(min(CHUNK_SIZE, remaining))
                    if not compressed_block:
                        raise ValueError(f"압축된 파일 데이터가 잘렸습니다: {item['path']}")
                    remaining -= len(compressed_block)
                    pending = compressed_block
                    while pending:
                        max_output = max(1, item["size"] - written + 1)
                        output = decompressor.decompress(pending, max_output)
                        pending = decompressor.unconsumed_tail
                        if output:
                            written += len(output)
                            if written > item["size"]:
                                raise ValueError(f"압축 해제 크기가 선언값을 초과합니다: {item['path']}")
                            digest.update(output)
                            out_file.write(output)
                        if not pending:
                            break

                tail = decompressor.flush()
                if tail:
                    written += len(tail)
                    if written > item["size"]:
                        raise ValueError(f"압축 해제 크기가 선언값을 초과합니다: {item['path']}")
                    digest.update(tail)
                    out_file.write(tail)

            if not decompressor.eof or decompressor.unused_data:
                raise ValueError(f"압축 데이터 구조가 올바르지 않습니다: {item['path']}")
            if written != item["size"]:
                raise ValueError(f"파일 크기가 일치하지 않습니다: {item['path']}")
            if digest.hexdigest() != item["sha256"]:
                raise ValueError(f"파일 무결성 검사에 실패했습니다: {item['path']}")

    target = destination / Path(*manifest["target"].split("/"))
    return destination, target
