import pandas as pd

# レコード種別ラベル（D/H/T ⇔ 日本語表示名）の唯一の定義元。
# 出力Excelの「レコード種別」列・行の色分け・コメント生成など、種別名を扱う箇所は全てここを参照する。
REC_TYPE_DATA = "データ"
REC_TYPE_HEADER = "ヘッダー"
REC_TYPE_TRAILER = "トレーラー"

REC_TYPE_LABELS = {"D": REC_TYPE_DATA, "H": REC_TYPE_HEADER, "T": REC_TYPE_TRAILER}


def parse_sheet_rules(excel_file, sheet_name):
    """横並び設定シート(1行目:項目名, 2行目:開始位置, 3行目:文字数)を解析"""
    if not sheet_name or sheet_name not in excel_file.sheet_names:
        return None

    df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, nrows=3)
    fields = []
    for col_idx in range(1, df.shape[1]):
        field_name = df.iloc[0, col_idx]
        start_pos = df.iloc[1, col_idx]
        length = df.iloc[2, col_idx]

        if pd.isna(field_name) or pd.isna(start_pos) or pd.isna(length):
            continue

        fields.append({
            "name": str(field_name).strip(),
            "start": int(start_pos) - 1,  # 1-based -> 0-based
            "length": int(length),
        })
    return fields


def load_config_rules(config_path):
    """Config Excelを読み込み、レコード種別(D/H/T)ごとのルール辞書を返す"""
    excel_file = pd.ExcelFile(config_path)
    sheets = excel_file.sheet_names
    return {
        "D": parse_sheet_rules(excel_file, next((s for s in sheets if REC_TYPE_DATA in s), sheets[0])),
        "H": parse_sheet_rules(excel_file, next((s for s in sheets if REC_TYPE_HEADER in s), None)),
        "T": parse_sheet_rules(excel_file, next((s for s in sheets if REC_TYPE_TRAILER in s), None)),
    }


def match_config(filename, df_map, columns):
    """mapping.csvの判定キーワードとファイル名を照合し、設定ファイル名を返す"""
    for _, row in df_map.iterrows():
        key = str(row[columns["keyword"]]).strip()
        cfg_name = str(row[columns["config_name"]]).strip()
        if key and key in filename:
            return cfg_name
    return None
