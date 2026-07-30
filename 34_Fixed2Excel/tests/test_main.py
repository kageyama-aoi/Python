import logging
import os
import sys

import openpyxl
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app_context import AppContext
from src.handlers import excel_to_fixed as excel_to_fixed_module
from src.handlers import fixed_to_excel as fixed_to_excel_module
from src.handlers.excel_to_fixed import build_fixed_line, pad_value_to_bytes, restore_all
from src.handlers.fixed_to_excel import _flatten_field_rules, convert_all, process_file
from src.handlers.mapping_handler import build_or_update_mapping
from src.utils.excel_style import _comment_text, _group_row_ranges, style_output_sheet
from src.utils.fixed_format import match_config

ENCODING = "cp932"
RECORD_TYPE_CODES = {"header": ["1"], "trailer": ["8", "9"]}

logger = logging.getLogger("test")


def _make_ctx(dirs, mapping_csv, mapping_columns, **overrides):
    """テスト用にAppContextを組み立てる（record_type_codes等は既定値を使い回す）"""
    fields = {
        "app_name": "test",
        "encoding": ENCODING,
        "dirs": dirs,
        "mapping_csv": str(mapping_csv),
        "mapping_columns": mapping_columns,
        "record_type_codes": RECORD_TYPE_CODES,
        "logger": logger,
    }
    fields.update(overrides)
    return AppContext(**fields)


def _write_config_excel(path):
    data_sheet = pd.DataFrame([
        ["開始位置", 1, 5],
        ["文字数", 1, 4],
    ], columns=["区分", "会員番号", "名前"])

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        data_sheet.to_excel(writer, sheet_name="データ", index=False)


# ---- process_file ----

def test_process_file_parses_data_rows(tmp_path):
    config_path = tmp_path / "config.xlsx"
    _write_config_excel(config_path)

    txt_path = tmp_path / "sample.txt"
    with open(txt_path, "wb") as f:
        f.write("2XXXABCD".encode(ENCODING) + b"\r\n")

    from src.utils.fixed_format import load_config_rules
    rules = load_config_rules(config_path)

    df = process_file(txt_path, rules, ENCODING, RECORD_TYPE_CODES)

    assert list(df["会員番号"]) == ["2"]
    assert list(df["名前"]) == ["ABCD"]
    assert list(df["レコード種別"]) == ["データ"]


def test_process_file_skips_blank_lines(tmp_path):
    config_path = tmp_path / "config.xlsx"
    _write_config_excel(config_path)

    txt_path = tmp_path / "sample.txt"
    with open(txt_path, "wb") as f:
        f.write(b"\r\n")
        f.write("2ABCDテスト".encode(ENCODING) + b"\r\n")

    from src.utils.fixed_format import load_config_rules
    rules = load_config_rules(config_path)

    df = process_file(txt_path, rules, ENCODING, RECORD_TYPE_CODES)
    assert len(df) == 1


# ---- pad_value_to_bytes / build_fixed_line ----

def test_pad_value_to_bytes_right_justifies_digits():
    assert pad_value_to_bytes("12", 5, ENCODING) == b"   12"


def test_pad_value_to_bytes_left_justifies_text():
    assert pad_value_to_bytes("AB", 5, ENCODING) == b"AB   "


def test_pad_value_to_bytes_truncates_when_too_long():
    assert pad_value_to_bytes("ABCDEF", 3, ENCODING) == b"ABC"


def test_build_fixed_line_places_fields_at_start_positions():
    rules = [
        {"name": "会員番号", "start": 0, "length": 1},
        {"name": "名前", "start": 1, "length": 4},
    ]
    row = {"会員番号": "2", "名前": "AB"}
    line = build_fixed_line(row, rules, ENCODING)
    assert line == b"2AB  "


# ---- match_config ----

def test_match_config_finds_matching_keyword():
    columns = {"keyword": "kw", "config_name": "cfg"}
    df_map = pd.DataFrame([{"kw": "KAIIN", "cfg": "kaiin.xlsx"}])
    assert match_config("KAIIN_SAMPLE.txt", df_map, columns) == "kaiin.xlsx"


def test_match_config_returns_none_when_no_match():
    columns = {"keyword": "kw", "config_name": "cfg"}
    df_map = pd.DataFrame([{"kw": "OTHER", "cfg": "other.xlsx"}])
    assert match_config("KAIIN_SAMPLE.txt", df_map, columns) is None


# ---- build_or_update_mapping ----

def test_build_or_update_mapping_appends_new_input_file(tmp_path):
    configs_dir = tmp_path / "configs"
    input_dir = tmp_path / "input"
    configs_dir.mkdir()
    input_dir.mkdir()
    (configs_dir / "sample.xlsx").write_bytes(b"")
    (input_dir / "KAIIN_SAMPLE.txt").write_bytes(b"")

    mapping_csv = tmp_path / "mapping.csv"
    columns = {"keyword": "kw", "config_name": "cfg", "note": "note"}

    ctx = _make_ctx({"configs": str(configs_dir), "input": str(input_dir)}, mapping_csv, columns)
    added = build_or_update_mapping(ctx)

    assert added == 1
    df_map = pd.read_csv(mapping_csv, encoding=ENCODING)
    assert df_map.iloc[0]["kw"] == "KAIIN_SAMPLE"
    assert df_map.iloc[0]["cfg"] == "sample.xlsx"


# 過去に見つかったバグ: mapping.csv を data/configs/ 配下に置く運用に変えた際、
# 設定ファイル一覧のスキャンが拡張子(.xlsx/.csv)だけで判定していたため、mapping.csv
# 自身を「設定ファイル」として拾ってしまい、新規input行の既定Configにmapping.csvが
# 提案されることがあった。

def test_build_or_update_mapping_excludes_mapping_csv_itself_when_colocated(tmp_path):
    configs_dir = tmp_path / "configs"
    input_dir = tmp_path / "input"
    configs_dir.mkdir()
    input_dir.mkdir()
    (configs_dir / "sample.xlsx").write_bytes(b"")
    (input_dir / "KAIIN_SAMPLE.txt").write_bytes(b"")

    mapping_csv = configs_dir / "mapping.csv"  # configs/ 直下に配置
    columns = {"keyword": "kw", "config_name": "cfg", "note": "note"}

    ctx = _make_ctx({"configs": str(configs_dir), "input": str(input_dir)}, mapping_csv, columns)
    build_or_update_mapping(ctx)

    df_map = pd.read_csv(mapping_csv, encoding=ENCODING)
    assert df_map.iloc[0]["cfg"] == "sample.xlsx"  # mapping.csv自身が既定Configになっていない


def test_build_or_update_mapping_skips_already_registered(tmp_path):
    configs_dir = tmp_path / "configs"
    input_dir = tmp_path / "input"
    configs_dir.mkdir()
    input_dir.mkdir()
    (input_dir / "KAIIN_SAMPLE.txt").write_bytes(b"")

    mapping_csv = tmp_path / "mapping.csv"
    columns = {"keyword": "kw", "config_name": "cfg", "note": "note"}
    pd.DataFrame([{"kw": "KAIIN_SAMPLE", "cfg": "x.xlsx", "note": ""}]).to_csv(
        mapping_csv, index=False, encoding=ENCODING
    )

    ctx = _make_ctx({"configs": str(configs_dir), "input": str(input_dir)}, mapping_csv, columns)
    added = build_or_update_mapping(ctx)

    assert added == 0


# ---- 固定長 -> Excel -> 固定長 の往復変換（回帰テスト） ----
# 過去に見つかったバグ: (1) 16桁の数字文字列がpd.read_excelの型推論でfloatに
# 化けて桁が欠落する、(2) 先頭1バイトのレコード種別コードが復元時に失われる。

def test_roundtrip_preserves_record_code_and_long_numeric_field(tmp_path):
    configs_dir = tmp_path / "configs"
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    recreated_dir = tmp_path / "recreated"
    for d in (configs_dir, input_dir, output_dir, recreated_dir):
        d.mkdir()

    header_sheet = pd.DataFrame([["開始位置", 2], ["文字数", 8]], columns=["区分", "作成年月日"])
    data_sheet = pd.DataFrame([["開始位置", 2], ["文字数", 16]], columns=["区分", "会員番号"])
    config_path = configs_dir / "config.xlsx"
    with pd.ExcelWriter(config_path, engine="openpyxl") as writer:
        data_sheet.to_excel(writer, sheet_name="データ", index=False)
        header_sheet.to_excel(writer, sheet_name="ヘッダー", index=False)

    h_line = "1" + "20260730"
    d_line = "2" + "1000000000000001"  # 16桁の数字文字列(会員番号)
    input_path = input_dir / "SAMPLE.txt"
    with open(input_path, "wb") as f:
        for line in [h_line, d_line]:
            f.write(line.encode(ENCODING) + b"\r\n")

    mapping_csv = tmp_path / "mapping.csv"
    columns = {"keyword": "判定キーワード(input側)", "config_name": "設定ファイル名(configs内)"}
    pd.DataFrame([{
        "判定キーワード(input側)": "SAMPLE",
        "設定ファイル名(configs内)": "config.xlsx",
    }]).to_csv(mapping_csv, index=False, encoding=ENCODING)

    dirs = {
        "configs": str(configs_dir), "input": str(input_dir),
        "output": str(output_dir), "recreated": str(recreated_dir),
    }
    ctx = _make_ctx(dirs, mapping_csv, columns)
    convert_all(ctx)
    restore_all(ctx)

    restored_path = recreated_dir / "RESTORED_SAMPLE.txt"
    with open(restored_path, "rb") as f:
        restored_lines = [l.rstrip(b"\r\n").decode(ENCODING) for l in f if l.strip()]

    assert restored_lines == [h_line, d_line]


# ---- 出力Excelの項目コメント（同名項目がレコード種別をまたぐケース） ----
# 過去に見つかったバグ: 「予備」のように同じ列名がヘッダー/データ/トレーラーで別々の
# 開始位置・文字数を持つとき、素朴に辞書へ詰めると後勝ちで上書きされ、片方の情報が消えて
# 誤ったコメントになっていた。

def test_flatten_field_rules_keeps_all_definitions_for_colliding_name():
    config_rules = {
        "D": [{"name": "予備", "start": 66, "length": 4}],
        "H": [{"name": "予備", "start": 49, "length": 20}],
        "T": None,
    }
    grouped = _flatten_field_rules(config_rules)
    assert grouped["予備"] == [
        ("データ", config_rules["D"][0]),
        ("ヘッダー", config_rules["H"][0]),
    ]


def test_comment_text_lists_each_record_type_when_ambiguous():
    entries = [
        ("データ", {"start": 66, "length": 4}),
        ("ヘッダー", {"start": 49, "length": 20}),
    ]
    text = _comment_text(entries)
    assert "データ: 開始位置:67 文字数:4" in text
    assert "ヘッダー: 開始位置:50 文字数:20" in text


def test_comment_text_omits_label_when_unambiguous():
    entries = [("データ", {"start": 0, "length": 1})]
    text = _comment_text(entries)
    assert text == "開始位置:1 文字数:1"


# ---- 出力先ファイルが他アプリ（Excel等）で開いている場合のエラーハンドリング ----
# 実際に開発中、出力Excelをexcelで開いたまま再変換してPermissionErrorでクラッシュした。
# 1ファイルの書き込み/読み込み失敗で処理全体を止めず、他のファイルは続行できるようにする。

def _write_simple_config(config_path):
    data_sheet = pd.DataFrame([["開始位置", 1], ["文字数", 1]], columns=["区分", "値"])
    with pd.ExcelWriter(config_path, engine="openpyxl") as writer:
        data_sheet.to_excel(writer, sheet_name="データ", index=False)


def test_convert_all_skips_locked_output_and_continues_other_files(tmp_path, monkeypatch):
    configs_dir = tmp_path / "configs"
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    configs_dir.mkdir()
    input_dir.mkdir()

    _write_simple_config(configs_dir / "config.xlsx")
    for name in ("LOCKED.txt", "OK.txt"):
        with open(input_dir / name, "wb") as f:
            f.write(b"2A\r\n")

    mapping_csv = tmp_path / "mapping.csv"
    columns = {"keyword": "kw", "config_name": "cfg"}
    pd.DataFrame([
        {"kw": "LOCKED", "cfg": "config.xlsx"},
        {"kw": "OK", "cfg": "config.xlsx"},
    ]).to_csv(mapping_csv, index=False, encoding=ENCODING)

    dirs = {
        "configs": str(configs_dir), "input": str(input_dir),
        "output": str(output_dir), "recreated": str(tmp_path / "recreated"),
    }
    ctx = _make_ctx(dirs, mapping_csv, columns)

    real_excel_writer = pd.ExcelWriter

    def flaky_excel_writer(path, *args, **kwargs):
        if "LOCKED" in str(path):
            raise PermissionError("mock: file is open in Excel")
        return real_excel_writer(path, *args, **kwargs)

    monkeypatch.setattr(fixed_to_excel_module.pd, "ExcelWriter", flaky_excel_writer)

    convert_all(ctx)  # 例外を送出せず完走すること

    assert not (output_dir / "解析結果_LOCKED.xlsx").exists()
    assert (output_dir / "解析結果_OK.xlsx").exists()


def test_restore_all_skips_locked_input_and_continues_other_files(tmp_path, monkeypatch):
    configs_dir = tmp_path / "configs"
    output_dir = tmp_path / "output"
    recreated_dir = tmp_path / "recreated"
    configs_dir.mkdir()
    output_dir.mkdir()

    _write_simple_config(configs_dir / "config.xlsx")
    for name in ("解析結果_LOCKED.xlsx", "解析結果_OK.xlsx"):
        pd.DataFrame([{"レコード種別": "データ", "区分": "2", "値": "A"}]).to_excel(
            output_dir / name, index=False
        )

    mapping_csv = tmp_path / "mapping.csv"
    columns = {"keyword": "kw", "config_name": "cfg"}
    pd.DataFrame([
        {"kw": "LOCKED", "cfg": "config.xlsx"},
        {"kw": "OK", "cfg": "config.xlsx"},
    ]).to_csv(mapping_csv, index=False, encoding=ENCODING)

    dirs = {
        "configs": str(configs_dir), "input": str(tmp_path / "input"),
        "output": str(output_dir), "recreated": str(recreated_dir),
    }
    ctx = _make_ctx(dirs, mapping_csv, columns)

    real_read_excel = pd.read_excel

    def flaky_read_excel(path, *args, **kwargs):
        if "LOCKED" in str(path):
            raise PermissionError("mock: file is open in Excel")
        return real_read_excel(path, *args, **kwargs)

    monkeypatch.setattr(excel_to_fixed_module.pd, "read_excel", flaky_read_excel)

    restore_all(ctx)  # 例外を送出せず完走すること

    assert not (recreated_dir / "RESTORED_LOCKED.txt").exists()
    assert (recreated_dir / "RESTORED_OK.txt").exists()


# ---- 出力Excelの行グループ化・罫線 ----

def test_group_row_ranges_groups_contiguous_runs_of_length_2_or_more():
    rec_types = ["ヘッダー", "データ", "データ", "データ", "トレーラー"]
    assert _group_row_ranges(rec_types) == [(3, 5)]


def test_group_row_ranges_skips_single_row_runs():
    rec_types = ["ヘッダー", "データ", "トレーラー"]
    assert _group_row_ranges(rec_types) == []


def test_group_row_ranges_handles_multiple_groups():
    rec_types = ["データ", "データ", "ヘッダー", "データ", "データ", "データ"]
    assert _group_row_ranges(rec_types) == [(2, 3), (5, 7)]


def test_style_output_sheet_applies_border_and_groups_data_rows(tmp_path):
    df = pd.DataFrame([
        {"行番号": 1, "区分": "1", "レコード種別": "ヘッダー", "値": "H"},
        {"行番号": 2, "区分": "2", "レコード種別": "データ", "値": "D1"},
        {"行番号": 3, "区分": "2", "レコード種別": "データ", "値": "D2"},
        {"行番号": 4, "区分": "9", "レコード種別": "トレーラー", "値": "T"},
    ])
    out_path = tmp_path / "styled.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
        style_output_sheet(writer.sheets["Sheet1"], df, {})

    wb = openpyxl.load_workbook(out_path)
    ws = wb.active

    assert ws.cell(row=1, column=1).border.left.style == "thin"
    assert ws.cell(row=3, column=1).border.right.style == "thin"

    assert ws.row_dimensions[2].outlineLevel == 0  # ヘッダー単独行
    assert ws.row_dimensions[3].outlineLevel == 1  # データ1行目
    assert ws.row_dimensions[4].outlineLevel == 1  # データ2行目
    assert ws.row_dimensions[5].outlineLevel == 0  # トレーラー単独行
