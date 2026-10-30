"""PocketBox launcher: opens a .pbox container, runs its program, then cleans cache."""
from __future__ import annotations

import ctypes
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from pocketbox_format import extract_payload
from pocketbox_settings import get_language, translate_error_text


def show_message(title: str, message: str, *, warning: bool = False) -> None:
    try:
        flags = 0x00000000 | (0x00000030 if warning else 0x00000010)  # MB_OK + icon
        ctypes.windll.user32.MessageBoxW(None, message, title, flags)
    except Exception:
        pass


def _windows_error(prefix: str) -> OSError:
    return ctypes.WinError(ctypes.get_last_error(), prefix)


class ProcessTrackingError(RuntimeError):
    """Raised when process-tree completion cannot be verified safely."""


MESSAGES = {
    "en": {
        "windows_only": "The PocketBox launcher is designed to run on Windows.",
        "missing_argument": "No .pbox file was specified.\n\nDouble-click a .pbox file in File Explorer, or pass a package path to PocketBox.exe.",
        "not_found": "The .pbox file could not be found.\n\n{path}",
        "invalid_package": "PocketBox requires a valid .pbox package file.",
        "tracking_failed": "Windows could not confirm that all child processes have exited. The cache will be kept to avoid deleting files that may still be in use. Reason: {cause}",
        "preserve_cache": "\n\nThe process tree could not be confirmed as stopped, so the cache was preserved. After confirming that all related programs have exited, delete this folder manually:\n\n{workspace}",
        "run_failed": "Failed to open the .pbox package.\n\n{error}",
        "cleanup_title": "PocketBox - Cache cleanup notice",
        "cleanup_failed": "The program has exited, but some cache files could not be deleted.\nCheck this folder:\n\n{workspace}",
        "error_title": "PocketBox launch error",
        "job_create": "Could not create a Windows Job Object",
        "start_failed": "Could not start the bundled program",
        "assign_failed": "Could not assign the process to the tracking job",
        "resume_failed": "Could not resume the bundled program",
        "query_failed": "Could not query process completion status",
    },
    "ko": {
        "windows_only": "PocketBox 런처는 Windows에서 실행하도록 만들어졌습니다.",
        "missing_argument": "열 .pbox 파일을 지정하지 않았습니다.\n\n탐색기에서 .pbox 파일을 더블클릭하거나 PocketBox.exe로 파일을 열어 주세요.",
        "not_found": ".pbox 파일을 찾을 수 없습니다.\n\n{path}",
        "invalid_package": "PocketBox 런처에는 유효한 .pbox 파일을 전달해야 합니다.",
        "tracking_failed": "Windows가 모든 자식 프로세스의 종료 여부를 확인하지 못했습니다. 사용 중인 파일을 삭제하지 않도록 캐시를 보존합니다. 원인: {cause}",
        "preserve_cache": "\n\n프로세스 종료 여부를 확인하지 못해 캐시를 보존했습니다. 관련 프로그램이 완전히 종료된 것을 확인한 뒤 아래 폴더를 직접 삭제하세요.\n\n{workspace}",
        "run_failed": ".pbox 실행에 실패했습니다.\n\n{error}",
        "cleanup_title": "PocketBox - 캐시 정리 알림",
        "cleanup_failed": "프로그램 실행이 끝났지만 일부 캐시 파일을 삭제하지 못했습니다.\n다음 폴더를 확인해 주세요.\n\n{workspace}",
        "error_title": "PocketBox 실행 오류",
        "job_create": "Windows 작업 개체를 만들 수 없습니다",
        "start_failed": "포함된 프로그램을 시작할 수 없습니다",
        "assign_failed": "프로세스를 관리 작업에 연결할 수 없습니다",
        "resume_failed": "프로그램 실행을 재개할 수 없습니다",
        "query_failed": "프로세스 종료 상태를 확인할 수 없습니다",
    },
}


def message(language: str, key: str, **values: object) -> str:
    return MESSAGES.get(language, MESSAGES["en"])[key].format(**values)


def _pe_uses_console_subsystem(executable: Path) -> bool:
    """Return True for standard Windows console-subsystem PE executables."""
    import struct

    try:
        with executable.open("rb") as file:
            dos = file.read(64)
            if len(dos) < 64 or dos[:2] != b"MZ":
                return False
            pe_offset = struct.unpack_from("<I", dos, 0x3C)[0]
            if pe_offset > 16 * 1024 * 1024:
                return False
            file.seek(pe_offset)
            if file.read(4) != b"PE\0\0":
                return False
            coff = file.read(20)
            if len(coff) != 20:
                return False
            optional_header_size = struct.unpack_from("<H", coff, 16)[0]
            if optional_header_size < 70 or optional_header_size > 4096:
                return False
            optional_header = file.read(optional_header_size)
            if len(optional_header) != optional_header_size:
                return False
            magic = struct.unpack_from("<H", optional_header, 0)[0]
            if magic not in (0x10B, 0x20B):
                return False
            subsystem = struct.unpack_from("<H", optional_header, 68)[0]
            return subsystem == 3  # IMAGE_SUBSYSTEM_WINDOWS_CUI
    except (OSError, ValueError, struct.error):
        return False


def run_and_wait_for_process_tree(executable: Path, working_directory: Path, language: str = "en") -> None:
    """Launch the app suspended, assign it to a Windows Job Object, then resume.

    The Job Object tracks child processes too. The cache is not removed just
    because the first EXE exits; it is removed after the whole process tree in
    the job has ended.
    """
    if sys.platform != "win32":
        # Useful for local format testing, although generated bundles target Windows.
        process = subprocess.Popen([str(executable)], cwd=str(working_directory))
        process.wait()
        return

    from ctypes import wintypes

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(ctypes.c_ubyte)),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    class BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_longlong),
            ("TotalKernelTime", ctypes.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes.c_longlong),
            ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
            ("TotalPageFaults", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel32.QueryInformationJobObject.argtypes = [
        wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    kernel32.QueryInformationJobObject.restype = wintypes.BOOL
    kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
    kernel32.ResumeThread.restype = wintypes.DWORD
    kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateProcess.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel32.WaitForSingleObject.restype = wintypes.DWORD
    kernel32.CreateProcessW.argtypes = [
        wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.LPVOID, wintypes.LPVOID,
        wintypes.BOOL, wintypes.DWORD, wintypes.LPVOID, wintypes.LPCWSTR,
        ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION),
    ]
    kernel32.CreateProcessW.restype = wintypes.BOOL

    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise _windows_error(message(language, "job_create"))

    process_info = PROCESS_INFORMATION()
    try:
        startup = STARTUPINFOW()
        startup.cb = ctypes.sizeof(STARTUPINFOW)
        command_line = ctypes.create_unicode_buffer(
            subprocess.list2cmdline([str(executable)])
        )
        CREATE_SUSPENDED = 0x00000004
        CREATE_NEW_CONSOLE = 0x00000010
        CREATE_UNICODE_ENVIRONMENT = 0x00000400
        console_flag = CREATE_NEW_CONSOLE if _pe_uses_console_subsystem(executable) else 0

        ok = kernel32.CreateProcessW(
            str(executable), command_line,
            None, None, False,
            CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT | console_flag,
            None, str(working_directory),
            ctypes.byref(startup), ctypes.byref(process_info),
        )
        if not ok:
            raise _windows_error(message(language, "start_failed"))

        # Assign before resuming so a fast-spawning application cannot create
        # an untracked child before job membership is established.
        if not kernel32.AssignProcessToJobObject(job, process_info.hProcess):
            error = _windows_error(message(language, "assign_failed"))
            kernel32.TerminateProcess(process_info.hProcess, 1)
            kernel32.WaitForSingleObject(process_info.hProcess, 0xFFFFFFFF)
            raise error

        if kernel32.ResumeThread(process_info.hThread) == 0xFFFFFFFF:
            error = _windows_error(message(language, "resume_failed"))
            kernel32.TerminateProcess(process_info.hProcess, 1)
            kernel32.WaitForSingleObject(process_info.hProcess, 0xFFFFFFFF)
            raise error

        kernel32.CloseHandle(process_info.hThread)
        process_info.hThread = None

        # Job Object accounting includes the original process and its children.
        # The default job policy does not allow breakaway processes.
        while True:
            accounting = BASIC_ACCOUNTING_INFORMATION()
            ok = kernel32.QueryInformationJobObject(
                job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None
            )
            if not ok:
                cause = _windows_error(message(language, "query_failed"))
                raise ProcessTrackingError(
                    message(language, "tracking_failed", cause=cause)
                ) from cause
            if accounting.ActiveProcesses == 0:
                break
            time.sleep(0.25)
    finally:
        if process_info.hThread:
            kernel32.CloseHandle(process_info.hThread)
        if process_info.hProcess:
            kernel32.CloseHandle(process_info.hProcess)
        if job:
            kernel32.CloseHandle(job)


def _remove_tree_with_retries(path: Path) -> bool:
    def repair_and_retry(function, item_path, _exc_info):
        try:
            Path(item_path).chmod(stat.S_IWRITE | stat.S_IREAD)
        except OSError:
            pass
        try:
            function(item_path)
        except OSError:
            raise

    for attempt in range(12):
        try:
            shutil.rmtree(path, onerror=repair_and_retry)
            return True
        except FileNotFoundError:
            return True
        except OSError:
            time.sleep(0.5 + min(attempt * 0.15, 1.0))
    return not path.exists()


def main() -> int:
    language = get_language()
    if sys.platform != "win32":
        show_message("PocketBox", message(language, "windows_only"))
        return 2

    if len(sys.argv) < 2:
        show_message("PocketBox", message(language, "missing_argument"))
        return 2

    package_path = Path(sys.argv[1]).expanduser()
    try:
        package_path = package_path.resolve(strict=True)
    except OSError:
        show_message("PocketBox", message(language, "not_found", path=package_path))
        return 2

    if not package_path.is_file() or package_path.suffix.lower() != ".pbox":
        show_message("PocketBox", message(language, "invalid_package"))
        return 2

    workspace: Path | None = None
    error_message: str | None = None
    cleanup_failed = False
    preserve_workspace = False

    try:
        # Extract into a fresh temporary workspace. The source folder and
        # the .pbox container itself are never modified.
        workspace = Path(tempfile.mkdtemp(prefix="PocketBox-"))
        bundle_root = workspace / "bundle"
        bundle_root, target_exe = extract_payload(package_path, bundle_root)

        import json
        from pocketbox_format import HEADER

        with package_path.open("rb") as package:
            header = package.read(HEADER.size)
            _magic, manifest_size = HEADER.unpack(header)
            manifest = json.loads(package.read(manifest_size).decode("utf-8"))
        working_directory = (
            target_exe.parent
            if manifest.get("working_directory") == "target_dir"
            else bundle_root
        )

        run_and_wait_for_process_tree(target_exe, working_directory, language)
    except ProcessTrackingError as exc:
        preserve_workspace = True
        error_message = (
            f"{exc}{message(language, 'preserve_cache', workspace=workspace)}"
        )
    except Exception as exc:
        error_message = message(
            language, "run_failed", error=translate_error_text(exc, language)
        )
    finally:
        if workspace is not None and not preserve_workspace:
            cleanup_failed = not _remove_tree_with_retries(workspace)

    if cleanup_failed and workspace is not None:
        show_message(
            message(language, "cleanup_title"),
            message(language, "cleanup_failed", workspace=workspace),
            warning=True,
        )

    if error_message:
        show_message(message(language, "error_title"), error_message)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
