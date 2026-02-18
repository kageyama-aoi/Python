"""JOINリンク集約ツール（テーブルペア単位）。

目的:
    `join_links.csv` の行単位リンクをテーブルペア単位で集約し、件数を集計する。

入力:
    - 既定入力: `join_links.csv`
    - 想定列: left_table, right_table, left_column, right_column, source, context

実行例:
    python aggregate_join_links.py
    python aggregate_join_links.py --input join_links.csv --output join_links_table_pairs.csv --sort table

実行順:
    `extract_join_links.py` 実行後に使う。
"""

import argparse
import csv

INPUT_DEFAULT = "join_links.csv"
OUTPUT_DEFAULT = "join_links_table_pairs.csv"


def norm_pair(a, b):
    """テーブルペアを順序非依存のタプルへ正規化する。"""
    return tuple(sorted([a, b]))


def build_rows(input_path):
    """行単位リンクからテーブルペア集約行を作る。

    Args:
        input_path: `join_links.csv` のパス。

    Returns:
        list[dict]: CSV出力用の集約行。
    """
    agg = {}

    with open(input_path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            lt = (row.get("left_table") or "").strip()
            rt = (row.get("right_table") or "").strip()
            if not lt or not rt:
                continue

            t1, t2 = norm_pair(lt, rt)
            key = (t1, t2)
            if key not in agg:
                agg[key] = {
                    "table_a": t1,
                    "table_b": t2,
                    "link_count": 0,
                    "column_pairs": set(),
                    "sources": set(),
                    "contexts": set(),
                }

            a = agg[key]
            a["link_count"] += 1
            a["column_pairs"].add(f"{row.get('left_column','')} = {row.get('right_column','')}")
            a["sources"].add(row.get("source", ""))
            a["contexts"].add(row.get("context", ""))

    rows = []
    for v in agg.values():
        rows.append(
            {
                "table_a": v["table_a"],
                "table_b": v["table_b"],
                "link_count": v["link_count"],
                "column_pair_count": len(v["column_pairs"]),
                "column_pairs": " | ".join(sorted(x for x in v["column_pairs"] if x.strip())),
                "source_count": len([s for s in v["sources"] if s]),
                "sources": " | ".join(sorted(s for s in v["sources"] if s)),
                "contexts": " | ".join(sorted(c for c in v["contexts"] if c)),
            }
        )
    return rows


def sort_rows(rows, sort_mode):
    """集約行をテーブル名順またはリンク件数順で並び替える。"""
    if sort_mode == "link":
        rows.sort(key=lambda x: (-int(x["link_count"]), x["table_a"], x["table_b"]))
    else:
        rows.sort(key=lambda x: (x["table_a"], x["table_b"], -int(x["link_count"])))


def write_rows(rows, output_path):
    """集約結果をUTF-8 BOM付きCSVとして保存する。"""
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "table_a",
                "table_b",
                "link_count",
                "column_pair_count",
                "column_pairs",
                "source_count",
                "sources",
                "contexts",
            ],
        )
        w.writeheader()
        w.writerows(rows)


def count_input_rows(path):
    """入力CSVのデータ行数（ヘッダー除く）を数える。"""
    with open(path, "r", encoding="utf-8-sig") as f:
        return max(sum(1 for _ in f) - 1, 0)


def main():
    """集約処理のCLIエントリポイント。"""
    parser = argparse.ArgumentParser(description="join_links.csv をテーブルペア単位で集約します。")
    parser.add_argument("--input", default=INPUT_DEFAULT, help=f"入力CSV（既定: {INPUT_DEFAULT}）")
    parser.add_argument("--output", default=OUTPUT_DEFAULT, help=f"出力CSV（既定: {OUTPUT_DEFAULT}）")
    parser.add_argument(
        "--sort",
        choices=["table", "link"],
        default="table",
        help="並び順: table=テーブル名順, link=リンク件数降順（既定: table）",
    )
    args = parser.parse_args()

    rows = build_rows(args.input)
    sort_rows(rows, args.sort)
    write_rows(rows, args.output)

    print(f"入力行数: {count_input_rows(args.input)}")
    print(f"集約後テーブルペア数: {len(rows)}")
    print(f"並び順: {args.sort}")
    print(f"出力先: {args.output}")


if __name__ == "__main__":
    main()

