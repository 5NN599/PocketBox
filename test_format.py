import tempfile
import unittest
from pathlib import Path

from pocketbox_format import build_payload, extract_payload, validate_relative_path


class PocketBoxFormatTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            (source / "assets" / "nested").mkdir(parents=True)
            (source / "empty-folder").mkdir()
            (source / "Game.exe").write_bytes(b"MZ" + b"executable-data" * 300)
            (source / "assets" / "nested" / "blob.dat").write_bytes(bytes(range(256)) * 400)
            (source / "zero.dat").write_bytes(b"")

            payload = base / "bundle.pbox"
            original_exe = (source / "Game.exe").read_bytes()
            original_blob = (source / "assets" / "nested" / "blob.dat").read_bytes()
            count, total = build_payload(source, "Game.exe", payload)
            self.assertTrue((source / "Game.exe").is_file())
            self.assertTrue((source / "assets" / "nested" / "blob.dat").is_file())
            self.assertEqual((source / "Game.exe").read_bytes(), original_exe)
            self.assertEqual((source / "assets" / "nested" / "blob.dat").read_bytes(), original_blob)
            self.assertEqual(count, 3)
            self.assertEqual(total, (source / "Game.exe").stat().st_size +
                             (source / "assets" / "nested" / "blob.dat").stat().st_size)

            destination = base / "extracted"
            root, target = extract_payload(payload, destination)
            self.assertEqual(target.read_bytes(), (source / "Game.exe").read_bytes())
            self.assertEqual(
                (root / "assets" / "nested" / "blob.dat").read_bytes(),
                (source / "assets" / "nested" / "blob.dat").read_bytes(),
            )
            self.assertTrue((root / "empty-folder").is_dir())
            self.assertEqual((root / "zero.dat").read_bytes(), b"")

    def test_rejects_traversal_and_windows_special_names(self):
        for path in ("../escape.txt", "a/../../escape", "/absolute.txt", "C:/drive.txt",
                     "a\\b.txt", "CON", "folder/NUL.txt", "trailing.", "bad:name"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    validate_relative_path(path)

    def test_detects_corruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            source.mkdir()
            (source / "Game.exe").write_bytes(b"MZ" + b"A" * 1000)
            payload = base / "bundle.pbox"
            build_payload(source, "Game.exe", payload)
            raw = bytearray(payload.read_bytes())
            raw[-1] ^= 0xFF
            payload.write_bytes(raw)
            with self.assertRaises(Exception):
                extract_payload(payload, base / "out")


if __name__ == "__main__":
    unittest.main()
