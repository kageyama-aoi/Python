"""fixed_length_formatter のユニットテスト。

output_dir / log_dir を一時ディレクトリに向けるため、実際の data/ を汚染しない。
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from run import FormatOptions, format_fixed_length  # noqa: E402


class FormatFixedLengthTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmpdir = Path(self._tmp.name)
        self.output_dir = self.tmpdir / "output"
        self.log_dir = self.tmpdir / "logs"

    def tearDown(self):
        self._tmp.cleanup()

    def _make_input(self, data: bytes, name="input.dat") -> Path:
        path = self.tmpdir / name
        path.write_bytes(data)
        return path

    def _run(self, data: bytes, **opt_kwargs):
        options = FormatOptions(**{"record_bytes": 10, "encoding": "ascii", **opt_kwargs})
        return format_fixed_length(
            self._make_input(data), options,
            output_dir=self.output_dir, log_dir=self.log_dir)

    # ---- 基本動作

    def test_exact_multiple(self):
        """割り切れるファイル: 全レコードが改行付きで出力される"""
        result = self._run(b"0123456789" * 3)
        self.assertEqual(result.total_records, 3)
        self.assertEqual(result.tail_bytes, 0)
        self.assertEqual(result.warnings, [])
        content = result.output_path.read_bytes()
        self.assertEqual(content, b"0123456789\r\n" * 3)

    def test_lf_newline(self):
        """newline='lf' で LF 改行になる"""
        result = self._run(b"0123456789" * 2, newline="lf")
        self.assertEqual(result.output_path.read_bytes(), b"0123456789\n" * 2)

    def test_tail_record_is_kept_with_warning(self):
        """半端な末尾レコードも出力され、警告が記録される"""
        result = self._run(b"0123456789" * 2 + b"abcde")
        self.assertEqual(result.total_records, 2)
        self.assertEqual(result.tail_bytes, 5)
        self.assertTrue(any("半端" in w for w in result.warnings))
        self.assertTrue(result.output_path.read_bytes().endswith(b"abcde\r\n"))

    def test_bom_is_skipped(self):
        """UTF-8 BOM は読み飛ばされ、レコード境界がズレない"""
        result = self._run(b"\xef\xbb\xbf" + b"0123456789" * 2)
        self.assertTrue(result.bom_skipped)
        self.assertEqual(result.total_records, 2)
        self.assertEqual(result.output_path.read_bytes(), b"0123456789\r\n" * 2)

    def test_output_written_to_run_subdir(self):
        """出力は <stem>_<日時>/ サブディレクトリに <stem>_formatted 名で置かれる"""
        result = self._run(b"0123456789")
        self.assertEqual(result.output_path.parent.parent, self.output_dir)
        self.assertRegex(result.output_path.parent.name, r"^input_\d{8}_\d{6}$")
        self.assertEqual(result.output_path.name, "input_formatted.dat")

    # ---- 境界チェック

    def test_boundary_ok_with_correct_length(self):
        """レコード長が正しければ boundary_ok=True（CP932全角込み）"""
        record = "あいう太郎".encode("cp932")  # 10バイト
        result = self._run(record * 2, encoding="cp932")
        self.assertIs(result.boundary_ok, True)

    def test_boundary_ng_with_wrong_length(self):
        """レコード長がズレて全角文字の途中で切れると boundary_ok=False で警告"""
        record = "あいう太郎".encode("cp932")  # 10バイト
        options = FormatOptions(record_bytes=9, encoding="cp932")  # わざと1バイト短く
        result = format_fixed_length(
            self._make_input(record * 2), options,
            output_dir=self.output_dir, log_dir=self.log_dir)
        self.assertIs(result.boundary_ok, False)
        self.assertTrue(any("デコード" in w for w in result.warnings))

    # ---- ストリーム動作（chunk境界をまたぐレコード）

    def test_records_across_chunk_boundary(self):
        """1MB chunk の境界をまたぐレコードが壊れない"""
        record = b"x" * 7  # 1MB と互いに素なレコード長
        count = (1024 * 1024 * 2) // 7 + 3
        result = self._run(record * count, record_bytes=7)
        self.assertEqual(result.total_records, count)
        self.assertEqual(result.tail_bytes, 0)

    # ---- バリデーション・ログ

    def test_validate_rejects_bad_values(self):
        for bad in (0, -1, "10"):
            with self.assertRaises(ValueError):
                FormatOptions(record_bytes=bad).validate()
        with self.assertRaises(ValueError):
            FormatOptions(record_bytes=10, newline="cr").validate()

    def test_log_is_written(self):
        """正常時にログへ実行条件と件数が記録される"""
        result = self._run(b"0123456789" * 3)
        content = result.log_path.read_text(encoding="utf-8")
        self.assertIn("record_bytes: 10", content)
        self.assertIn("total_records: 3", content)
        self.assertIn("input.dat", content)


if __name__ == "__main__":
    unittest.main()
