# PocketBox Container Format (Version 1)

This note describes the current `.pbox` container emitted by `pocketbox_format.py`.
The format is versioned and should be treated as an implementation format until a
formal compatibility policy is published.

## Binary layout

| Offset | Size | Description |
|---:|---:|---|
| 0 | 8 bytes | Magic bytes: ASCII `PBOXPK01` |
| 8 | 8 bytes | Unsigned little-endian manifest length (`uint64`) |
| 16 | variable | UTF-8 JSON manifest |
| `16 + manifest_length` | remaining bytes | Concatenated compressed file streams |

The fixed header is encoded with Python `struct` format `<8sQ`.

## Manifest

The manifest is a UTF-8 JSON object with these top-level fields:

- `format_version`: currently `1`.
- `target`: relative path of the EXE selected as the startup program.
- `working_directory`: either `target_dir` or `bundle_root`.
- `entries`: an array of directory and file entries.

A directory entry contains `path` and `kind: "dir"`. A file entry contains:

- `path`: package-relative path using `/` separators.
- `kind`: `"file"`.
- `size`: uncompressed byte count.
- `offset`: byte offset relative to the beginning of the compressed-data section.
- `compressed_size`: byte count of the zlib stream.
- `sha256`: lowercase hexadecimal SHA-256 digest of the uncompressed file bytes.

Every file is stored as an independent zlib stream. Directory entries preserve empty folders.

## Validation limits

The implementation currently limits the manifest to 64 MiB and the entry count to
250,000. Paths are validated for Windows compatibility; absolute paths, traversal
components, reserved Windows device names, unsupported characters, symbolic links,
and reparse points are rejected. During extraction, data ranges, decompressed sizes,
zlib stream completion, and SHA-256 hashes are checked.

## Compatibility

Do not change the meaning of existing version 1 fields in a backwards-incompatible
way. A future incompatible format should use a new magic/version and must retain a
clear reader path for older packages where practical.
