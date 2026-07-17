"""
analyze.py（入力ファイル事前解析ヘルパー）のユニットテスト。
tkinter の表示系には触れず、純粋なロジックのみ検証する。
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from analyze import (
    _count_rows,
    _detect_encoding_from_file,
    _fmt_size,
    _read_first_row,
    _suggest_rows,
)


# ------------------------------------------------------------------
# _fmt_size
# ------------------------------------------------------------------

class TestFmtSize(unittest.TestCase):
    def test_bytes(self):
        self.assertEqual(_fmt_size(512), "512.0 B")

    def test_kilobytes(self):
        self.assertEqual(_fmt_size(1024), "1.0 KB")

    def test_megabytes(self):
        self.assertEqual(_fmt_size(1024 * 1024), "1.0 MB")

    def test_gigabytes(self):
        self.assertEqual(_fmt_size(1024 ** 3), "1.0 GB")

    def test_fractional_kb(self):
        self.assertEqual(_fmt_size(1536), "1.5 KB")


# ------------------------------------------------------------------
# _suggest_rows
# ------------------------------------------------------------------

class TestSuggestRows(unittest.TestCase):
    def test_zero(self):
        self.assertIn("不明", _suggest_rows(0))

    def test_large(self):
        """1,000,000行 → 100,000行（10分割）"""
        result = _suggest_rows(1_000_000)
        self.assertIn("100,000", result)

    def test_medium(self):
        """100,000行 → 10,000行"""
        result = _suggest_rows(100_000)
        self.assertIn("10,000", result)

    def test_small(self):
        """500行 → 最低1,000行"""
        result = _suggest_rows(500)
        self.assertIn("1,000", result)

    def test_contains_約10ファイル(self):
        result = _suggest_rows(50_000)
        self.assertIn("約10ファイル", result)


# ------------------------------------------------------------------
# _detect_encoding_from_file
# ------------------------------------------------------------------

class TestDetectEncodingFromFile(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_utf8_bom(self):
        path = self.tmpdir / "bom.csv"
        path.write_bytes(b"\xef\xbb\xbf" + "id,name\n1,test\n".encode("utf-8"))
        self.assertEqual(_detect_encoding_from_file(path), "utf-8-sig")

    def test_utf8(self):
        path = self.tmpdir / "utf8.csv"
        path.write_text("id,name\n1,test\n", encoding="utf-8")
        self.assertEqual(_detect_encoding_from_file(path), "utf-8")

    def test_shift_jis(self):
        path = self.tmpdir / "sjis.csv"
        path.write_text("id,名前\n1,テスト\n", encoding="shift_jis")
        result = _detect_encoding_from_file(path)
        self.assertIn(result, ("shift_jis", "cp932"))


# ------------------------------------------------------------------
# _count_rows
# ------------------------------------------------------------------

class TestCountRows(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_basic(self):
        """4行のファイル → 改行4つ"""
        path = self.tmpdir / "test.csv"
        path.write_text("a,b\n1,2\n3,4\n5,6\n", encoding="utf-8")
        self.assertEqual(_count_rows(path), 4)

    def test_empty(self):
        path = self.tmpdir / "empty.csv"
        path.write_bytes(b"")
        self.assertEqual(_count_rows(path), 0)

    def test_single_row(self):
        path = self.tmpdir / "one.csv"
        path.write_text("a,b,c\n", encoding="utf-8")
        self.assertEqual(_count_rows(path), 1)

    def test_large_chunk(self):
        """1MB超のファイルでも正確にカウント"""
        path = self.tmpdir / "large.csv"
        n = 5000
        path.write_text("\n".join(f"{i},value{i}" for i in range(n)) + "\n", encoding="utf-8")
        self.assertEqual(_count_rows(path), n)


# ------------------------------------------------------------------
# _read_first_row
# ------------------------------------------------------------------

class TestReadFirstRow(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_basic(self):
        path = self.tmpdir / "test.csv"
        path.write_text("id,name,value\n1,test,100\n", encoding="utf-8")
        col_count, preview = _read_first_row(path, "utf-8", ",")
        self.assertEqual(col_count, 3)
        self.assertIn("id", preview)
        self.assertIn("name", preview)

    def test_single_column(self):
        path = self.tmpdir / "single.csv"
        path.write_text("code\n001\n", encoding="utf-8")
        col_count, preview = _read_first_row(path, "utf-8", ",")
        self.assertEqual(col_count, 1)

    def test_many_columns_truncated(self):
        """9列以上は先頭8列 + 省略表示"""
        cols = [f"col{i}" for i in range(10)]
        path = self.tmpdir / "wide.csv"
        path.write_text(",".join(cols) + "\n", encoding="utf-8")
        col_count, preview = _read_first_row(path, "utf-8", ",")
        self.assertEqual(col_count, 10)
        self.assertIn("+", preview)  # "+2列" のような省略表示

    def test_tab_delimiter(self):
        path = self.tmpdir / "test.tsv"
        path.write_text("id\tname\n1\ttest\n", encoding="utf-8")
        col_count, preview = _read_first_row(path, "utf-8", "\t")
        self.assertEqual(col_count, 2)

    def test_nonexistent_file(self):
        """存在しないファイルはエラーにならず (0, '(読み取り失敗)') を返す"""
        col_count, preview = _read_first_row(self.tmpdir / "ghost.csv", "utf-8", ",")
        self.assertEqual(col_count, 0)
        self.assertIn("読み取り失敗", preview)


if __name__ == "__main__":
    unittest.main()
