import tempfile
import unittest
from pathlib import Path

from src.config_io import OrganizeConfig
from src.organizer import (
    ACTION_MOVE,
    ACTION_RENAME,
    ACTION_SKIP,
    build_plan,
    execute_plan,
)


def _touch(path: Path, content: str = "x") -> Path:
    path.write_text(content, encoding="utf-8")
    return path


class BuildPlanTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.cfg = OrganizeConfig(
            target_dir=self.target,
            log_dir_name="logs",
            extension_groups={"images": ["jpg", "png"]},
            exclude_filenames={"desktop.ini"},
            exclude_extensions={"exe"},
        )

    def _plan_by_name(self):
        return {p.source.name: p for p in build_plan(self.target, self.cfg)}

    def test_group_and_bare_extension(self):
        _touch(self.target / "a.jpg")
        _touch(self.target / "b.txt")
        plan = self._plan_by_name()
        self.assertEqual(plan["a.jpg"].dest_dir, self.target / "images")
        self.assertEqual(plan["b.txt"].dest_dir, self.target / "txt")
        self.assertTrue(plan["a.jpg"].creates_dir)

    def test_no_extension_folder(self):
        _touch(self.target / "README")
        plan = self._plan_by_name()
        self.assertEqual(plan["README"].dest_dir, self.target / "no_extension")

    def test_exclude_by_name_and_extension(self):
        _touch(self.target / "desktop.ini")
        _touch(self.target / "setup.exe")
        plan = self._plan_by_name()
        self.assertEqual(plan["desktop.ini"].action, ACTION_SKIP)
        self.assertEqual(plan["setup.exe"].action, ACTION_SKIP)
        self.assertIn("除外", plan["setup.exe"].reason)

    def test_skips_subdirectories_and_log_dir(self):
        (self.target / "logs").mkdir()
        (self.target / "somedir").mkdir()
        plan = self._plan_by_name()
        self.assertEqual(plan["logs"].action, ACTION_SKIP)
        self.assertEqual(plan["somedir"].action, ACTION_SKIP)

    def test_collision_against_existing_file(self):
        images = self.target / "images"
        images.mkdir()
        _touch(images / "photo.jpg")
        _touch(self.target / "photo.jpg")
        plan = self._plan_by_name()
        self.assertEqual(plan["photo.jpg"].action, ACTION_RENAME)
        self.assertEqual(plan["photo.jpg"].dest_name, "photo_2.jpg")

    def test_chained_collision_against_existing_files(self):
        images = self.target / "images"
        images.mkdir()
        _touch(images / "p.jpg")
        _touch(images / "p_2.jpg")
        _touch(self.target / "p.jpg")
        plan = self._plan_by_name()
        self.assertEqual(plan["p.jpg"].dest_name, "p_3.jpg")


class ExecutePlanTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.target = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.cfg = OrganizeConfig(
            target_dir=self.target,
            extension_groups={"images": ["jpg"]},
            exclude_extensions={"exe"},
        )

    def test_moves_files_and_creates_dirs(self):
        _touch(self.target / "a.jpg")
        _touch(self.target / "b.csv")
        _touch(self.target / "skip.exe")
        logs: list[tuple[str, str]] = []
        result = execute_plan(
            build_plan(self.target, self.cfg), on_log=lambda m, lv: logs.append((m, lv))
        )
        self.assertEqual(result.moved, 2)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.failed, 0)
        self.assertTrue((self.target / "images" / "a.jpg").exists())
        self.assertTrue((self.target / "csv" / "b.csv").exists())
        self.assertTrue((self.target / "skip.exe").exists())
        self.assertFalse((self.target / "a.jpg").exists())

    def test_rename_on_execute(self):
        (self.target / "images").mkdir()
        _touch(self.target / "images" / "p.jpg", "old")
        _touch(self.target / "p.jpg", "new")
        result = execute_plan(build_plan(self.target, self.cfg))
        self.assertEqual(result.renamed, 1)
        self.assertTrue((self.target / "images" / "p_2.jpg").exists())
        self.assertEqual(
            (self.target / "images" / "p_2.jpg").read_text(encoding="utf-8"), "new"
        )


if __name__ == "__main__":
    unittest.main()
