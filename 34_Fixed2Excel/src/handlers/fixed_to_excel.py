import os

import pandas as pd

from src.utils.excel_style import style_output_sheet
from src.utils.fixed_format import (
    REC_TYPE_DATA,
    REC_TYPE_HEADER,
    REC_TYPE_LABELS,
    REC_TYPE_TRAILER,
    load_config_rules,
    match_config,
)


def _flatten_field_rules(config_rules):
    """D/H/T のルールを項目名 -> [(レコード種別ラベル, rule), ...] の辞書にまとめる（列コメント用）

    同じ項目名がヘッダー/データ/トレーラーで別々の開始位置・文字数を持つことがあるため、
    1つの辞書に単純上書きすると片方の定義が消えて誤ったコメントになる。リストで両方保持する。
    """
    grouped = {}
    for rec_key, rules in config_rules.items():
        label = REC_TYPE_LABELS.get(rec_key, rec_key)
        for rule in rules or []:
            grouped.setdefault(rule["name"], []).append((label, rule))
    return grouped


def process_file(txt_file_path, config_rules, encoding, record_type_codes):
    """1つの固定長テキストファイルを解析してDataFrameに変換する"""
    parsed_rows = []
    with open(txt_file_path, "rb") as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip(b"\r\n")
            if not line:
                continue

            rec_code = line[0:1].decode(encoding, errors="ignore")

            if rec_code in record_type_codes["header"] and config_rules["H"]:
                rules = config_rules["H"]
                rec_type = REC_TYPE_HEADER
            elif rec_code in record_type_codes["trailer"] and config_rules["T"]:
                rules = config_rules["T"]
                rec_type = REC_TYPE_TRAILER
            else:
                rules = config_rules["D"]
                rec_type = REC_TYPE_DATA

            if not rules:
                continue

            row_data = {"行番号": line_num, "区分": rec_code, "レコード種別": rec_type}
            for rule in rules:
                start = rule["start"]
                end = start + rule["length"]
                raw_bytes = line[start:end]
                row_data[rule["name"]] = raw_bytes.decode(encoding, errors="replace").strip()

            parsed_rows.append(row_data)

    return pd.DataFrame(parsed_rows)


def convert_all(ctx):
    """input内の固定長テキストを全て解析し、outputへExcelとして出力する"""
    dirs = ctx.dirs
    configs_dir = dirs["configs"]
    input_dir = dirs["input"]
    output_dir = dirs["output"]
    logger = ctx.logger

    if not os.path.exists(ctx.mapping_csv):
        logger.warning("mapping.csv が見つかりません。先に mapping.csv 更新を実行してください。")
        return

    df_map = pd.read_csv(ctx.mapping_csv, encoding=ctx.encoding)
    os.makedirs(output_dir, exist_ok=True)

    input_files = [f for f in os.listdir(input_dir) if not f.startswith(".")]

    for txt_name in input_files:
        txt_path = os.path.join(input_dir, txt_name)

        matched_config_name = match_config(txt_name, df_map, ctx.mapping_columns)
        if not matched_config_name:
            logger.info(f"スキップ: '{txt_name}' (mapping.csv に合致するキーワードがありません)")
            continue

        config_path = os.path.join(configs_dir, matched_config_name)
        if not os.path.exists(config_path):
            logger.error(f"設定ファイル '{matched_config_name}' が configs/ に存在しません。")
            continue

        logger.info(f"解析中: '{txt_name}' -> 適用Config: [{matched_config_name}]")

        config_rules = load_config_rules(config_path)
        df_result = process_file(txt_path, config_rules, ctx.encoding, ctx.record_type_codes)

        out_name = f"解析結果_{os.path.splitext(txt_name)[0]}.xlsx"
        out_path = os.path.join(output_dir, out_name)
        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            df_result.to_excel(writer, index=False, sheet_name="Sheet1")
            style_output_sheet(writer.sheets["Sheet1"], df_result, _flatten_field_rules(config_rules))
        logger.info(f"出力完了: {out_path}")
