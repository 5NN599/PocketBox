import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pocketbox_settings


class PocketBoxSettingsTests(unittest.TestCase):
    def test_defaults_to_english_when_settings_are_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(pocketbox_settings, "settings_file", return_value=Path(temporary) / "missing.json"):
                self.assertEqual(pocketbox_settings.get_language(), "en")

    def test_saves_and_loads_language_preference(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "PocketBox" / "settings.json"
            with patch.object(pocketbox_settings, "settings_file", return_value=path):
                pocketbox_settings.set_language("ko")
                self.assertEqual(pocketbox_settings.get_language(), "ko")
                self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"language": "ko"})

    def test_invalid_language_is_rejected(self):
        with self.assertRaises(ValueError):
            pocketbox_settings.set_language("fr")

    def test_invalid_settings_values_fall_back_to_english(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "settings.json"
            path.write_text(json.dumps({"language": ["not", "a", "language"]}), encoding="utf-8")
            with patch.object(pocketbox_settings, "settings_file", return_value=path):
                self.assertEqual(pocketbox_settings.get_language(), "en")

    def test_known_format_error_is_translated_to_english(self):
        original = "파일 무결성 검사에 실패했습니다: assets/icon.png"
        self.assertEqual(
            pocketbox_settings.translate_error_text(original, "en"),
            "File integrity check failed: assets/icon.png",
        )
        self.assertEqual(pocketbox_settings.translate_error_text(original, "ko"), original)


if __name__ == "__main__":
    unittest.main()
