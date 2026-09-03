"""「新しいファイルに対応」ウィザードのロジック層（GUIから切り離した純関数群）。

仕様書の桁位置の表を貼り付け → 設定Excel（parse_sheet_rules が読める横並び形式）を生成する。
貼り付けテキストの1行 = 「項目名 <区切り> 開始位置 <区切り> 文字数」。区切りはタブ優先、
無ければカンマ、それも無ければ空白。開始位置・文字数は設定Excelと同じく1始まりの整数。
"""
import pandas as pd

from src.utils.fixed_format import (
    REC_TYPE_DATA,
    REC_TYPE_END,
    REC_TYPE_HEADER,
    REC_TYPE_TRAILER,
    validate_config_rules,
)

# レコード種別コード → シート名（設定Excelのシート名は parse_sheet_rules の判定に使われる）
REC_TYPE_SHEETS = [
    ("D", REC_TYPE_DATA),
    ("H", REC_TYPE_HEADER),
    ("T", REC_TYPE_TRAILER),
    ("E", REC_TYPE_END),
]


def _split_row(line):
    if "\t" in line:
        return line.split("\t")
    if "," in line:
        return line.split(",")
    return line.split()


def parse_field_spec(text):
    """貼り付けテキストを [{"name", "start", "length"}, ...] にする（start/length は1始まり）。

    空行と「#」で始まる行は無視する。戻り値は (fields, errors)。
    errors は "N行目: ..." 形式のメッセージ列（1件でもあれば設定生成はしない想定）。
    """
    fields = []
    errors = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        parts = [p.strip() for p in _split_row(line) if p.strip()]
        if len(parts) < 3:
            errors.append(f"{lineno}行目: 「項目名 開始位置 文字数」の3つが必要です（{line}）")
            continue

        name, start_s, length_s = parts[0], parts[1], parts[2]
        try:
            start = int(start_s)
            length = int(length_s)
        except ValueError:
            errors.append(f"{lineno}行目: 開始位置・文字数は整数で指定してください（{line}）")
            continue

        fields.append({"name": name, "start": start, "length": length})

    if not fields and not errors:
        errors.append("桁位置の定義が空です")
    return fields, errors


def sheet_df(fields):
    """フィールド定義（1始まり）から parse_sheet_rules が読める横並びシートDataFrameを作る"""
    columns = ["区分"] + [f["name"] for f in fields]
    start_row = ["開始位置"] + [f["start"] for f in fields]
    length_row = ["文字数"] + [f["length"] for f in fields]
    return pd.DataFrame([start_row, length_row], columns=columns)


def build_config_excel(path, fields_by_type):
    """fields_by_type: {"D": [fields], "H": [...], ...}（1始まり）を設定Excelとして書き出す。

    フィールドが空のレコード種別はシートを作らない。「データ」は必須。
    """
    if not fields_by_type.get("D"):
        raise ValueError("「データ」レコードの桁位置定義は必須です")

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for key, sheet_name in REC_TYPE_SHEETS:
            fields = fields_by_type.get(key)
            if not fields:
                continue
            sheet_df(fields).to_excel(writer, sheet_name=sheet_name, index=False)


def validation_warnings(fields_by_type):
    """プレビュー用: 1始まりの fields_by_type を validate_config_rules（0始まり前提）にかける。"""
    rules = {
        key: [
            {"name": f["name"], "start": f["start"] - 1, "length": f["length"]}
            for f in (fields_by_type.get(key) or [])
        ]
        for key, _ in REC_TYPE_SHEETS
    }
    return validate_config_rules(rules)
