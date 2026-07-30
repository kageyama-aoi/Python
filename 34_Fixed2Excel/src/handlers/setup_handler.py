import os

import pandas as pd

from src.handlers.excel_to_fixed import build_fixed_line
from src.utils.fixed_format import REC_TYPE_DATA, REC_TYPE_HEADER, REC_TYPE_TRAILER
from src.utils.log_tags import log_end, log_start

# サンプルConfig（Excel）とサンプル固定長テキストを同じ定義から生成する。
# 区分(1バイト目)は各シートに含めず、レコード種別コードとして別途付与する。
HEADER_FIELDS = [
    {"name": "作成年月日", "start": 2, "length": 8},
    {"name": "送信元コード", "start": 10, "length": 10},
    {"name": "送信元名称", "start": 20, "length": 30},
    {"name": "予備", "start": 50, "length": 20},
]

DATA_FIELDS = [
    {"name": "会員番号", "start": 2, "length": 16},
    {"name": "有効期限", "start": 18, "length": 4},
    {"name": "店舗名", "start": 22, "length": 20},
    {"name": "店舗仕様", "start": 42, "length": 15},
    {"name": "金額", "start": 57, "length": 10},
    {"name": "予備", "start": 67, "length": 4},
]

TRAILER_FIELDS = [
    {"name": "合計件数", "start": 2, "length": 10},
    {"name": "合計金額", "start": 12, "length": 12},
    {"name": "予備", "start": 24, "length": 16},
]

SAMPLE_DATA_ROWS = [
    {"会員番号": "1000000000000001", "有効期限": "2801", "店舗名": "TEST_SHOP_A", "店舗仕様": "SPEC_A", "金額": "1000"},
    {"会員番号": "1000000000000002", "有効期限": "2805", "店舗名": "TEST_SHOP_B", "店舗仕様": "SPEC_B", "金額": "1500"},
    {"会員番号": "1000000000000003", "有効期限": "2812", "店舗名": "TEST_SHOP_C", "店舗仕様": "SPEC_C", "金額": "2000"},
]


def _sheet_df(fields):
    """フィールド定義から parse_sheet_rules が読める横並びシートDataFrameを作る"""
    columns = ["区分"] + [f["name"] for f in fields]
    start_row = ["開始位置"] + [f["start"] for f in fields]
    length_row = ["文字数"] + [f["length"] for f in fields]
    return pd.DataFrame([start_row, length_row], columns=columns)


def _build_line(rec_code, fields, values, encoding):
    """フィールド定義と値からrec_code付きの固定長バイト列を作る（Excel⇔固定長と同じ組み立てロジックを使う）"""
    rules = [{"name": f["name"], "start": f["start"] - 1, "length": f["length"]} for f in fields]
    line = bytearray(build_fixed_line(values, rules, encoding))
    line[0:1] = rec_code.encode(encoding)
    return bytes(line)


def init_environment(ctx):
    """configs/input/output/recreated_input フォルダとサンプルConfig・サンプル固定長テキストを生成する"""
    dirs = ctx.dirs
    encoding = ctx.encoding
    logger = ctx.logger

    log_start(logger, "Fixed2Excel 開発環境 セットアップ開始")

    for folder in dirs.values():
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"フォルダ作成: {folder}/")
        else:
            logger.info(f"既存フォルダ使用: {folder}/")

    sample_config_path = os.path.join(dirs["configs"], "config_サンプル会員データ.xlsx")
    if not os.path.exists(sample_config_path):
        with pd.ExcelWriter(sample_config_path, engine="openpyxl") as writer:
            _sheet_df(DATA_FIELDS).to_excel(writer, sheet_name=REC_TYPE_DATA, index=False)
            _sheet_df(HEADER_FIELDS).to_excel(writer, sheet_name=REC_TYPE_HEADER, index=False)
            _sheet_df(TRAILER_FIELDS).to_excel(writer, sheet_name=REC_TYPE_TRAILER, index=False)

        logger.info(f"ひな形Excel作成: {sample_config_path}")

    sample_input_path = os.path.join(dirs["input"], "KAIIN_SAMPLE.txt")
    if not os.path.exists(sample_input_path):
        h_line = _build_line("1", HEADER_FIELDS, {
            "作成年月日": "20260730",
            "送信元コード": "SRC001",
            "送信元名称": "TEST_SENDER",
        }, encoding)

        d_lines = [_build_line("2", DATA_FIELDS, row, encoding) for row in SAMPLE_DATA_ROWS]

        record_count = len(SAMPLE_DATA_ROWS)
        total_amount = sum(int(row["金額"]) for row in SAMPLE_DATA_ROWS)
        t_line = _build_line("9", TRAILER_FIELDS, {
            "合計件数": str(record_count),
            "合計金額": str(total_amount),
        }, encoding)

        with open(sample_input_path, "wb") as f:
            for line in [h_line, *d_lines, t_line]:
                f.write(line + b"\r\n")

        logger.info(f"サンプル固定長テキスト作成: {sample_input_path}（データ{record_count}件 / 合計金額{total_amount}）")

    log_end(logger, "Fixed2Excel 開発環境 セットアップ完了")
