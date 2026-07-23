import json
import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_drive_structure import (
    BASE_DIR,
    ConfigError,
    ConfigManager,
    DirectoryScanner,
    ScannedItem,
    create_dataframe_with_fullpath,
    format_size,
    manage_old_output_files,
)


# ---- format_size ----

def test_format_size_none():
    assert format_size(None) == ''


def test_format_size_bytes():
    assert format_size(0) == '0 B'
    assert format_size(500) == '500 B'


def test_format_size_kb():
    assert format_size(1536) == '1.5 KB'


def test_format_size_mb():
    assert format_size(2 * 1024 * 1024) == '2.0 MB'


def test_format_size_gb():
    assert format_size(3 * 1024 ** 3) == '3.0 GB'


# ---- ConfigManager ----

def _write_config(tmp_path, data):
    p = tmp_path / "config.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_config_manager_missing_file(tmp_path):
    with pytest.raises(ConfigError):
        ConfigManager(str(tmp_path / "no_such.json"))


def test_config_manager_invalid_json(tmp_path):
    p = tmp_path / "config.json"
    p.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ConfigError):
        ConfigManager(str(p))


def test_config_manager_missing_required_key(tmp_path):
    path = _write_config(tmp_path, {"root_dir": "C:/tmp"})
    with pytest.raises(ConfigError):
        ConfigManager(path)


def test_config_manager_root_dir_wrong_type(tmp_path):
    path = _write_config(tmp_path, {
        "root_dir": 123,
        "output_base_dir": "output",
        "output_filename": "out.xlsx",
    })
    with pytest.raises(ConfigError):
        ConfigManager(path)


def test_config_manager_defaults(tmp_path):
    path = _write_config(tmp_path, {
        "root_dir": "C:/tmp",
        "output_base_dir": "output",
        "output_filename": "out.xlsx",
    })
    cm = ConfigManager(path)
    assert cm.get_excluded_extensions() == []
    assert cm.get_excluded_folder_names() == []


def test_config_manager_excluded_lists_lowercased(tmp_path):
    path = _write_config(tmp_path, {
        "root_dir": "C:/tmp",
        "output_base_dir": "output",
        "output_filename": "out.xlsx",
        "excluded_extensions": [".LOG", ".Tmp"],
        "excluded_folder_names": ["OLD", "Backup"],
    })
    cm = ConfigManager(path)
    assert cm.get_excluded_extensions() == ['.log', '.tmp']
    assert cm.get_excluded_folder_names() == ['old', 'backup']


def test_config_manager_output_base_dir_relative_resolves_under_base_dir(tmp_path):
    path = _write_config(tmp_path, {
        "root_dir": "C:/tmp",
        "output_base_dir": "some_output",
        "output_filename": "out.xlsx",
    })
    cm = ConfigManager(path)
    assert cm.output_base_dir == os.path.join(BASE_DIR, "some_output")


def test_config_manager_output_base_dir_absolute_kept_as_is(tmp_path):
    abs_dir = str(tmp_path / "abs_output")
    path = _write_config(tmp_path, {
        "root_dir": "C:/tmp",
        "output_base_dir": abs_dir,
        "output_filename": "out.xlsx",
    })
    cm = ConfigManager(path)
    assert cm.output_base_dir == abs_dir


def test_config_manager_save_root_dir_persists(tmp_path):
    path = _write_config(tmp_path, {
        "root_dir": "C:/tmp",
        "output_base_dir": "output",
        "output_filename": "out.xlsx",
    })
    cm = ConfigManager(path)
    cm.save_root_dir("D:/new_dir")
    assert cm.root_dir == "D:/new_dir"

    reloaded = json.loads(open(path, encoding="utf-8").read())
    assert reloaded["root_dir"] == "D:/new_dir"


# ---- DirectoryScanner ----

def _build_sample_tree(tmp_path):
    root = tmp_path / "root"
    (root / "sub").mkdir(parents=True)
    (root / "OLD").mkdir()
    (root / "OLD" / "hidden.txt").write_text("secret", encoding="utf-8")
    (root / "a.txt").write_text("hello", encoding="utf-8")  # 5 bytes
    (root / "b.log").write_text("should be excluded", encoding="utf-8")
    (root / "sub" / "c.txt").write_text("world!", encoding="utf-8")  # 6 bytes
    return root


def test_scan_nonexistent_root_returns_empty(tmp_path):
    scanner = DirectoryScanner(str(tmp_path / "does_not_exist"))
    assert scanner.scan() == []


def test_scan_collects_files_and_folders(tmp_path):
    root = _build_sample_tree(tmp_path)
    scanner = DirectoryScanner(
        str(root),
        excluded_extensions=['.log'],
        excluded_folder_names=['old'],
    )
    items = scanner.scan()
    names = {item.name for item in items}

    assert 'a.txt' in names
    assert 'sub' in names
    assert 'c.txt' in names
    # 除外対象は含まれない
    assert 'b.log' not in names
    assert 'OLD' not in names
    assert 'hidden.txt' not in names


def test_scan_file_size_bytes_populated(tmp_path):
    root = _build_sample_tree(tmp_path)
    scanner = DirectoryScanner(str(root), excluded_extensions=['.log'], excluded_folder_names=['old'])
    items = {item.name: item for item in scanner.scan()}

    assert items['a.txt'].size_bytes == 5
    assert items['a.txt'].item_type == 'file'


def test_scan_folder_size_is_none(tmp_path):
    root = _build_sample_tree(tmp_path)
    scanner = DirectoryScanner(str(root), excluded_extensions=['.log'], excluded_folder_names=['old'])
    items = {item.name: item for item in scanner.scan()}

    assert items['sub'].item_type == 'folder'
    assert items['sub'].size_bytes is None


def test_scan_levels_reflect_depth(tmp_path):
    root = _build_sample_tree(tmp_path)
    scanner = DirectoryScanner(str(root), excluded_extensions=['.log'], excluded_folder_names=['old'])
    items = {item.name: item for item in scanner.scan()}

    assert items['a.txt'].levels == []
    assert items['c.txt'].levels == ['sub']


# ---- create_dataframe_with_fullpath ----

def test_create_dataframe_empty_input():
    df = create_dataframe_with_fullpath([])
    assert df.empty


def test_create_dataframe_columns_and_values():
    # 'sub' はルート直下(深さ1)のフォルダ、'c.txt' はその配下(深さ2)のファイル。
    # 深さの異なる階層は「階段状」に列へ配置される仕様のため、'sub' の名前は
    # Level1列に入り、アイテム名列は空になる（アイテム名列は最大深度の行のみ埋まる）。
    items = [
        ScannedItem(r"C:\root\sub", r"C:\root", [], "sub", "folder", None),
        ScannedItem(r"C:\root\sub\c.txt", r"C:\root\sub", ["sub"], "c.txt", "file", 6),
    ]
    df = create_dataframe_with_fullpath(items)

    assert list(df.columns) == [
        '_item_self_path', 'タイプ', 'フルパス', 'サイズ(バイト)', 'サイズ', 'Level1', 'アイテム名'
    ]
    df = df.set_index('_item_self_path')

    folder_row = df.loc[r"C:\root\sub"]
    assert folder_row['タイプ'] == 'folder'
    assert folder_row['フルパス'] == r"C:\root"
    assert folder_row['サイズ(バイト)'] == ''
    assert folder_row['サイズ'] == ''
    assert folder_row['Level1'] == 'sub'
    assert folder_row['アイテム名'] == ''

    file_row = df.loc[r"C:\root\sub\c.txt"]
    assert file_row['タイプ'] == 'file'
    assert file_row['フルパス'] == ''  # ファイル行は親フルパスを表示しない
    assert file_row['サイズ(バイト)'] == 6
    assert file_row['サイズ'] == format_size(6)
    assert file_row['Level1'] == 'sub'
    assert file_row['アイテム名'] == 'c.txt'


def test_create_dataframe_no_level_columns_when_flat():
    items = [ScannedItem(r"C:\root\a.txt", r"C:\root", [], "a.txt", "file", 5)]
    df = create_dataframe_with_fullpath(items)
    assert 'Level1' not in df.columns
    assert list(df.columns) == [
        '_item_self_path', 'タイプ', 'フルパス', 'サイズ(バイト)', 'サイズ', 'アイテム名'
    ]


# ---- manage_old_output_files ----

def test_manage_old_output_files_deletes_on_confirm(tmp_path, monkeypatch):
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    old_file = out_dir / "drive_structure_20250101_000000.xlsx"
    old_file.write_text("dummy", encoding="utf-8")
    current_file = "drive_structure_20260101_000000.xlsx"

    monkeypatch.setattr('builtins.input', lambda _: 'y')
    manage_old_output_files(str(out_dir), "drive_structure.xlsx", current_file)

    assert not old_file.exists()


def test_manage_old_output_files_keeps_on_decline(tmp_path, monkeypatch):
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    old_file = out_dir / "drive_structure_20250101_000000.xlsx"
    old_file.write_text("dummy", encoding="utf-8")
    current_file = "drive_structure_20260101_000000.xlsx"

    monkeypatch.setattr('builtins.input', lambda _: 'n')
    manage_old_output_files(str(out_dir), "drive_structure.xlsx", current_file)

    assert old_file.exists()


def test_manage_old_output_files_ignores_non_matching_names(tmp_path, monkeypatch):
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    unrelated = out_dir / "notes.txt"
    unrelated.write_text("keep me", encoding="utf-8")

    monkeypatch.setattr('builtins.input', lambda _: (_ for _ in ()).throw(AssertionError("input should not be called")))
    manage_old_output_files(str(out_dir), "drive_structure.xlsx", "drive_structure_20260101_000000.xlsx")

    assert unrelated.exists()
