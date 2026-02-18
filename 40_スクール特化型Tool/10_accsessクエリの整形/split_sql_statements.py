"""SQL分割＋CSVコメント付与ツール。

目的:
    1つのSQLファイルを文単位へ分割し、メタCSVのコメントを各ファイル先頭へ付与する。

入力:
    - 必須入力SQL（例: `04_sql_restored_from_safe.sql`）
    - メタCSV（既定: `01_sanitized_with_notes.csv`）
    - 出力先ベースディレクトリ（既定: `split_sql`）

実行例:
    python split_sql_statements.py 04_sql_restored_from_safe.sql
    python split_sql_statements.py 04_sql_restored_from_safe.sql --out-dir split_sql --meta-csv 01_sanitized_with_notes.csv

実行順:
    SQL復元後、文ごとに解析したい場合に実行する。
"""

import argparse
import os
import re
from datetime import datetime

import pandas as pd

TOP_LEVEL_KEYWORDS = {
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "CREATE",
    "ALTER",
    "DROP",
    "WITH",
    "MERGE",
    "TRUNCATE",
    "REPLACE",
    "GRANT",
    "REVOKE",
    "COMMIT",
    "ROLLBACK",
    "BEGIN",
    "DECLARE",
    "CALL",
    "EXEC",
    "TRANSFORM",
}


def split_sql_statements(text: str):
    """引用符やコメントを考慮してトップレベルの`;`でSQLを分割する。"""
    statements = []
    buf = []

    in_single = False
    in_double = False
    in_line_comment = False
    in_block_comment = False

    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        if in_line_comment:
            buf.append(ch)
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            buf.append(ch)
            if ch == "*" and nxt == "/":
                buf.append(nxt)
                i += 2
                in_block_comment = False
            else:
                i += 1
            continue

        if not in_single and not in_double:
            if ch == "-" and nxt == "-":
                buf.append(ch)
                buf.append(nxt)
                i += 2
                in_line_comment = True
                continue
            if ch == "/" and nxt == "*":
                buf.append(ch)
                buf.append(nxt)
                i += 2
                in_block_comment = True
                continue

        if ch == "'" and not in_double:
            if in_single and nxt == "'":
                buf.append(ch)
                buf.append(nxt)
                i += 2
                continue
            in_single = not in_single
            buf.append(ch)
            i += 1
            continue

        if ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
            i += 1
            continue

        if ch == ";" and not in_single and not in_double:
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt + ";")
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)

    return statements


def _sanitize_comment(text: str) -> str:
    """メタ情報コメントを1行テキストへ正規化する。"""
    if text is None:
        return ""
    t = str(text).replace("\r", " ").replace("\n", " ").strip()
    if t.lower() == "nan":
        return ""
    return t


def load_comment_rows(meta_csv: str, col_a: str, col_b: str, col_c: str):
    """メタCSVから3列のコメントを読み込み、整形して返す。"""
    df = pd.read_csv(meta_csv, encoding="utf-8-sig", dtype=str)

    required = [col_a, col_b, col_c]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(
            f"コメント列が {meta_csv} に見つかりません: {missing}。"
            f"利用可能列: {list(df.columns)}"
        )

    rows = []
    for _, r in df[required].iterrows():
        rows.append(
            (
                _sanitize_comment(r[col_a]),
                _sanitize_comment(r[col_b]),
                _sanitize_comment(r[col_c]),
            )
        )
    return rows


def statement_type(sql: str) -> str:
    """先頭キーワードから安全なファイル名用トークンを作る。"""
    m = re.match(r"^\s*([A-Za-z]+)", sql)
    if not m:
        return "SQL"
    t = m.group(1).upper()
    return re.sub(r"[^A-Z0-9_]+", "_", t) or "SQL"


def _first_token(sql: str) -> str:
    """SQL断片の先頭トークンを返す。"""
    m = re.match(r"^\s*([A-Za-z_]+)", sql)
    return m.group(1).upper() if m else ""


def _is_continuation_fragment(sql: str) -> bool:
    """断片が前文の続きかどうかを判定する。"""
    s = sql.lstrip()
    if not s:
        return True
    if s[0] in "),":
        return True
    tok = _first_token(s)
    return tok not in TOP_LEVEL_KEYWORDS


def align_statement_count(statements, target_count):
    """過分割を結合して目標件数へ寄せる。"""
    if target_count <= 0:
        return statements

    aligned = list(statements)

    while len(aligned) > target_count:
        merged = False
        for i in range(len(aligned) - 1):
            nxt = aligned[i + 1]
            if _is_continuation_fragment(nxt):
                left = aligned[i].rstrip().rstrip(";")
                right = nxt.strip()
                aligned[i] = f"{left};\n{right}"
                del aligned[i + 1]
                merged = True
                break
        if not merged:
            left = aligned[-2].rstrip().rstrip(";")
            right = aligned[-1].strip()
            aligned[-2] = f"{left};\n{right}"
            aligned.pop()

    return aligned


def main():
    """SQL分割とコメント付与のCLIエントリポイント。"""
    parser = argparse.ArgumentParser(description="1つのSQLファイルを1文1ファイルへ分割します。")
    parser.add_argument("input", help="入力SQLファイル（例: 04_sql_restored_from_safe.sql）")
    parser.add_argument("--out-dir", default="split_sql", help="出力先ベースディレクトリ")
    parser.add_argument("--prefix", default="", help="任意のファイル名プレフィックス（例: プロジェクト名）")

    parser.add_argument(
        "--meta-csv",
        default="01_sanitized_with_notes.csv",
        help="SQLごとのコメント参照CSV（既定: 01_sanitized_with_notes.csv）",
    )
    parser.add_argument("--comment-col-1", default="0", help="1つ目のコメント列名（既定: 0）")
    parser.add_argument("--comment-col-2", default="1", help="2つ目のコメント列名（既定: 1）")
    parser.add_argument("--comment-col-3", default="3", help="3つ目のコメント列名（既定: 3）")
    parser.add_argument(
        "--sync-count-with-comments",
        action="store_true",
        default=True,
        help="過分割された文を結合し、コメント行数に合わせる（既定: 有効）",
    )

    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8-sig") as f:
        text = f.read()

    statements = split_sql_statements(text)
    if not statements:
        raise SystemExit("SQL文が見つかりません。")

    comment_rows = load_comment_rows(args.meta_csv, args.comment_col_1, args.comment_col_2, args.comment_col_3)

    original_count = len(statements)
    target_count = len(comment_rows)
    if args.sync_count_with_comments and original_count > target_count:
        statements = align_statement_count(statements, target_count)

    run_dir = os.path.join(args.out_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(run_dir, exist_ok=True)

    manifest_path = os.path.join(run_dir, "_manifest.txt")
    with open(manifest_path, "w", encoding="utf-8") as mf:
        mf.write(f"input={args.input}\n")
        mf.write(f"meta_csv={args.meta_csv}\n")
        mf.write(f"count_statements_before_sync={original_count}\n")
        mf.write(f"count_statements_after_sync={len(statements)}\n")
        mf.write(f"count_comments={len(comment_rows)}\n")

        if len(statements) != len(comment_rows):
            mf.write("warning=SQL文数とCSV行数が不一致\n")
            print(
                f"警告: SQL文数 ({len(statements)}) とコメント行数 ({len(comment_rows)}) が一致しません。"
                "いずれかが尽きるまで順番にコメントを付与します。"
            )
        else:
            mf.write("status=件数一致\n")

        for idx, stmt in enumerate(statements, start=1):
            stype = statement_type(stmt)
            base = f"{idx:03d}_{stype}.sql"
            if args.prefix:
                base = f"{idx:03d}_{args.prefix}_{stype}.sql"
            out_path = os.path.join(run_dir, base)

            c1 = c2 = c3 = ""
            if idx - 1 < len(comment_rows):
                c1, c2, c3 = comment_rows[idx - 1]

            with open(out_path, "w", encoding="utf-8-sig", newline="\n") as wf:
                if c1:
                    wf.write(f"-- {c1}\n")
                if c2:
                    wf.write(f"-- {c2}\n")
                if c3:
                    wf.write(f"-- {c3}\n")
                if c1 or c2 or c3:
                    wf.write("\n")
                wf.write(stmt.strip() + "\n")

            mf.write(f"{idx:03d}\t{stype}\t{base}\t{c1}\t{c2}\t{c3}\n")

    print(f"分割完了: {len(statements)} 文")
    print(f"出力ディレクトリ: {run_dir}")
    print(f"マニフェスト: {manifest_path}")


if __name__ == "__main__":
    main()

