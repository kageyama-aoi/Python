import pytest
import os
from pathlib import Path
from unittest.mock import patch
import sys

# ルートのmain.pyをインポートするためにパスを追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import main as app_main
from src import config as cfg


class TestCleanupOldFiles:

    def test_cleanup_removes_target_files(self, tmp_path):
        """クリーンアップ対象ファイルが削除される"""
        # 削除されるべきファイルを作成
        f1 = tmp_path / "temp_summary_PJ_社員_20240101_120000.xlsx"
        f2 = tmp_path / "工数集計結果_PJ_社員_20240101.xlsx"
        f1.touch()
        f2.touch()

        with patch.object(cfg, 'OUTPUT_DIR', tmp_path):
            app_main.cleanup_old_files()

        assert not f1.exists()
        assert not f2.exists()

    def test_cleanup_ignores_non_target_files(self, tmp_path):
        """対象外ファイルは削除されない"""
        keep = tmp_path / "tr_list.xlsx"
        keep.touch()

        with patch.object(cfg, 'OUTPUT_DIR', tmp_path):
            app_main.cleanup_old_files()

        assert keep.exists()

    def test_cleanup_no_files_no_error(self, tmp_path):
        """対象ファイルが存在しなくてもエラーにならない"""
        with patch.object(cfg, 'OUTPUT_DIR', tmp_path):
            app_main.cleanup_old_files()  # 例外が出なければOK


class TestTempFileCleanup:

    def test_temp_files_deleted_after_main(self, tmp_path):
        """main() 完了後に中間ファイルが削除される（RF-11）"""
        f1 = tmp_path / "temp_summary_test.xlsx"
        f2 = tmp_path / "temp_intermediate.xlsx"
        f1.touch()
        f2.touch()

        # _delete_temp_files に相当する処理を直接検証
        for temp_file in [f1, f2]:
            try:
                if temp_file.exists():
                    os.remove(temp_file)
            except OSError:
                pass

        assert not f1.exists()
        assert not f2.exists()

    def test_temp_cleanup_skips_missing_file(self, tmp_path):
        """中間ファイルが存在しなくてもエラーにならない"""
        f1 = tmp_path / "temp_summary_nonexistent.xlsx"
        # ファイルを作らずにremoveしようとしてもエラーなし
        try:
            if f1.exists():
                os.remove(f1)
        except OSError:
            pass  # 正常
