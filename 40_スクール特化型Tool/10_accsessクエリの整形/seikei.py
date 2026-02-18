"""Step-1 SQL整形・フォーマッタ準備ツール。

目的:
    タブ区切りCSV/TSVに含まれるAccess風SQLを変換し、次の3成果物を作成する。
    1) 変換結果＋注意点付きCSV
    2) 変換後の生SQL
    3) フォーマッタ安全化SQL（プレースホルダ置換）

入力:
    - 既定入力: `kennsyuu.csv`（UTF-8 BOM、タブ区切り、ヘッダーなし想定）
    - SQL列はキーワード出現頻度で自動検出

実行例:
    python seikei.py
    python seikei.py --input kennsyuu.csv --out-csv 01_sanitized_with_notes.csv

実行順:
    このファイルを最初に実行する。
"""

import argparse
import os
import re
import shutil
from datetime import datetime

import pandas as pd


REPLACEMENT_TOKENS = {
    "／": "__FW_SLASH__",
    "/": "__SLASH__",
    "．": "__FW_DOT__",
    "。": "__JP_DOT__",
    "，": "__FW_COMMA__",
    "～": "__FW_WAVE__",
    "〜": "__WAVE__",
}
INTERNAL_SEMI_TOKEN = "/*__SC__*/"

DEFAULT_INPUT = "kennsyuu.csv"
DEFAULT_OUTPUT_CSV = "01_sanitized_with_notes.csv"
DEFAULT_OUTPUT_SQL_RAW = "02_sql_after_conversion.sql"
DEFAULT_OUTPUT_SQL_SAFE = "03_sql_for_formatter.safe.sql"
DEFAULT_ARCHIVE_DIR = "archive"

LEGACY_OUTPUTS = [
    "kennsyuu_sanitized.csv",
    "kennsyuu_sanitized_only.sql",
    "kennsyuu_sanitized_formatter_safe.sql",
    "kennsyuu_restored_from_formatter.sql",
]


def clean_access_sql(sql):
    """Access固有のSQL記法を変換しやすい形へ正規化する。

    Args:
        sql: 入力CSVセルの生SQL文字列。

    Returns:
        tuple[str, str]: 変換後SQLと処理メモ。
    """
    if pd.isna(sql) or str(sql).strip() == "":
        return "", "No SQL content"

    warnings = []
    converted = str(sql)

    if "#" in converted:
        converted = converted.replace("#", "'")
        warnings.append("Converted # date to '")
    if "&" in converted:
        converted = converted.replace("&", " + ")
        warnings.append("Changed & to +")
    if "!" in converted:
        converted = converted.replace("!", ".")
        warnings.append("Replaced ! with .")

    if "[" in converted or "]" in converted:
        converted = converted.replace("[", "FIX_").replace("]", "")
        warnings.append("Brackets to FIX_")

    pattern_num = r"(?<!['\w])\b(\d+[A-Za-z_]\w*)\b"
    if re.search(pattern_num, converted):
        converted = re.sub(pattern_num, r"FIX_\1", converted)
        warnings.append("Digit-start ID protected")

    before_bool = converted
    converted = re.sub(r"=\s*True\b", "= 1", converted, flags=re.IGNORECASE)
    converted = re.sub(r"=\s*Yes\b", "= 1", converted, flags=re.IGNORECASE)
    converted = re.sub(r"=\s*False\b", "= 0", converted, flags=re.IGNORECASE)
    converted = re.sub(r"=\s*No\b", "= 0", converted, flags=re.IGNORECASE)
    if converted != before_bool:
        warnings.append("Boolean values normalized")

    return converted, " | ".join(warnings)


def _replace_outside_single_quotes(sql, replacer):
    """シングルクォート文字列の外側だけに置換を適用する。"""
    parts = re.split(r"('(?:''|[^'])*')", sql)
    for i in range(0, len(parts), 2):
        parts[i] = replacer(parts[i])
    return "".join(parts)


def to_formatter_safe_sql(sql):
    """記号とセミコロンをフォーマッタ安全なプレースホルダへ置換する。"""
    if not sql:
        return sql

    src = sql.strip()
    had_terminal_semicolon = src.endswith(";")

    def replacer(chunk):
        out = chunk
        for ch, token in REPLACEMENT_TOKENS.items():
            out = out.replace(ch, token)
        out = out.replace(";", INTERNAL_SEMI_TOKEN)
        return out

    converted = _replace_outside_single_quotes(src, replacer).strip()

    if had_terminal_semicolon and converted.endswith(INTERNAL_SEMI_TOKEN):
        converted = converted[: -len(INTERNAL_SEMI_TOKEN)] + ";"
    elif not converted.endswith(";"):
        converted = converted.rstrip(";") + ";"

    return converted


def _detect_sql_column(df):
    """キーワード出現数にもとづいてSQL列を推定する。"""
    keyword_pattern = r"\b(?:SELECT|INSERT|UPDATE|DELETE)\b"
    scored_cols = []
    for col in df.columns:
        score = (
            df[col]
            .astype(str)
            .str.contains(keyword_pattern, case=False, regex=True, na=False)
            .sum()
        )
        scored_cols.append((score, col))

    best_score, sql_col_name = max(scored_cols, key=lambda x: x[0])
    if best_score == 0:
        fallback_idx = 7 if len(df.columns) > 7 else (4 if len(df.columns) > 4 else len(df.columns) - 1)
        sql_col_name = df.columns[fallback_idx]
    return sql_col_name


def _archive_files(files, archive_dir):
    """既存出力をタイムスタンプ付きでアーカイブへ退避する。"""
    os.makedirs(archive_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived = []
    for path in files:
        if not os.path.exists(path):
            continue
        base = os.path.basename(path)
        dst = os.path.join(archive_dir, f"{timestamp}_{base}")
        shutil.move(path, dst)
        archived.append(dst)
    return archived


def process_queries(input_file, output_csv, output_sql_raw, output_sql_safe, archive_dir):
    """Step-1の全処理を実行して3つの成果物を作成する。"""
    archive_targets = LEGACY_OUTPUTS + [output_csv, output_sql_raw, output_sql_safe]
    archived = _archive_files(archive_targets, archive_dir)
    if archived:
        print("アーカイブ済みファイル:")
        for p in archived:
            print(f"  - {p}")

    try:
        df = pd.read_csv(input_file, encoding="utf-8-sig", sep="\t", header=None)
    except Exception as e:
        print(f"入力ファイル読み込みエラー {input_file}: {e}")
        return False

    sql_col_name = _detect_sql_column(df)
    print(f"処理対象列: {sql_col_name}")

    results = df[sql_col_name].apply(clean_access_sql)

    df["Formatted_Candidate_SQL"] = [r[0] for r in results]
    df["Processing_Notes"] = [r[1] for r in results]

    df.to_csv(output_csv, index=False, encoding="utf-8-sig")

    sql_only_lines = [r[0].strip() for r in results if str(r[0]).strip()]
    with open(output_sql_raw, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write("\n\n".join(sql_only_lines))

    formatter_safe_lines = [to_formatter_safe_sql(s) for s in sql_only_lines]
    with open(output_sql_safe, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write("\n\n".join(formatter_safe_lines))

    print("生成ファイル:")
    print(f"  1) {output_csv}")
    print(f"  2) {output_sql_raw}")
    print(f"  3) {output_sql_safe}")
    print("次の手順:")
    print(f"  - {output_sql_safe} を VS Code で開いてSQL整形を実行してください。")
    print("  - その後、次のコマンドでプレースホルダを復元してください:")
    print(f"    python restore_formatter_safe_sql.py {output_sql_safe} 04_sql_restored_from_safe.sql")
    return True


def parse_args():
    """Step-1変換用のコマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(
        description="Step-1 変換: レビュー用SQLとフォーマッタ安全化SQLを生成します。"
    )
    parser.add_argument("--input", default=DEFAULT_INPUT, help=f"入力TSV/CSVファイル（既定: {DEFAULT_INPUT}）")
    parser.add_argument("--out-csv", default=DEFAULT_OUTPUT_CSV, help=f"注記付き出力CSV（既定: {DEFAULT_OUTPUT_CSV}）")
    parser.add_argument("--out-sql", default=DEFAULT_OUTPUT_SQL_RAW, help=f"変換後の生SQL出力（既定: {DEFAULT_OUTPUT_SQL_RAW}）")
    parser.add_argument(
        "--out-safe",
        default=DEFAULT_OUTPUT_SQL_SAFE,
        help=f"フォーマッタ安全化SQL出力（既定: {DEFAULT_OUTPUT_SQL_SAFE}）",
    )
    parser.add_argument(
        "--archive-dir",
        default=DEFAULT_ARCHIVE_DIR,
        help=f"旧出力/上書き対象を退避するアーカイブ先（既定: {DEFAULT_ARCHIVE_DIR}）",
    )
    return parser.parse_args()


def main():
    """Step-1変換のCLIエントリポイント。"""
    args = parse_args()
    ok = process_queries(args.input, args.out_csv, args.out_sql, args.out_safe, args.archive_dir)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()

