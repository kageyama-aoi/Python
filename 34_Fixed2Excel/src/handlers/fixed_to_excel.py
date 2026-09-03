import os

import pandas as pd

from src.utils.excel_style import insert_group_separators, style_output_sheet
from src.utils.fixed_format import (
    REC_TYPE_DATA,
    REC_TYPE_END,
    REC_TYPE_HEADER,
    REC_TYPE_LABELS,
    REC_TYPE_TRAILER,
    analysis_excel_name,
    build_field_columns,
    load_config_rules,
    read_mapping_csv,
    resolve_config_path,
)
from src.utils.log_tags import log_end, log_start


def _flatten_field_rules(config_rules):
    """出力Excelのカラム名 -> (レコード種別ラベル, rule) の辞書にまとめる（列コメント・グルーピング用）

    build_field_columnsで種別ごと・出現順に一意化したカラム名をそのままキーにするため、
    カラム名は必ず1つの定義に対応する。
    """
    field_columns = build_field_columns(config_rules)
    flattened = {}
    for rec_key, entries in field_columns.items():
        label = REC_TYPE_LABELS.get(rec_key, rec_key)
        for entry in entries:
            flattened[entry["column"]] = (label, entry["rule"])
    return flattened


def _expected_record_length(rules):
    """レコード種別のルール群から想定レコード長（末尾フィールドの終端位置）を返す"""
    return max((r["start"] + r["length"] for r in rules), default=0)


def process_file(txt_file_path, config_rules, encoding, record_type_codes, *, diagnostics=None):
    """1つの固定長テキストファイルを解析してDataFrameに変換する

    diagnostics（list）を渡すと、行の実バイト長が設定の想定レコード長と食い違う行を
    {"line", "rec_type", "expected", "actual"} の dict で追記する。
    """
    field_columns = build_field_columns(config_rules)
    parsed_rows = []
    with open(txt_file_path, "rb") as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip(b"\r\n")
            if not line:
                continue

            rec_code = line[0:1].decode(encoding, errors="ignore")

            if rec_code in record_type_codes["header"] and config_rules["H"]:
                rec_key, rec_type = "H", REC_TYPE_HEADER
            elif rec_code in record_type_codes["trailer"] and config_rules["T"]:
                rec_key, rec_type = "T", REC_TYPE_TRAILER
            elif rec_code in record_type_codes.get("end", []) and config_rules.get("E"):
                rec_key, rec_type = "E", REC_TYPE_END
            else:
                rec_key, rec_type = "D", REC_TYPE_DATA

            entries = field_columns.get(rec_key)
            if not entries:
                continue

            if diagnostics is not None:
                expected = _expected_record_length([e["rule"] for e in entries])
                if expected and len(line) != expected:
                    diagnostics.append({
                        "line": line_num, "rec_type": rec_type,
                        "expected": expected, "actual": len(line),
                    })

            row_data = {"行番号": line_num, "区分": rec_code, "レコード種別": rec_type}
            for entry in entries:
                rule = entry["rule"]
                start = rule["start"]
                end = start + rule["length"]
                raw_bytes = line[start:end]
                row_data[entry["column"]] = raw_bytes.decode(encoding, errors="replace").strip()

            parsed_rows.append(row_data)

    return pd.DataFrame(parsed_rows)


def convert_all(ctx):
    """input内の固定長テキストを全て解析し、outputへExcelとして出力する"""
    dirs = ctx.dirs
    configs_dir = dirs["configs"]
    input_dir = dirs["input"]
    output_dir = dirs["output"]
    logger = ctx.logger

    log_start(logger, "固定長→Excel変換開始")

    if not os.path.exists(ctx.mapping_csv):
        logger.warning("mapping.csv未検出（先にmapping.csv更新を実行）")
        log_end(logger, "固定長→Excel変換完了")
        return

    df_map = read_mapping_csv(ctx.mapping_csv, ctx.encoding)
    os.makedirs(output_dir, exist_ok=True)

    input_files = [f for f in os.listdir(input_dir) if not f.startswith(".")]

    for txt_name in input_files:
        txt_path = os.path.join(input_dir, txt_name)

        config_path = resolve_config_path(txt_name, df_map, ctx.mapping_columns, configs_dir, logger)
        if not config_path:
            continue

        logger.info(f"解析: {txt_name} → {os.path.basename(config_path)}")

        config_rules = load_config_rules(config_path, logger=logger)
        length_diag = []
        df_result = process_file(
            txt_path, config_rules, ctx.encoding, ctx.record_type_codes, diagnostics=length_diag
        )
        for d in length_diag:
            logger.warning(
                f"{txt_name} 行{d['line']}（{d['rec_type']}）: レコード長 {d['actual']}バイト "
                f"（設定の想定は {d['expected']}バイト）"
            )
        if length_diag:
            logger.warning(f"{txt_name}: レコード長不一致 {len(length_diag)}件（設定Excelの桁定義を確認）")
        field_rules = _flatten_field_rules(config_rules)
        df_display = insert_group_separators(df_result, field_rules)

        out_name = analysis_excel_name(txt_name)
        out_path = os.path.join(output_dir, out_name)
        try:
            with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                df_display.to_excel(writer, index=False, sheet_name="Sheet1")
                style_output_sheet(writer.sheets["Sheet1"], df_display, field_rules)
        except PermissionError:
            logger.error(f"書き込み不可（Excelで開いている可能性）: {out_path}")
            continue
        logger.info(f"出力: {out_path}")

    log_end(logger, "固定長→Excel変換完了")
