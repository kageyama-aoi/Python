"""
run.py のユニットテスト。
OUTPUT_DIR / LOG_DIR を一時ディレクトリに差し替えてファイルシステムを汚染しない。
"""
import csv
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
import run
from run import _detect_delimiter, split_csv, write_log


# ------------------------------------------------------------------
# ヘルパー
# ------------------------------------------------------------------

def _make_csv(
    tmpdir: Path,
    rows: list,
    encoding: str = "utf-8",
    delimiter: str = ",",
    filename: str = "input.csv",
) -> Path:
    path = tmpdir / filename
    with open(path, "w", encoding=encoding, newline="") as f:
        writer = csv.writer(f, delimiter=delimiter)
        for row in rows:
            writer.writerow(row)
    return path


def _make_config(
    tmpdir: Path,
    rows_per_file: int = 3,
    encoding: str = "utf-8",
    has_header: bool = False,
    delimiter: str | None = None,
) -> Path:
    cfg: dict = {"rows_per_file": rows_per_file, "encoding": encoding, "has_header": has_header}
    if delimiter is not None:
        cfg["delimiter"] = delimiter
    path = tmpdir / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


# ------------------------------------------------------------------
# _detect_delimiter
# ------------------------------------------------------------------

class TestDetectDelimiter(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_comma(self):
        path = _make_csv(self.tmpdir, [["a", "b", "c"], [1, 2, 3]])
        self.assertEqual(_detect_delimiter(path, "utf-8", ".csv"), ",")

    def test_tab(self):
        path = _make_csv(self.tmpdir, [["a", "b", "c"]], delimiter="\t", filename="input.tsv")
        self.assertEqual(_detect_delimiter(path, "utf-8", ".tsv"), "\t")

    def test_semicolon(self):
        path = self.tmpdir / "input.csv"
        path.write_text("a;b;c\n1;2;3\n4;5;6\n", encoding="utf-8")
        self.assertEqual(_detect_delimiter(path, "utf-8", ".csv"), ";")

    def test_fallback_csv_extension(self):
        """区切り文字が全くないファイルは拡張子でフォールバック"""
        path = self.tmpdir / "input.csv"
        path.write_text("abc\ndef\n", encoding="utf-8")
        self.assertEqual(_detect_delimiter(path, "utf-8", ".csv"), ",")

    def test_fallback_tsv_extension(self):
        path = self.tmpdir / "input.tsv"
        path.write_text("abc\ndef\n", encoding="utf-8")
        self.assertEqual(_detect_delimiter(path, "utf-8", ".tsv"), "\t")


# ------------------------------------------------------------------
# split_csv
# ------------------------------------------------------------------

class TestSplitCsv(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)
        # OUTPUT_DIR / LOG_DIR を一時ディレクトリに差し替え
        self._orig_output = run.OUTPUT_DIR
        self._orig_log = run.LOG_DIR
        run.OUTPUT_DIR = self.tmpdir / "output"
        run.LOG_DIR = self.tmpdir / "logs"

    def tearDown(self):
        run.OUTPUT_DIR = self._orig_output
        run.LOG_DIR = self._orig_log
        self._tmp.cleanup()

    # --- 基本分割 ---

    def test_exact_split(self):
        """9行を3件ずつ → 3ファイル、各3レコード"""
        rows = [[str(i), f"v{i}"] for i in range(9)]
        path = _make_csv(self.tmpdir, rows)
        cfg = _make_config(self.tmpdir, rows_per_file=3)

        total, summaries, _ = split_csv(path, cfg)

        self.assertEqual(total, 9)
        self.assertEqual(len(summaries), 3)
        for _, count in summaries:
            self.assertEqual(count, 3)

    def test_split_with_remainder(self):
        """10行を3件ずつ → 4ファイル（3+3+3+1）"""
        rows = [[str(i)] for i in range(10)]
        path = _make_csv(self.tmpdir, rows)
        cfg = _make_config(self.tmpdir, rows_per_file=3)

        total, summaries, _ = split_csv(path, cfg)

        self.assertEqual(total, 10)
        self.assertEqual(len(summaries), 4)
        self.assertEqual(summaries[-1][1], 1)

    def test_rows_per_file_larger_than_data(self):
        """rows_per_file が総行数より大きい → 1ファイルにまとまる"""
        rows = [[str(i)] for i in range(5)]
        path = _make_csv(self.tmpdir, rows)
        cfg = _make_config(self.tmpdir, rows_per_file=100)

        total, summaries, _ = split_csv(path, cfg)

        self.assertEqual(total, 5)
        self.assertEqual(len(summaries), 1)

    # --- ヘッダー ---

    def test_header_replicated_in_each_file(self):
        """has_header=True: 各分割ファイルの1行目がヘッダー"""
        rows = [["id", "name"]] + [[str(i), f"name{i}"] for i in range(6)]
        path = _make_csv(self.tmpdir, rows)
        cfg = _make_config(self.tmpdir, rows_per_file=3, has_header=True)

        total, summaries, _ = split_csv(path, cfg)

        self.assertEqual(total, 6)
        for fname, _ in summaries:
            out = run.OUTPUT_DIR / fname
            with open(out, encoding="utf-8", newline="") as f:
                first_row = next(csv.reader(f))
            self.assertEqual(first_row, ["id", "name"])

    def test_no_header_all_rows_are_data(self):
        """has_header=False: ヘッダー行なし、全行がデータ"""
        rows = [[str(i)] for i in range(6)]
        path = _make_csv(self.tmpdir, rows)
        cfg = _make_config(self.tmpdir, rows_per_file=6, has_header=False)

        total, summaries, _ = split_csv(path, cfg)

        self.assertEqual(total, 6)
        self.assertEqual(len(summaries), 1)

    # --- TSV ---

    def test_tab_delimiter(self):
        """タブ区切りファイルも正しく分割される"""
        rows = [["a", "b"], ["c", "d"], ["e", "f"]]
        path = _make_csv(self.tmpdir, rows, delimiter="\t", filename="input.tsv")
        cfg = _make_config(self.tmpdir, rows_per_file=2)

        total, summaries, _ = split_csv(path, cfg)

        self.assertEqual(total, 3)
        self.assertEqual(len(summaries), 2)

    # --- 戻り値 ---

    def test_return_types(self):
        """(int, list, Path) を返す"""
        rows = [[str(i)] for i in range(4)]
        path = _make_csv(self.tmpdir, rows)
        cfg = _make_config(self.tmpdir, rows_per_file=2)

        result = split_csv(path, cfg)

        self.assertIsInstance(result[0], int)
        self.assertIsInstance(result[1], list)
        self.assertIsInstance(result[2], Path)

    def test_log_file_created_on_success(self):
        """正常実行時にログファイルが生成される"""
        rows = [[str(i)] for i in range(3)]
        path = _make_csv(self.tmpdir, rows)
        cfg = _make_config(self.tmpdir, rows_per_file=10)

        _, _, log_path = split_csv(path, cfg)

        self.assertTrue(log_path.exists())
        content = log_path.read_text(encoding="utf-8")
        self.assertIn("status: SUCCESS", content)
        self.assertIn("data_record_count: 3", content)

    # --- エラー ---

    def test_file_not_found(self):
        cfg = _make_config(self.tmpdir)
        with self.assertRaises(FileNotFoundError):
            split_csv(self.tmpdir / "nonexistent.csv", cfg)

    def test_invalid_rows_per_file_zero(self):
        path = _make_csv(self.tmpdir, [["a"]])
        cfg = _make_config(self.tmpdir, rows_per_file=0)
        with self.assertRaises(ValueError):
            split_csv(path, cfg)

    def test_invalid_rows_per_file_negative(self):
        path = _make_csv(self.tmpdir, [["a"]])
        cfg = _make_config(self.tmpdir, rows_per_file=-1)
        with self.assertRaises(ValueError):
            split_csv(path, cfg)


# ------------------------------------------------------------------
# write_log
# ------------------------------------------------------------------

class TestWriteLog(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _call(self, status="SUCCESS", total_rows=100, summaries=None, error_message=""):
        if summaries is None:
            summaries = [("out_001.csv", 100)]
        now = datetime.now()
        log_path = self.tmpdir / "test.log"
        write_log(
            log_path=log_path,
            status=status,
            started_at=now,
            ended_at=now,
            input_path=Path("input/test.csv"),
            rows_per_file=100,
            encoding="utf-8",
            delimiter=",",
            has_header=True,
            total_rows=total_rows,
            output_summaries=summaries,
            error_message=error_message,
        )
        return log_path.read_text(encoding="utf-8")

    def test_success_status(self):
        content = self._call(status="SUCCESS")
        self.assertIn("status: SUCCESS", content)

    def test_error_status(self):
        content = self._call(status="ERROR", error_message="何かが壊れた")
        self.assertIn("status: ERROR", content)
        self.assertIn("何かが壊れた", content)

    def test_data_record_count(self):
        content = self._call(total_rows=250)
        self.assertIn("data_record_count: 250", content)

    def test_created_file_count(self):
        summaries = [("f1.csv", 50), ("f2.csv", 50)]
        content = self._call(summaries=summaries)
        self.assertIn("created_file_count: 2", content)

    def test_empty_summaries(self):
        content = self._call(summaries=[])
        self.assertIn("- (none)", content)

    def test_tab_delimiter_repr(self):
        """タブ区切りは \\t と表示される"""
        now = datetime.now()
        log_path = self.tmpdir / "tab.log"
        write_log(
            log_path=log_path,
            status="SUCCESS",
            started_at=now,
            ended_at=now,
            input_path=Path("input/test.tsv"),
            rows_per_file=10,
            encoding="utf-8",
            delimiter="\t",
            has_header=False,
            total_rows=10,
            output_summaries=[("out.tsv", 10)],
        )
        content = log_path.read_text(encoding="utf-8")
        self.assertIn(r"delimiter: \t", content)


if __name__ == "__main__":
    unittest.main()
