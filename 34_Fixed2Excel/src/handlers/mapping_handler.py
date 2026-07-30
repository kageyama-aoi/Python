import os

import pandas as pd

from src.utils.log_tags import log_end, log_start


def build_or_update_mapping(ctx):
    """input内のファイル名からキーワード候補を拾い、mapping.csvに未登録分を追記する"""
    dirs = ctx.dirs
    columns = ctx.mapping_columns
    mapping_csv = ctx.mapping_csv
    encoding = ctx.encoding
    logger = ctx.logger

    configs_dir = dirs["configs"]
    input_dir = dirs["input"]
    os.makedirs(configs_dir, exist_ok=True)
    os.makedirs(input_dir, exist_ok=True)

    keyword_col = columns["keyword"]
    config_col = columns["config_name"]
    note_col = columns.get("note", "備考")

    log_start(logger, "mapping.csv 更新開始")

    if os.path.exists(mapping_csv):
        df_map = pd.read_csv(mapping_csv, encoding=encoding)
        logger.info("既存mapping.csv読み込み")
    else:
        df_map = pd.DataFrame(columns=[keyword_col, config_col, note_col])
        logger.info("新規mapping.csv作成")

    mapping_csv_name = os.path.basename(mapping_csv)
    input_files = [f for f in os.listdir(input_dir) if not f.startswith(".")]
    config_files = [
        f for f in os.listdir(configs_dir)
        if f.endswith((".xlsx", ".csv")) and f != mapping_csv_name
    ]

    existing_keys = set(df_map[keyword_col].dropna().astype(str))
    new_rows = []
    for input_file in input_files:
        keyword_candidate = os.path.splitext(input_file)[0]
        if keyword_candidate not in existing_keys:
            default_config = config_files[0] if config_files else "（configs内のファイル名を指定）"
            new_rows.append({
                keyword_col: keyword_candidate,
                config_col: default_config,
                note_col: f"自動追加: {input_file}",
            })

    if new_rows:
        df_map = pd.concat([df_map, pd.DataFrame(new_rows)], ignore_index=True)
        df_map.to_csv(mapping_csv, index=False, encoding=encoding)
        logger.info(f"新規ファイル追記: {len(new_rows)}件")
    else:
        logger.info("新規ファイルなし（登録済み）")

    logger.info("configsフォルダ 設定ファイル一覧:")
    for cfg in config_files:
        logger.info(f" - {cfg}")

    log_end(logger, "mapping.csv 更新完了")

    return len(new_rows)
