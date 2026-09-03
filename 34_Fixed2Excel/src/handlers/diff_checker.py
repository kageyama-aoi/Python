import os

import pandas as pd

from src.handlers.fixed_to_excel import process_file
from src.utils.fixed_format import load_config_rules, resolve_config_path
from src.utils.log_tags import log_diff, log_end, log_start


def restored_name_for(input_name):
    """input側ファイル名から対応する復元後ファイル名を組み立てる（excel_to_fixed.restore_allの命名と対）"""
    base = os.path.splitext(input_name)[0]
    return f"RESTORED_{base}.txt"


def _values_equal(before_val, after_val):
    """レコード種別が異なる行では項目自体が存在せずNaNになるため、NaN同士は「一致」扱いにする
    （素朴な != 比較だとNaN != NaNがTrueになり、無関係の欠損項目まで差分扱いになってしまう）"""
    if pd.isna(before_val) and pd.isna(after_val):
        return True
    return before_val == after_val


def diff_rows(df_before, df_after, logger, txt_name):
    """行番号を揃えて項目単位で突き合わせ、差分をログ出力する。件数が違う場合はNoneを返す"""
    if len(df_before) != len(df_after):
        logger.error(
            f"{txt_name}: 件数不一致（変換前{len(df_before)}行 → 復元後{len(df_after)}行）。"
            "行の追加/削除の可能性があるため項目比較はスキップします。"
        )
        return None

    compare_columns = [c for c in df_before.columns if c != "行番号"]
    diff_count = 0
    for i in range(len(df_before)):
        row_before = df_before.iloc[i]
        row_after = df_after.iloc[i]
        row_no = row_before["行番号"]
        for col in compare_columns:
            before_val = row_before.get(col)
            after_val = row_after.get(col)
            if not _values_equal(before_val, after_val):
                diff_count += 1
                log_diff(logger, f"{txt_name} 行{row_no} 「{col}」: 「{before_val}」→「{after_val}」")
    return diff_count


def check_all(ctx):
    """data/input(原本)と data/recreated_input(復元後)を項目単位で突き合わせ、差分をログ出力する"""
    dirs = ctx.dirs
    configs_dir = dirs["configs"]
    input_dir = dirs["input"]
    recreated_dir = dirs["recreated"]
    logger = ctx.logger

    log_start(logger, "入力/復元後 差分チェック開始")

    if not os.path.exists(ctx.mapping_csv):
        logger.warning("mapping.csv未検出（先にmapping.csv更新を実行）")
        log_end(logger, "入力/復元後 差分チェック完了")
        return

    df_map = pd.read_csv(ctx.mapping_csv, encoding=ctx.encoding)
    input_files = [f for f in os.listdir(input_dir) if not f.startswith(".")]

    for txt_name in input_files:
        restored_name = restored_name_for(txt_name)
        restored_path = os.path.join(recreated_dir, restored_name)
        if not os.path.exists(restored_path):
            logger.info(f"スキップ: {txt_name}（復元後ファイル未検出: {restored_name}。先にExcel→固定長復元を実行）")
            continue

        config_path = resolve_config_path(txt_name, df_map, ctx.mapping_columns, configs_dir, logger)
        if not config_path:
            continue

        logger.info(f"比較: {txt_name} vs {restored_name}")

        config_rules = load_config_rules(config_path, logger=logger)
        input_path = os.path.join(input_dir, txt_name)
        df_before = process_file(input_path, config_rules, ctx.encoding, ctx.record_type_codes)
        df_after = process_file(restored_path, config_rules, ctx.encoding, ctx.record_type_codes)

        diff_count = diff_rows(df_before, df_after, logger, txt_name)
        if diff_count is None:
            continue
        if diff_count == 0:
            logger.info(f"{txt_name}: 差分なし（構成・値とも一致）")
        else:
            logger.warning(f"{txt_name}: 差分{diff_count}件検出（詳細は上記ログ参照）")

    log_end(logger, "入力/復元後 差分チェック完了")
