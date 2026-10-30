# Contributing to PocketBox

Thanks for considering a contribution!

## Before you start

- Search existing issues and pull requests before opening a new one.
- For a significant change, open an issue first to discuss the design.
- Do not include personal data, private packages, credentials, or copyrighted files that you do not have permission to share.

## Development setup

1. Install Python 3.12 (64-bit) on Windows.
2. Create a virtual environment and install dependencies:

   ```powershell
   py -3.12 -m venv .venv
   .venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Run the tests:

   ```powershell
   .venv\Scripts\python.exe -m unittest discover -v
   ```

## Pull requests

- Keep changes focused and explain the user-visible impact.
- Add or update tests for format, extraction, settings, and path-validation changes.
- Update the English and Korean sections of `README.md` together when behavior or instructions change.
- Add an entry to `CHANGELOG.md`.
- Do not commit `.venv/`, `build/`, generated EXEs, `.pbox` packages, or local settings.
- For Windows-specific behavior, include the Windows version and relevant test results. Do not claim an integration test passed unless it was run on Windows.

## Code style

Use clear names, type hints where practical, and comments for non-obvious Windows API behavior. Avoid introducing dependencies unless they provide a clear benefit.
