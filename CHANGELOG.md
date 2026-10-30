# Changelog

All notable changes to PocketBox are documented here.

## [0.3.1] - 2026-10-30

### Added
- English-first Builder UI with an English/Korean language selector.
- Per-user language preference saved in `%APPDATA%\\PocketBox\\settings.json`.
- Launcher error dialogs use the same saved language preference.
- Shared diagnostic translation for known container-format errors.
- MIT license and GitHub project files: contribution guide, security policy, code of conduct, support notes, issue templates, pull request template, citation metadata, and CI tests.
- A single bilingual README with English first and Korean below it.
- Documentation for the `.pbox` version 1 binary format.
- Unit tests for language preference storage, malformed-settings fallback, and error translation.

### Changed
- Version metadata updated to 0.3.1.
- README now documents package behavior, temporary workspace cleanup, limitations, build steps, and security boundaries.

## [0.2.4]

- Fix PyInstaller icon lookup when generated `.spec` files are stored under `build\\spec` by passing absolute resource paths.
- Pass the Builder icon data path as an absolute path as well.
- Build EXEs into temporary staging folders under `build\\staging`, then copy only successfully completed EXEs into the project root.
- Apply the same path and staging fixes to the standalone launcher and Builder build scripts.

## [0.2.3]

- Make `build_all.bat` the only required first-run setup/build/install action.
- Automatically create and reuse a project-local `.venv` with Python 3.12 64-bit.
- Install required packages, run container format tests, and build both EXEs in one sequence.
- Automatically install the launcher, Builder, and `.pbox` file association for the current Windows user.
- Keep final EXEs in the project root and PyInstaller intermediates under `build/`.
- Add non-interactive installer mode for the one-click workflow and improve failure messages.

## [0.2.2]

- Build `PocketBox.exe` and `PocketBoxBuilder.exe` directly into the project root instead of a `dist` folder.
- Keep PyInstaller intermediate files and spec files under `build/`.
- Update Builder launching and installer source paths to use the project root executables.

## [0.2.1]

- Added a custom multi-resolution PocketBox application icon and a dedicated `.pbox` document icon.
- Embedded icons in the launcher and Builder executables and registered the `.pbox` file association.

## [0.2]

- Split the `.pbox` container format from its shared Windows launcher.
- Preserve source folders and create a separate `.pbox` output file.
- Extract to a temporary workspace and clean it after the tracked process tree exits.
- Add path validation, streaming zlib compression, and SHA-256 verification.

