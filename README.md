# PocketBox

![PocketBox application icon](assets/pocketbox.png)

**Bundle a folder into one `.pbox` package and launch its selected Windows program with a double-click.**

PocketBox is a small Windows packaging utility. The Builder reads a source folder and creates a separate `.pbox` container. The original files are not moved, deleted, or modified. A shared PocketBox launcher opens the package, extracts it to a temporary workspace, starts the selected executable, and removes the workspace after the tracked process tree exits.

> **Important:** PocketBox is a packaging and launching tool, not a security sandbox. Programs launched from a `.pbox` package run with your normal Windows user permissions. Only open packages from sources you trust.

## Features

- Create one `.pbox` file from a folder containing an EXE, DLLs, assets, and subfolders.
- Choose which EXE is started when the package is opened.
- Preserve the original source folder; package creation writes to a separate output file.
- Use a shared launcher so each package does not need its own EXE wrapper.
- Extract to a unique temporary workspace and clean it after the tracked Windows Job Object process tree exits.
- Validate package paths and metadata, stream zlib-compressed files, and verify SHA-256 hashes during extraction.
- Switch the Builder and launcher messages between English and Korean. English is the default; the selected language is saved per Windows user.

## Requirements

- Windows 10 or Windows 11, 64-bit.
- Python 3.12, 64-bit, and the Python Launcher (`py`) for building from source.
- Internet access on the first build to install PySide6 and PyInstaller.

The generated `PocketBox.exe` and `PocketBoxBuilder.exe` do not require a separate Python installation to run. The one-click build script does not install Python itself.

## Build and install

1. Install Python 3.12 (64-bit). During setup, enable the Python Launcher and add Python to `PATH`.
2. Extract this repository to a folder.
3. Double-click **`build_all.bat`**.

The script creates or reuses `.venv`, installs dependencies, runs the format tests, builds both executables, copies them to the repository root, installs the launcher for the current Windows user, and registers `.pbox` file association. Administrator rights are not required for the per-user installation.

When it finishes, the repository root contains:

```text
PocketBox/
├── PocketBox.exe          # Shared .pbox launcher
├── PocketBoxBuilder.exe   # GUI package builder
├── build_all.bat          # One-click setup, build, and install
├── pocketbox_builder.py
├── pocketbox_runtime.py
├── pocketbox_format.py
├── pocketbox_settings.py
├── assets/
│   ├── pocketbox.ico
│   └── pbox_file.ico
├── .venv/                 # Local build environment
└── build/                 # PyInstaller intermediate files
```

The final EXE files are placed in the repository root, not in a `dist` folder. Generated executables, local environments, build output, and `.pbox` packages are excluded by `.gitignore`.

## Create a package

1. Start `PocketBoxBuilder.exe`.
2. Select the source folder that contains the program and all of its required files.
3. Choose the startup `.exe` from the detected executable list.
4. Choose an output path outside the source folder.
5. Click **Create .pbox**.
6. Double-click the resulting `.pbox` file in File Explorer.

The Builder only reads the source folder and writes a new `.pbox` file elsewhere. It does not delete or relocate the original files. The generated package stores a copy of the selected source files, so changes made to the original folder after packaging are not automatically reflected in an existing `.pbox` file.

## Language

The Builder starts in English. Use the language selector in the upper-right corner to switch to Korean. The preference is saved to `%APPDATA%\PocketBox\settings.json` and is shared with the launcher's message dialogs. If the settings file is missing or invalid, PocketBox falls back to English.

## Temporary workspace and saved data

When a `.pbox` package is opened, PocketBox extracts its contents to a unique folder under the current user's Windows temporary directory. The source folder and the `.pbox` file are not modified. The launcher tracks the started process and its normal child processes with a Windows Job Object. It removes the temporary workspace after the tracked process tree exits.

Files saved by the launched program inside this temporary workspace are removed during cleanup. For persistent save data or settings, the launched program must write to a durable location such as `%APPDATA%`, `%LOCALAPPDATA%`, or the user's Documents folder. If process completion cannot be verified or Windows keeps a file locked, PocketBox preserves the workspace rather than intentionally deleting files that may still be in use; the path is shown in an error or cleanup notice.

## Uninstall

Run `uninstall_pocketbox.bat` to remove the current user's `.pbox` association, installed launcher and Builder, file icon, Start Menu shortcut, and saved language preference. This does not delete the repository folder, original source folders, or `.pbox` packages.

## Security notes and limitations

- A `.pbox` package is **not** an application sandbox, virtual machine, or permission boundary. Its program runs with the current user's permissions and may access files, the registry, devices, and network resources available to that user.
- Do not run `.pbox` files from untrusted sources. SHA-256 checks detect accidental or malicious changes to packaged file data relative to its manifest; they do not establish who created or signed a package.
- Package paths are validated to reject traversal, absolute paths, Windows reserved names, and unsupported filesystem entries. Symbolic links and Windows reparse points are not packaged.
- Extraction validates manifest entries, stream boundaries, declared sizes, and file hashes. These checks reduce malformed-package risks but are not a substitute for operating-system isolation.
- Programs that deliberately break away from the tracked Job Object, elevate privileges, install services or drivers, or keep files locked may not follow the normal cleanup lifecycle.
- Temporary workspace cleanup is best-effort. If a file remains locked, the launcher reports the remaining path rather than claiming that cleanup succeeded.
- The current package format uses streaming zlib compression; it is not designed to outperform specialist archivers.

## Development and tests

Run the format and settings tests with Python 3.12 or newer:

```powershell
py -3.12 -m unittest discover -v
```

To prepare a local environment manually:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -v
```

Windows-specific executable building, Explorer file association, icon refresh, and process-tree cleanup should be validated on a real Windows 10/11 machine. The automated tests cover the container format, language preference storage, and diagnostic translation; they do not replace those integration tests.

## Project files

| File | Purpose |
|---|---|
| `pocketbox_builder.py` | PySide6 GUI for creating `.pbox` packages |
| `pocketbox_runtime.py` | Shared launcher entry point |
| `pocketbox_format.py` | Container format, compression, validation, extraction, and hashing |
| `pocketbox_settings.py` | Per-user language preference storage and diagnostic translation |
| `test_format.py` | Container format tests |
| `test_settings.py` | Preference storage tests |
| `build_all.bat` | One-click setup, test, build, and per-user installation |
| `install_pocketbox.bat` | Register launcher and `.pbox` association |
| `uninstall_pocketbox.bat` | Remove the per-user registration and installed files |
| `docs/PBOX_FORMAT.md` | Version 1 container format notes |
| `LICENSE` | MIT License |

## License

PocketBox is distributed under the [MIT License](LICENSE).

---

# PocketBox (한국어)

**여러 파일과 폴더를 하나의 `.pbox` 패키지로 묶고, 더블클릭으로 지정한 Windows 프로그램을 실행하는 도구입니다.**

PocketBox는 Windows용 파일 패키징 도구입니다. Builder가 원본 폴더를 읽어 별도의 `.pbox` 컨테이너를 생성합니다. 원본 파일은 이동·삭제·수정하지 않습니다. 공용 PocketBox 런처가 패키지를 열어 임시 작업 폴더에 압축을 풀고 지정된 프로그램을 실행하며, 추적 중인 프로세스 트리가 종료되면 작업 폴더를 정리합니다.

> **중요:** PocketBox는 파일 패키징 및 실행 도구이지 보안 샌드박스가 아닙니다. `.pbox`에서 실행한 프로그램은 현재 Windows 사용자와 동일한 권한으로 동작합니다. 신뢰할 수 있는 출처의 패키지만 실행하세요.

## 주요 기능

- EXE, DLL, 리소스 및 하위 폴더가 들어 있는 폴더를 하나의 `.pbox` 파일로 패키징합니다.
- 패키지를 열 때 실행할 시작 EXE를 지정할 수 있습니다.
- 원본 폴더를 보존하고 별도 위치에 `.pbox` 파일을 생성합니다.
- 패키지마다 별도 실행 파일을 만들지 않고 공용 런처를 사용합니다.
- 고유한 임시 작업 폴더에 압축을 풀고 Windows Job Object로 추적한 프로세스 트리가 끝나면 정리합니다.
- 경로 및 메타데이터 검증, 스트리밍 zlib 압축, 압축 해제 시 SHA-256 해시 검사를 지원합니다.
- Builder와 런처 안내 문구를 영어/한국어로 전환할 수 있습니다. 기본 언어는 영어이며 선택한 언어는 사용자별로 저장됩니다.

## 요구 사항

- Windows 10 또는 Windows 11, 64비트.
- 소스에서 빌드하려면 Python 3.12 64비트와 Python Launcher(`py`)가 필요합니다.
- 최초 빌드 시 PySide6 및 PyInstaller 설치를 위한 인터넷 연결이 필요합니다.

빌드된 `PocketBox.exe`와 `PocketBoxBuilder.exe`를 실행하는 데 별도의 Python 설치는 필요하지 않습니다. 원클릭 빌드 스크립트가 Python 자체를 설치해 주지는 않습니다.

## 빌드 및 설치

1. Python 3.12(64비트)를 설치합니다. 설치 중 Python Launcher를 활성화하고 Python을 `PATH`에 추가하세요.
2. 이 저장소를 원하는 폴더에 압축 해제하거나 Git으로 복제합니다.
3. **`build_all.bat`을 더블클릭**합니다.

스크립트가 `.venv` 생성 또는 재사용, 의존성 설치, 포맷 테스트, 실행 파일 두 개 빌드, 저장소 최상위 폴더로 EXE 복사, 현재 Windows 사용자용 런처 설치 및 `.pbox` 파일 연결을 순서대로 수행합니다. 현재 사용자 계정에만 설치하므로 관리자 권한은 필요하지 않습니다.

완료 후 저장소 최상위 폴더에 다음 파일이 생성됩니다.

```text
PocketBox/
├── PocketBox.exe          # 공용 .pbox 실행 런처
├── PocketBoxBuilder.exe   # GUI 패키지 제작기
├── build_all.bat          # 준비·빌드·설치 통합 스크립트
├── pocketbox_builder.py
├── pocketbox_runtime.py
├── pocketbox_format.py
├── pocketbox_settings.py
├── assets/
│   ├── pocketbox.ico
│   └── pbox_file.ico
├── .venv/                 # 로컬 빌드 환경
└── build/                 # PyInstaller 중간 산출물
```

최종 EXE는 `dist` 폴더가 아니라 저장소 최상위 폴더에 생성됩니다. `.gitignore`는 실행 파일, 로컬 가상환경, 빌드 산출물 및 `.pbox` 패키지를 Git에 올리지 않도록 설정되어 있습니다.

## 패키지 만들기

1. `PocketBoxBuilder.exe`를 실행합니다.
2. 프로그램과 필요한 파일이 들어 있는 원본 폴더를 선택합니다.
3. 검색된 실행 파일 목록에서 시작할 `.exe`를 선택합니다.
4. 원본 폴더 바깥에 결과 파일을 저장할 위치를 지정합니다.
5. **Create .pbox** 또는 **.pbox 만들기**를 누릅니다.
6. 파일 탐색기에서 생성된 `.pbox`를 더블클릭합니다.

Builder는 원본 폴더를 읽기만 하고 다른 위치에 새 `.pbox` 파일을 생성합니다. 원본 파일을 삭제하거나 이동하지 않습니다. 패키지는 선택한 시점의 파일 복사본을 포함하므로, 패키지 생성 이후 원본 폴더의 변경 사항이 기존 `.pbox`에 자동 반영되지는 않습니다.

## 언어 설정

Builder는 영어로 시작합니다. 오른쪽 위 언어 선택 메뉴에서 한국어로 변경할 수 있습니다. 선택값은 `%APPDATA%\PocketBox\settings.json`에 저장되며 런처의 메시지 창도 같은 설정을 사용합니다. 설정 파일이 없거나 올바르지 않으면 영어로 실행됩니다.

## 임시 작업 폴더와 저장 데이터

`.pbox`를 열면 현재 사용자의 Windows 임시 폴더 아래에 고유한 작업 폴더가 생성되고 패키지 내용이 추출됩니다. 원본 폴더와 `.pbox` 파일은 수정하지 않습니다. 런처는 Windows Job Object로 시작 프로그램과 일반적인 자식 프로세스를 추적합니다. 추적 중인 프로세스 트리가 종료된 뒤 임시 작업 폴더를 삭제합니다.

실행된 프로그램이 이 임시 작업 폴더 안에 저장한 세이브나 설정 파일은 정리 과정에서 함께 삭제됩니다. 영구 보존해야 하는 데이터는 `%APPDATA%`, `%LOCALAPPDATA%`, 문서 폴더 등 지속 가능한 경로에 저장해야 합니다. 프로세스 종료를 확인할 수 없거나 Windows가 파일을 잠그고 있으면, 실행 중인 파일을 무리하게 삭제하지 않고 작업 폴더를 보존한 뒤 경로를 안내합니다.

## 제거

`uninstall_pocketbox.bat`을 실행하면 현재 사용자에게 등록된 `.pbox` 연결, 설치된 런처와 Builder, 파일 아이콘, 시작 메뉴 바로가기 및 저장된 언어 설정을 제거합니다. 저장소 폴더, 원본 폴더 및 기존 `.pbox` 패키지는 삭제하지 않습니다.

## 보안 안내 및 제한 사항

- `.pbox`는 **보안 샌드박스, 가상 머신 또는 권한 경계가 아닙니다.** 포함된 프로그램은 현재 사용자 권한으로 실행되며 해당 사용자에게 허용된 파일, 레지스트리, 장치 및 네트워크 리소스에 접근할 수 있습니다.
- 신뢰할 수 없는 출처의 `.pbox`를 실행하지 마세요. SHA-256 검사는 매니페스트 기준 파일 데이터의 변조를 탐지하지만, 패키지 제작자의 신원이나 서명을 증명하지 않습니다.
- 패키지 경로는 경로 탈출, 절대 경로, Windows 예약 이름 및 지원하지 않는 파일 항목을 거부합니다. 심볼릭 링크와 Windows 재분석 지점은 패키징하지 않습니다.
- 추출 과정에서 매니페스트 항목, 데이터 범위, 선언된 크기 및 파일 해시를 검사합니다. 이러한 검사는 잘못된 패키지로 인한 위험을 줄이지만 운영체제 수준의 격리를 대체하지 않습니다.
- Job Object에서 의도적으로 이탈하는 프로그램, 관리자 권한 승격, 서비스 또는 드라이버 설치를 요구하는 프로그램, 파일을 계속 잠그는 프로그램은 일반적인 실행 및 정리 흐름을 따르지 않을 수 있습니다.
- 임시 폴더 정리는 최선형(best-effort)으로 수행됩니다. 파일 잠금 등으로 삭제할 수 없으면 런처는 정리가 끝났다고 표시하지 않고 남은 경로를 안내합니다.
- 현재 컨테이너 형식은 스트리밍 zlib 압축을 사용합니다. 전문 압축 프로그램보다 높은 압축률을 목표로 설계된 것은 아닙니다.

## 개발 및 테스트

Python 3.12 이상에서 포맷 및 설정 테스트를 실행할 수 있습니다.

```powershell
py -3.12 -m unittest discover -v
```

수동으로 개발 환경을 준비하려면 다음 명령을 사용하세요.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m unittest discover -v
```

Windows EXE 빌드, 탐색기 파일 연결, 아이콘 갱신 및 프로세스 트리 정리는 실제 Windows 10/11 PC에서 확인해야 합니다. 자동 테스트는 컨테이너 포맷, 언어 설정 저장 및 오류 문구 변환을 검사하며, Windows 통합 테스트를 대체하지 않습니다.

## 프로젝트 파일

| 파일 | 설명 |
|---|---|
| `pocketbox_builder.py` | `.pbox` 생성을 위한 PySide6 GUI |
| `pocketbox_runtime.py` | 공용 실행 런처 진입점 |
| `pocketbox_format.py` | 컨테이너 형식, 압축, 경로 검사, 추출 및 해시 검사 |
| `pocketbox_settings.py` | 사용자별 언어 설정 저장 및 오류 문구 번역 |
| `test_format.py` | 컨테이너 포맷 테스트 |
| `test_settings.py` | 언어 설정 저장 테스트 |
| `build_all.bat` | 준비, 테스트, 빌드 및 사용자별 설치를 한 번에 수행 |
| `install_pocketbox.bat` | 런처 설치 및 `.pbox` 파일 연결 |
| `uninstall_pocketbox.bat` | 사용자별 등록과 설치 파일 제거 |
| `docs/PBOX_FORMAT.md` | 컨테이너 포맷 버전 1 설명 |
| `LICENSE` | MIT 라이선스 |

## 라이선스

PocketBox는 [MIT License](LICENSE)에 따라 배포됩니다.
