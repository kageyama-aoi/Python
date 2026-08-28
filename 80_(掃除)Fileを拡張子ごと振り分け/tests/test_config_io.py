import tempfile
import unittest
from pathlib import Path

from src.config_io import OrganizeConfig, load_config, save_config

SAMPLE_INI = """\
[Settings]
TargetDirectory = C:\\Users\\test\\Downloads
LogDirectoryName = logs

[ExtensionGroups]
images = jpg, jpeg, png
documents = pdf, docx

[Exclude]
filenames = desktop.ini, thumbs.db
extensions = exe, MSI
"""


class LoadConfigTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.ini = self.tmp / "config.ini"
        self.ini.write_text(SAMPLE_INI, encoding="utf-8")

    def test_parses_settings(self):
        cfg = load_config(self.ini)
        self.assertEqual(cfg.target_dir, Path("C:\\Users\\test\\Downloads"))
        self.assertEqual(cfg.log_dir_name, "logs")

    def test_parses_extension_groups(self):
        cfg = load_config(self.ini)
        self.assertEqual(cfg.extension_groups["images"], ["jpg", "jpeg", "png"])
        self.assertEqual(cfg.extension_to_folder["png"], "images")
        self.assertEqual(cfg.extension_to_folder["pdf"], "documents")

    def test_exclude_extensions_lowercased(self):
        cfg = load_config(self.ini)
        self.assertEqual(cfg.exclude_extensions, {"exe", "msi"})
        self.assertEqual(cfg.exclude_filenames, {"desktop.ini", "thumbs.db"})

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_config(self.tmp / "nope.ini")

    def test_default_log_dir_name(self):
        (self.tmp / "b.ini").write_text(
            "[Settings]\nTargetDirectory = X:\\data\n", encoding="utf-8"
        )
        cfg = load_config(self.tmp / "b.ini")
        self.assertEqual(cfg.log_dir_name, "logs")


class SaveConfigTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_round_trip(self):
        cfg = OrganizeConfig(
            target_dir=Path("D:\\inbox"),
            log_dir_name="_log",
            extension_groups={"images": ["jpg", "png"]},
            exclude_filenames={"desktop.ini"},
            exclude_extensions={"exe"},
        )
        out = self.tmp / "config.ini"
        save_config(out, cfg)
        reloaded = load_config(out)
        self.assertEqual(reloaded.target_dir, Path("D:\\inbox"))
        self.assertEqual(reloaded.log_dir_name, "_log")
        self.assertEqual(reloaded.extension_groups, {"images": ["jpg", "png"]})
        self.assertEqual(reloaded.exclude_filenames, {"desktop.ini"})
        self.assertEqual(reloaded.exclude_extensions, {"exe"})

    def test_saved_file_keeps_comments(self):
        cfg = OrganizeConfig(target_dir=Path("D:\\inbox"), extension_groups={"images": ["jpg"]})
        out = self.tmp / "config.ini"
        save_config(out, cfg)
        text = out.read_text(encoding="utf-8")
        comment_lines = [ln for ln in text.splitlines() if ln.strip().startswith(";")]
        self.assertGreaterEqual(len(comment_lines), 3)
        # コメント付きでも読み戻せる
        self.assertEqual(load_config(out).extension_groups, {"images": ["jpg"]})

    def test_percent_in_path_survives(self):
        cfg = OrganizeConfig(target_dir=Path(r"C:\Users\me\Downloads\%TEMP%_data"))
        out = self.tmp / "config.ini"
        save_config(out, cfg)
        self.assertEqual(
            load_config(out).target_dir, Path(r"C:\Users\me\Downloads\%TEMP%_data")
        )


if __name__ == "__main__":
    unittest.main()
