# Security Policy

## Scope and important design note

PocketBox is a package format, packager, and launcher. **It is not a sandbox.**
Programs launched from a `.pbox` package run with the permissions of the current
Windows user. They may access that user's files, registry settings, devices, and
network resources.

The project validates package paths, checks manifest bounds, verifies compressed
stream lengths, and compares extracted file data against SHA-256 hashes. These
checks help detect malformed or modified package contents; they do not authenticate
the package publisher or isolate the launched program.

## Reporting a vulnerability

Please do not publish details of an exploitable vulnerability in a public issue.
Use GitHub's private vulnerability reporting feature for this repository when it is
enabled. If private reporting is unavailable, contact the repository maintainers
through a private channel before disclosing technical details publicly.

Include the affected version, operating system, reproduction steps, and impact.
Do not attach personal files, private data, or real credentials.

## Supported versions

Security fixes are intended for the latest published version. Older versions may
not receive updates.
