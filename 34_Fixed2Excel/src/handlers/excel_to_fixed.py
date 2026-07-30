import os

import pandas as pd

from src.utils.fixed_format import REC_TYPE_DATA, REC_TYPE_LABELS, load_config_rules, match_config
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

        matched_config_name = match_config(excel_name, df_map, ctx.mapping_columns)
        if not matched_config_name:
            logger.info(f"スキップ: {excel_name}（キーワード不一致）")
            continue

        config_path = os.path.join(configs_dir, matched_config_name)
        if not os.path.exists(config_path):
            logger.error(f"設定ファイル不明: {matched_config_name}")
            continue

        logger.info(f"逆変換: {excel_name} → {matched_config_name}")

        rules_by_type = load_config_rules(config_path)
        rules_dict = {REC_TYPE_LABELS[k]: v for k, v in rules_by_type.items()}

        try:
            # dtype=str必須: 既定の型推論だと桁数の多い数字文字列(会員番号等)が
            # float64に変換され、有効桁を超えた分が丸められて値が壊れる。
            df_target = pd.read_excel(excel_path, dtype=str)
        except PermissionError:
            logger.error(f"読み込み不可（Excelで開いている可能性）: {excel_path}")
            continue

        output_lines = []
        for _, row in df_target.iterrows():
            rec_type = str(row.get("レコード種別", REC_TYPE_DATA)).strip()
            rules = rules_dict.get(rec_type) or rules_dict[REC_TYPE_DATA]
            line_bytes = build_fixed_line(row, rules, encoding)
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
