import os
import shutil
from datetime import datetime

import pandas as pd

from src.utils.fixed_format import read_mapping_csv
from src.utils.log_tags import log_end, log_start


def _backup_existing_file(path, logger):
    """上書き前に既存ファイルをタイムスタンプ付きでバックアップする"""
    if not os.path.exists(path):
        return
    backup_path = f"{path}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(path, backup_path)
    logger.info(f"バックアップ作成: {backup_path}")


def _mapping_column_names(ctx):
    columns = ctx.mapping_columns
    return columns["keyword"], columns["config_name"], columns.get("note", "備考")


def load_mapping(ctx):
    """mapping.csvを読み込んでDataFrameを返す（無ければ列だけの空DataFrame）"""
    keyword_col, config_col, note_col = _mapping_column_names(ctx)
    if os.path.exists(ctx.mapping_csv):
        return read_mapping_csv(ctx.mapping_csv, ctx.encoding)
    return pd.DataFrame(columns=[keyword_col, config_col, note_col])


def find_existing_config(ctx, keyword):
    """指定キーワードが既に登録されていれば現在の適用Config名を返す（未登録ならNone）"""
    keyword_col, config_col, _ = _mapping_column_names(ctx)
    df_map = load_mapping(ctx)
    matched = df_map[df_map[keyword_col].astype(str) == str(keyword)]
    if matched.empty:
        return None
    return str(matched.iloc[0][config_col])


def add_mapping_entry(ctx, keyword, config_name, note=""):
    """mapping.csvにキーワード⇔設定ファイルの対応を1件登録する（同じキーワードがあれば置き換え）"""
    keyword_col, config_col, note_col = _mapping_column_names(ctx)

    df_map = load_mapping(ctx)
    _backup_existing_file(ctx.mapping_csv, ctx.logger)

    df_map = df_map[df_map[keyword_col].astype(str) != str(keyword)]
    new_row = pd.DataFrame([{keyword_col: keyword, config_col: config_name, note_col: note}])
    df_map = pd.concat([df_map, new_row], ignore_index=True)

    os.makedirs(os.path.dirname(ctx.mapping_csv), exist_ok=True)
    df_map.to_csv(ctx.mapping_csv, index=False, encoding=ctx.encoding)
    ctx.logger.info(f"mapping.csv登録: {keyword} → {config_name}")


def remove_mapping_entry(ctx, keyword):
    """mapping.csvから指定キーワードの行を削除する。該当行が無ければ何もせずFalseを返す"""
    keyword_col, _, _ = _mapping_column_names(ctx)

    df_map = load_mapping(ctx)
    if str(keyword) not in set(df_map[keyword_col].dropna().astype(str)):
        return False

    _backup_existing_file(ctx.mapping_csv, ctx.logger)
    df_map = df_map[df_map[keyword_col].astype(str) != str(keyword)]
    df_map.to_csv(ctx.mapping_csv, index=False, encoding=ctx.encoding)
    ctx.logger.info(f"mapping.csv削除: {keyword}")
    return True


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
        df_map = read_mapping_csv(mapping_csv, encoding)
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
        _backup_existing_file(mapping_csv, logger)
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
