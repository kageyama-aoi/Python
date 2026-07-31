import os

import pandas as pd

from src.utils.fixed_format import (
    REC_TYPE_DATA,
    REC_TYPE_LABELS,
    build_field_columns,
    load_config_rules,
    resolve_config_path,
)
from src.utils.log_tags import log_end, log_start


def pad_value_to_bytes(val, length, encoding):
    """
    データ型に応じた自動パディング処理
    - 数値・数字のみ: 右寄せスペース埋め
    - 文字列: 左寄せスペース埋め
    """
    if pd.isna(val) or val is None:
        val_str = ""
    elif isinstance(val, float) and val.is_integer():
        val_str = str(int(val))
    else:
        val_str = str(val).strip()

    encoded = val_str.encode(encoding, errors="replace")

    if len(encoded) >= length:
        return encoded[:length]

    pad_len = length - len(encoded)
    if isinstance(val, (int, float)) or val_str.isdigit():
        return (b" " * pad_len) + encoded
    return encoded + (b" " * pad_len)


def build_fixed_line(row_data, rules, encoding):
    """Excelの1行から固定長バイト列を作成"""
    if not rules:
        return None

    max_len = max(r["start"] + r["length"] for r in rules)
    line_buf = bytearray(b" " * max_len)

    for rule in rules:
        val = row_data.get(rule["name"], "")
        field_bytes = pad_value_to_bytes(val, rule["length"], encoding)
        line_buf[rule["start"]: rule["start"] + rule["length"]] = field_bytes

    return bytes(line_buf)


def restore_all(ctx):
    """output内の編集済みExcelから固定長テキストを復元し、recreated_inputへ出力する"""
    dirs = ctx.dirs
    configs_dir = dirs["configs"]
    output_dir = dirs["output"]
    recreated_dir = dirs["recreated"]
    encoding = ctx.encoding
    logger = ctx.logger

    log_start(logger, "Excel→固定長復元開始")

    if not os.path.exists(ctx.mapping_csv):
        logger.warning("mapping.csv未検出")
        log_end(logger, "Excel→固定長復元完了")
        return

    os.makedirs(recreated_dir, exist_ok=True)
    df_map = pd.read_csv(ctx.mapping_csv, encoding=encoding)

    output_files = [f for f in os.listdir(output_dir) if f.endswith(".xlsx") and not f.startswith("~$")]
    if not output_files:
        logger.info("復元対象なし（output/ にExcelファイルなし）")
        log_end(logger, "Excel→固定長復元完了")
        return

    for excel_name in output_files:
        excel_path = os.path.join(output_dir, excel_name)

        config_path = resolve_config_path(excel_name, df_map, ctx.mapping_columns, configs_dir, logger)
        if not config_path:
            continue

        logger.info(f"逆変換: {excel_name} → {os.path.basename(config_path)}")

        rules_by_type = load_config_rules(config_path)
        field_columns_by_label = {REC_TYPE_LABELS[k]: v for k, v in build_field_columns(rules_by_type).items()}

        try:
            # dtype=str必須: 既定の型推論だと桁数の多い数字文字列(会員番号等)が
            # float64に変換され、有効桁を超えた分が丸められて値が壊れる。
            # skiprows=[1, 2]: 2/3行目は開始位置・文字数の参考表示(_insert_position_rows)であり
            # 実データではないため、復元対象から除外する。
            df_target = pd.read_excel(excel_path, dtype=str, skiprows=[1, 2])
        except PermissionError:
            logger.error(f"読み込み不可（Excelで開いている可能性）: {excel_path}")
            continue

        output_lines = []
        for _, row in df_target.iterrows():
            rec_type = str(row.get("レコード種別", REC_TYPE_DATA)).strip()
            entries = field_columns_by_label.get(rec_type) or field_columns_by_label[REC_TYPE_DATA]

            # 出力Excel上では同名項目がbuild_field_columnsで一意なカラム名に分けられているため
            # （種別ごと・同種別内の連番）、そのカラム名自体をruleの"name"として使う合成ルールを
            # 組み立て、build_fixed_lineの既存ロジック（name経由の突き合わせ）はそのまま使う。
            synthetic_rules = [
                {"name": e["column"], "start": e["rule"]["start"], "length": e["rule"]["length"]}
                for e in entries
            ]
            translated_row = {e["column"]: row.get(e["column"], "") for e in entries}
            line_bytes = build_fixed_line(translated_row, synthetic_rules, encoding)
            if not line_bytes:
                continue

            # 先頭1バイトのレコード種別コード(区分)はrulesに含まれないため、
            # 解析時に保存した「区分」列の値で明示的に書き戻す。
            rec_code = row.get("区分")
            if not pd.isna(rec_code):
                rec_code = str(rec_code).strip()
                if rec_code:
                    buf = bytearray(line_bytes)
                    buf[0:1] = rec_code.encode(encoding)[:1]
                    line_bytes = bytes(buf)

            output_lines.append(line_bytes)

        raw_base_name = excel_name.replace("解析結果_", "").replace(".xlsx", "")
        out_txt_name = f"RESTORED_{raw_base_name}.txt"
        out_txt_path = os.path.join(recreated_dir, out_txt_name)

        try:
            with open(out_txt_path, "wb") as f:
                for line in output_lines:
                    f.write(line + b"\r\n")
        except PermissionError:
            logger.error(f"書き込み不可（他アプリで開いている可能性）: {out_txt_path}")
            continue

        logger.info(f"生成: {out_txt_path}")

    log_end(logger, "Excel→固定長復元完了")
