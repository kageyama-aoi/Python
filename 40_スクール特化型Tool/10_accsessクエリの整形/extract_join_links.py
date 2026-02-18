"""SQL結合キー抽出ツール。

目的:
    SQLのON/WHERE句にあるテーブル・カラム同士の等価条件を抽出する。

入力:
    - 単一SQLファイル、または `*.sql` を含むディレクトリ
    - 出力CSV既定: `join_links.csv`

実行例:
    python extract_join_links.py split_sql
    python extract_join_links.py 04_sql_restored_from_safe.sql --out join_links.csv

実行順:
    SQL復元/分割の後、集約前に実行する。
"""

import argparse
import csv
import os
import re
from pathlib import Path

# SQLキーワードをエイリアスとして誤認しないための簡易集合
KEYWORDS = {
    "ON", "WHERE", "GROUP", "ORDER", "HAVING", "UNION", "INNER", "LEFT", "RIGHT",
    "FULL", "JOIN", "AS", "SELECT", "FROM", "AND", "OR", "BY", "IN", "IS", "NOT"
}

IDENT = r"[\w\u0080-\uFFFF]+"
QUALIFIED_EQ_RE = re.compile(
    rf"({IDENT})\.({IDENT})\s*=\s*({IDENT})\.({IDENT})",
    re.IGNORECASE,
)

FROM_JOIN_RE = re.compile(
    rf"\b(?:FROM|JOIN)\s+({IDENT})(?:\s+(?:AS\s+)?({IDENT}))?",
    re.IGNORECASE,
)

ON_BLOCK_RE = re.compile(
    r"\bON\b(.*?)(?=\b(?:INNER|LEFT|RIGHT|FULL|JOIN|WHERE|GROUP|ORDER|HAVING|UNION)\b|;|$)",
    re.IGNORECASE | re.DOTALL,
)

WHERE_BLOCK_RE = re.compile(
    r"\bWHERE\b(.*?)(?=\b(?:GROUP|ORDER|HAVING|UNION)\b|;|$)",
    re.IGNORECASE | re.DOTALL,
)

STMT_TYPE_RE = re.compile(r"^\s*([A-Za-z]+)")


def sanitize_sql(sql: str) -> str:
    """行コメントを除去して正規表現マッチの安定性を上げる。"""
    lines = []
    for line in sql.splitlines():
        if line.lstrip().startswith("--"):
            continue
        lines.append(line)
    return "\n".join(lines)


def extract_alias_map(sql: str):
    """FROM/JOIN句から alias -> table の対応表を作る。"""
    alias_to_table = {}
    for m in FROM_JOIN_RE.finditer(sql):
        table = m.group(1)
        alias = m.group(2)
        alias_to_table[table] = table
        if alias and alias.upper() not in KEYWORDS:
            alias_to_table[alias] = table
    return alias_to_table


def statement_type(sql: str) -> str:
    """先頭トークンからSQL種別（例: SELECT）を返す。"""
    m = STMT_TYPE_RE.match(sql)
    return m.group(1).upper() if m else "UNKNOWN"


def extract_links_from_block(block: str, alias_map: dict, source: str, stmt_type: str, context: str):
    """1ブロック内の修飾付き等価条件を抽出する。"""
    rows = []
    seen = set()
    for m in QUALIFIED_EQ_RE.finditer(block):
        l_ref, l_col, r_ref, r_col = m.group(1), m.group(2), m.group(3), m.group(4)
        l_tbl = alias_map.get(l_ref, l_ref)
        r_tbl = alias_map.get(r_ref, r_ref)

        # 結合条件ではない自己比較は除外
        if l_tbl == r_tbl and l_col == r_col:
            continue

        key = (source, context, l_tbl, l_col, r_tbl, r_col)
        if key in seen:
            continue
        seen.add(key)

        rows.append(
            {
                "source": source,
                "statement_type": stmt_type,
                "context": context,
                "left_ref": l_ref,
                "left_table": l_tbl,
                "left_column": l_col,
                "right_ref": r_ref,
                "right_table": r_tbl,
                "right_column": r_col,
                "condition": m.group(0),
            }
        )
    return rows


def extract_from_sql(sql: str, source: str):
    """1つのSQLからON/WHERE由来の結合キー行を抽出する。"""
    text = sanitize_sql(sql)
    alias_map = extract_alias_map(text)
    stype = statement_type(text)
    rows = []

    for m in ON_BLOCK_RE.finditer(text):
        rows.extend(extract_links_from_block(m.group(1), alias_map, source, stype, "ON"))

    for m in WHERE_BLOCK_RE.finditer(text):
        rows.extend(extract_links_from_block(m.group(1), alias_map, source, stype, "WHERE"))

    return rows


def load_sql_files(input_path: Path):
    """単一ファイルまたはディレクトリから対象SQLファイル一覧を返す。"""
    files = []
    if input_path.is_file():
        files.append(input_path)
    else:
        for p in sorted(input_path.glob("*.sql")):
            if p.name.startswith("_"):
                continue
            files.append(p)
    return files


def main():
    """結合キー抽出のCLIエントリポイント。"""
    parser = argparse.ArgumentParser(description="SQLファイルから結合キー関係を抽出します。")
    parser.add_argument("input", help="SQLファイル、または分割SQLディレクトリ")
    parser.add_argument("--out", default="join_links.csv", help="出力CSVパス")
    args = parser.parse_args()

    input_path = Path(args.input)
    files = load_sql_files(input_path)
    if not files:
        raise SystemExit("SQLファイルが見つかりません。")

    all_rows = []
    for p in files:
        sql = p.read_text(encoding="utf-8-sig")
        all_rows.extend(extract_from_sql(sql, p.name))

    fieldnames = [
        "source",
        "statement_type",
        "context",
        "left_ref",
        "left_table",
        "left_column",
        "right_ref",
        "right_table",
        "right_column",
        "condition",
    ]

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)

    print(f"読み込んだSQLファイル数: {len(files)}")
    print(f"抽出した結合リンク数: {len(all_rows)}")
    print(f"出力先: {args.out}")


if __name__ == "__main__":
    main()

