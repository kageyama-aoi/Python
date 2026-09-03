import os

import pandas as pd

# レコード種別ラベル（D/H/T ⇔ 日本語表示名）の唯一の定義元。
# 出力Excelの「レコード種別」列・行の色分け・コメント生成など、種別名を扱う箇所は全てここを参照する。
REC_TYPE_DATA = "データ"
REC_TYPE_HEADER = "ヘッダー"
REC_TYPE_TRAILER = "トレーラー"
REC_TYPE_END = "エンドレコード"

REC_TYPE_LABELS = {"D": REC_TYPE_DATA, "H": REC_TYPE_HEADER, "T": REC_TYPE_TRAILER, "E": REC_TYPE_END}


def parse_sheet_rules(excel_file, sheet_name, invalid_cells=None):
    """横並び設定シート(1行目:項目名, 2行目:開始位置, 3行目:文字数)を解析

    開始位置・文字数が数値に変換できないセル（数式の文字列化・全角数字・単位付き等）は、
    そのフィールドを飛ばす。invalid_cells（list）を渡すと飛ばしたフィールド名を追記する。
    """
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

        try:
            start = int(start_pos) - 1  # 1-based -> 0-based
            length = int(length)
        except (ValueError, TypeError):
            if invalid_cells is not None:
                invalid_cells.append(f"{sheet_name}「{str(field_name).strip()}」")
            continue

        fields.append({
            "name": str(field_name).strip(),
            "start": start,
            "length": length,
        })
    return fields


def load_config_rules(config_path, logger=None):
    """Config Excelを読み込み、レコード種別(D/H/T/E)ごとのルール辞書を返す。

    logger を渡すと、桁定義の不整合（重なり・隙間・非正の値・数値化できないセル・
    レコード種別間の終端位置ズレ）を WARNING で通知する（処理は止めない）。
    """
    excel_file = pd.ExcelFile(config_path)
    sheets = excel_file.sheet_names
    invalid_cells = []
    rules = {
        "D": parse_sheet_rules(excel_file, next((s for s in sheets if REC_TYPE_DATA in s), sheets[0]), invalid_cells),
        "H": parse_sheet_rules(excel_file, next((s for s in sheets if REC_TYPE_HEADER in s), None), invalid_cells),
        "T": parse_sheet_rules(excel_file, next((s for s in sheets if REC_TYPE_TRAILER in s), None), invalid_cells),
        "E": parse_sheet_rules(excel_file, next((s for s in sheets if REC_TYPE_END in s), None), invalid_cells),
    }

    if logger is not None:
        name = os.path.basename(config_path)
        for cell in invalid_cells:
            logger.warning(f"{name}: {cell} の開始位置/文字数が数値ではないためこの項目を無視しました")
        for msg in validate_config_rules(rules):
            logger.warning(f"{name}: {msg}")

    return rules


def validate_config_rules(config_rules):
    """レコード種別ごとのルールを検証し、警告メッセージ（str）のリストを返す。

    - 開始位置・文字数が正でない
    - フィールド範囲の重なり
    - フィールド間の隙間（未定義バイト）
    - レコード種別ごとの終端位置（=想定レコード長）が種別間で不一致

    重なり・隙間・ズレは意図的な設計の場合もあるため、処理は止めず注意喚起にとどめる。
    """
    messages = []
    end_positions = {}
    for rec_key, rules in config_rules.items():
        if not rules:
            continue
        label = REC_TYPE_LABELS.get(rec_key, rec_key)

        for r in rules:
            if r["length"] <= 0:
                messages.append(f"{label}「{r['name']}」: 文字数が {r['length']}（1以上にしてください）")
            if r["start"] < 0:
                messages.append(f"{label}「{r['name']}」: 開始位置が {r['start'] + 1}（1以上にしてください）")

        cursor = 0
        for r in sorted(rules, key=lambda r: r["start"]):
            s, e = r["start"], r["start"] + r["length"]
            if s < cursor:
                messages.append(
                    f"{label}「{r['name']}」（開始位置 {s + 1}）: 直前のフィールドと {cursor - s} バイト重なっています"
                )
            elif s > cursor:
                messages.append(
                    f"{label}: 開始位置 {cursor + 1}〜{s} に未定義のバイトがあります（「{r['name']}」の手前）"
                )
            cursor = max(cursor, e)
        end_positions[label] = cursor

    if len(set(end_positions.values())) > 1:
        detail = "、".join(f"{k}={v}" for k, v in end_positions.items())
        messages.append(f"レコード種別ごとの終端位置（レコード長）が揃っていません（{detail}）")

    return messages


def count_field_name_usage(config_rules):
    """項目名がいくつのレコード種別で使われているかを数える
    （複数のレコード種別で共有される項目名を判定するために使う）"""
    counts = {}
    for rules in config_rules.values():
        for rule in rules or []:
            counts[rule["name"]] = counts.get(rule["name"], 0) + 1
    return counts


def column_name_for(field_name, rec_type_label, name_counts):
    """出力Excel上のカラム名を決める。

    同じ項目名が複数のレコード種別で使われる場合（例:「予備」がヘッダーとデータの両方にある）、
    開始位置・文字数がレコード種別ごとに異なることがあるため1カラムに混在させられない。
    「項目名（種別）」の形で種別ごとに別カラムとして分ける。1つの種別だけで使われる項目名は
    そのままの名前にする。
    """
    if name_counts.get(field_name, 0) > 1:
        return f"{field_name}（{rec_type_label}）"
    return field_name


def build_field_columns(config_rules):
    """レコード種別ごとの各項目に、出力Excel上で一意な出力カラム名を割り当てる。

    - 同じ項目名が複数のレコード種別で使われる場合:「項目名（種別）」で区別する(column_name_for)。
    - さらに、同じレコード種別の中で同じ項目名が複数回使われる場合（実務の転記漏れでありがちな、
      本来別々の項目に同じラベルを使い回しているケース。例: あるトレーラーの「区分コード」が
      13個ある）は、それだけでは列名が衝突して値が上書きされてしまうため、出現順の連番も付けて
      完全に一意にする。

    戻り値: {レコード種別コード: [{"column": 出力カラム名, "rule": rule}, ...]}
    """
    name_counts = count_field_name_usage(config_rules)

    result = {}
    for rec_key, rules in config_rules.items():
        rules = rules or []
        label = REC_TYPE_LABELS.get(rec_key, rec_key)
        type_name_counts = {}
        for rule in rules:
            type_name_counts[rule["name"]] = type_name_counts.get(rule["name"], 0) + 1

        seen = {}
        columns = []
        for rule in rules:
            name = rule["name"]
            column = column_name_for(name, label, name_counts)
            if type_name_counts[name] > 1:
                seen[name] = seen.get(name, 0) + 1
                column = f"{column}{seen[name]}"
            columns.append({"column": column, "rule": rule})
        result[rec_key] = columns
    return result


class AmbiguousKeywordMatchError(Exception):
    """1つのファイル名に複数のキーワードが部分一致した場合に送出する"""

    def __init__(self, filename, matches):
        self.filename = filename
        self.matches = matches  # [(keyword, config_name), ...]
        keywords = "、".join(f"'{k}'→{c}" for k, c in matches)
        super().__init__(
            f"{filename}: 複数のキーワードが部分一致しました（{keywords}）。"
            "どちらを採用すべきか自動判定できないため処理をスキップします。mapping.csvのキーワードを見直してください。"
        )


def match_config(filename, df_map, columns):
    """mapping.csvの判定キーワードとファイル名を照合し、設定ファイル名を返す（不一致ならNone）。

    キーワードは部分一致(in)で判定するため、複数行が同時に一致することがある
    （例: 'SAMPLE'と'KAIIN_SAMPLE'が両方登録されていると'KAIIN_SAMPLE_20260731.txt'は両方に一致する）。
    どちらを採用すべきか機械的に決められないため、その場合はAmbiguousKeywordMatchErrorを送出する。
    """
    matches = []
    for _, row in df_map.iterrows():
        key = str(row[columns["keyword"]]).strip()
        cfg_name = str(row[columns["config_name"]]).strip()
        if key and key in filename:
            matches.append((key, cfg_name))

    if not matches:
        return None
    if len(matches) > 1:
        raise AmbiguousKeywordMatchError(filename, matches)
    return matches[0][1]


def resolve_config_path(filename, df_map, columns, configs_dir, logger):
    """filenameに対応する設定Excelのフルパスを解決する（convert_all/restore_all/check_all共通処理）。

    キーワード不一致・複数一致・設定ファイル欠落のいずれの場合も、理由をloggerに出したうえで
    Noneを返す（呼び出し側は`if not config_path: continue`とするだけでよい）。
    """
    try:
        matched_config_name = match_config(filename, df_map, columns)
    except AmbiguousKeywordMatchError as e:
        logger.error(str(e))
        return None

    if not matched_config_name:
        logger.info(f"スキップ: {filename}（キーワード不一致）")
        return None

    config_path = os.path.join(configs_dir, matched_config_name)
    if not os.path.exists(config_path):
        logger.error(f"設定ファイル不明: {matched_config_name}")
        return None
    return config_path
