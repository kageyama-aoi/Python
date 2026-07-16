"""
run.py のユニットテスト。
output_dir / log_dir を引数で一時ディレクトリに向けるため、実際の output/ logs/ を汚染しない。
"""
import csv
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from run import SplitOptions, SplitResult, _detect_delimiter, split_csv, write_log


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


def _make_options(
    rows_per_file: int = 3,
    encoding: str = "utf-8",
    has_header: bool = False,
    delimiter: str | None = None,
) -> SplitOptions:
    return SplitOptions(
        rows_per_file=rows_per_file,
        encoding=encoding,
        has_header=has_header,
        delimiter=delimiter,
    )


# ------------------------------------------------------------------
# SplitOptions
# ------------------------------------------------------------------

class TestSplitOptions(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write_config(self, cfg: dict) -> Path:
        path = self.tmpdir / "config.json"
        path.write_text(json.dumps(cfg), encoding="utf-8")
        return path

    def test_from_config_file(self):
        path = self._write_config(
            {"rows_per_file": 500, "encoding": "cp932", "has_header": True, "delimiter": ";"}
        )
        opts = SplitOptions.from_config_file(path)
        self.assertEqual(opts.rows_per_file, 500)
        self.assertEqual(opts.encoding, "cp932")
        self.assertTrue(opts.has_header)
        self.assertEqual(opts.delimiter, ";")

    def test_from_config_file_defaults(self):
        """has_header 省略時は True、delimiter 省略・null・空文字は None（自動判定）"""
        path = self._write_config({"rows_per_file": 100, "encoding": "utf-8"})
        opts = SplitOptions.from_config_file(path)
        self.assertTrue(opts.has_header)
        self.assertIsNone(opts.delimiter)

        path = self._write_config({"rows_per_file": 100, "encoding": "utf-8", "delimiter": None})
        self.assertIsNone(SplitOptions.from_config_file(path).delimiter)

        path = self._write_config({"rows_per_file": 100, "encoding": "utf-8", "delimiter": ""})
        self.assertIsNone(SplitOptions.from_config_file(path).delimiter)

    def test_validate_rejects_zero(self):
        with self.assertRaises(ValueError):
            _make_options(rows_per_file=0).validate()

    def test_validate_rejects_negative(self):
        with self.assertRaises(ValueError):
            _make_options(rows_per_file=-1).validate()

    def test_validate_rejects_non_bool_header(self):
        opts = SplitOptions(rows_per_file=10, encoding="utf-8", has_header="yes")
        with self.assertRaises(ValueError):
            opts.validate()


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
        self.output_dir = self.tmpdir / "output"
        self.log_dir = self.tmpdir / "logs"

    def tearDown(self):
        self._tmp.cleanup()

    def _split(self, input_path: Path, options: SplitOptions, **kwargs):
        return split_csv(
            input_path, options, output_dir=self.output_dir, log_dir=self.log_dir, **kwargs
        )

    # --- 基本分割 ---

    def test_exact_split(self):
        """9行を3件ずつ → 3ファイル、各3レコード"""
        rows = [[str(i), f"v{i}"] for i in range(9)]
        path = _make_csv(self.tmpdir, rows)

        result = self._split(path, _make_options(rows_per_file=3))

        self.assertEqual(result.total_rows, 9)
        self.assertEqual(len(result.output_summaries), 3)
        for _, count in result.output_summaries:
            self.assertEqual(count, 3)

    def test_split_with_remainder(self):
        """10行を3件ずつ → 4ファイル（3+3+3+1）"""
        rows = [[str(i)] for i in range(10)]
        path = _make_csv(self.tmpdir, rows)

        result = self._split(path, _make_options(rows_per_file=3))

        self.assertEqual(result.total_rows, 10)
        self.assertEqual(len(result.output_summaries), 4)
        self.assertEqual(result.output_summaries[-1][1], 1)

    def test_rows_per_file_larger_than_data(self):
        """rows_per_file が総行数より大きい → 1ファイルにまとまる"""
        rows = [[str(i)] for i in range(5)]
        path = _make_csv(self.tmpdir, rows)

        result = self._split(path, _make_options(rows_per_file=100))

        self.assertEqual(result.total_rows, 5)
        self.assertEqual(len(result.output_summaries), 1)

    # --- 出力サブディレクトリ ---

    def test_output_written_to_run_subdir(self):
        """分割ファイルは output/<stem>_<日時>/ サブディレクトリに出力される"""
        rows = [[str(i)] for i in range(4)]
        path = _make_csv(self.tmpdir, rows, filename="myinput.csv")

        result = self._split(path, _make_options(rows_per_file=2))

        self.assertEqual(result.output_dir.parent, self.output_dir)
        self.assertRegex(result.output_dir.name, r"^myinput_\d{8}_\d{6}$")
        for fname, _ in result.output_summaries:
            self.assertTrue((result.output_dir / fname).exists())
        # output_dir 直下には分割ファイルを直接置かない
        top_level_files = [p for p in self.output_dir.iterdir() if p.is_file()]
        self.assertEqual(top_level_files, [])

    def test_no_empty_subdir_on_empty_input(self):
        """データ0行の入力ではサブディレクトリを作らない"""
        path = _make_csv(self.tmpdir, [])
        result = self._split(path, _make_options(rows_per_file=10))

        self.assertEqual(result.total_rows, 0)
        self.assertFalse(result.output_dir.exists())

    # --- ヘッダー ---

    def test_header_replicated_in_each_file(self):
        """has_header=True: 各分割ファイルの1行目がヘッダー"""
        rows = [["id", "name"]] + [[str(i), f"name{i}"] for i in range(6)]
        path = _make_csv(self.tmpdir, rows)

        result = self._split(path, _make_options(rows_per_file=3, has_header=True))

        self.assertEqual(result.total_rows, 6)
        for fname, _ in result.output_summaries:
            out = result.output_dir / fname
            with open(out, encoding="utf-8", newline="") as f:
                first_row = next(csv.reader(f))
            self.assertEqual(first_row, ["id", "name"])

    def test_no_header_all_rows_are_data(self):
        """has_header=False: ヘッダー行なし、全行がデータ"""
        rows = [[str(i)] for i in range(6)]
        path = _make_csv(self.tmpdir, rows)

        result = self._split(path, _make_options(rows_per_file=6, has_header=False))

        self.assertEqual(result.total_rows, 6)
        self.assertEqual(len(result.output_summaries), 1)

    # --- TSV ---

    def test_tab_delimiter(self):
        """タブ区切りファイルも正しく分割される"""
        rows = [["a", "b"], ["c", "d"], ["e", "f"]]
        path = _make_csv(self.tmpdir, rows, delimiter="\t", filename="input.tsv")

        result = self._split(path, _make_options(rows_per_file=2))

        self.assertEqual(result.total_rows, 3)
        self.assertEqual(len(result.output_summaries), 2)

    # --- 戻り値 ---

    def test_return_types(self):
        """SplitResult を返し、主要フィールドの型が正しい"""
        rows = [[str(i)] for i in range(4)]
        path = _make_csv(self.tmpdir, rows)

        result = self._split(path, _make_options(rows_per_file=2))

        self.assertIsInstance(result, SplitResult)
        self.assertIsInstance(result.total_rows, int)
        self.assertIsInstance(result.output_summaries, list)
        self.assertIsInstance(result.output_dir, Path)
        self.assertIsInstance(result.log_path, Path)

    def test_log_file_created_on_success(self):
        """正常実行時にログファイルが生成され、出力先も記録される"""
        rows = [[str(i)] for i in range(3)]
        path = _make_csv(self.tmpdir, rows)

        result = self._split(path, _make_options(rows_per_file=10))

        self.assertTrue(result.log_path.exists())
        content = result.log_path.read_text(encoding="utf-8")
        self.assertIn("status: SUCCESS", content)
        self.assertIn("data_record_count: 3", content)
        self.assertIn(f"output_dir: {result.output_dir}", content)

    # --- 進捗コールバック ---

    def test_progress_callback_called(self):
        """10,000行ごとに progress コールバックが呼ばれる"""
        rows = [[str(i)] for i in range(20_001)]
        path = _make_csv(self.tmpdir, rows)
        messages: list[str] = []

        self._split(path, _make_options(rows_per_file=30_000), progress=messages.append)

        self.assertEqual(len(messages), 2)  # 10,000 / 20,000 行時点
        self.assertIn("10,000", messages[0])

    # --- エラー ---

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self._split(self.tmpdir / "nonexistent.csv", _make_options())

    def test_invalid_rows_per_file_zero(self):
        path = _make_csv(self.tmpdir, [["a"]])
        with self.assertRaises(ValueError):
            self._split(path, _make_options(rows_per_file=0))

    def test_invalid_rows_per_file_negative(self):
        path = _make_csv(self.tmpdir, [["a"]])
        with self.assertRaises(ValueError):
            self._split(path, _make_options(rows_per_file=-1))

    def test_error_log_written_on_failure(self):
        """読み込み途中のエラーでも finally でログが出力される"""
        path = self.tmpdir / "broken.csv"
        path.write_bytes("a,b\n".encode("utf-8") + b"\xff\xfe\x00" + "c,d\n".encode("utf-8"))

        with self.assertRaises(Exception):
            self._split(path, _make_options(rows_per_file=10))

        logs = list(self.log_dir.glob("split_log_*.log"))
        self.assertEqual(len(logs), 1)
        content = logs[0].read_text(encoding="utf-8")
        self.assertIn("status: ERROR", content)
        self.assertIn("error:", content)


# ------------------------------------------------------------------
# write_log
# ------------------------------------------------------------------

def _make_result(**overrides) -> SplitResult:
    now = datetime.now()
    defaults = dict(
        status="SUCCESS",
        started_at=now,
        ended_at=now,
        input_path=Path("input/test.csv"),
        rows_per_file=100,
        encoding="utf-8",
        delimiter=",",
        has_header=True,
        total_rows=100,
        output_summaries=[("out_001.csv", 100)],
        error_message="",
        output_dir=Path("output/test_20260101_000000"),
        log_path=Path("logs/split_log_20260101_000000.log"),
    )
    defaults.update(overrides)
    return SplitResult(**defaults)


class TestWriteLog(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _call(self, **overrides) -> str:
        log_path = self.tmpdir / "test.log"
        write_log(log_path, _make_result(**overrides))
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
        content = self._call(output_summaries=[("f1.csv", 50), ("f2.csv", 50)])
        self.assertIn("created_file_count: 2", content)

    def test_empty_summaries(self):
        content = self._call(output_summaries=[])
        self.assertIn("- (none)", content)

    def test_tab_delimiter_repr(self):
        """タブ区切りは \\t と表示される"""
        content = self._call(delimiter="\t")
        self.assertIn(r"delimiter: \t", content)

    def test_output_dir_recorded(self):
        """出力サブディレクトリのパスがログに記録される"""
        content = self._call(output_dir=Path("output/foo_20260101_000000"))
        self.assertIn("output_dir:", content)
        self.assertIn("foo_20260101_000000", content)


if __name__ == "__main__":
    unittest.main()
