"""フォーマッタ安全化SQLの復元ツール。

目的:
    フォーマット用に置換したプレースホルダを元の記号へ戻す。

入力:
    - 必須入力: フォーマッタ安全化SQL（例: `03_sql_for_formatter.safe.sql`）
    - 任意出力: 復元後SQL（既定: `04_sql_restored_from_safe.sql`）

実行例:
    python restore_formatter_safe_sql.py 03_sql_for_formatter.safe.sql
    python restore_formatter_safe_sql.py 03_sql_for_formatter.safe.sql 04_sql_restored_from_safe.sql

実行順:
    Step-1の安全化SQLを整形した後に実行する。
"""

import argparse
import re
from pathlib import Path

REVERSE_TOKENS = {
    "__FW_SLASH__": "／",
    "__SLASH__": "/",
    "__FW_DOT__": "．",
    "__JP_DOT__": "。",
    "__FW_COMMA__": "，",
    "__FW_WAVE__": "～",
    "__WAVE__": "〜",
}
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = "output/04_sql_restored_from_safe.sql"


def resolve_path(path_str: str) -> Path:
    """相対パスをプロジェクトルート基準へ解決する。"""
    p = Path(path_str)
    return p if p.is_absolute() else (PROJECT_ROOT / p)


def restore_sql(text: str) -> str:
    """SQL全体の区切り記号と置換トークンを復元する。"""
    out = re.sub(r"/\*\s*__SC__\s*\*/", ";", text, flags=re.IGNORECASE)
    for token, ch in REVERSE_TOKENS.items():
        out = re.sub(re.escape(token), ch, out, flags=re.IGNORECASE)
    return out


def main() -> None:
    """復元処理のCLIエントリポイント。"""
    parser = argparse.ArgumentParser(
        description="Step-2 復元: フォーマッタ安全化SQLを元の文字へ戻します（レイアウト維持）。"
    )
    parser.add_argument("input", help="整形済みの安全化SQLファイル（例: 03_sql_for_formatter.safe.sql）")
    parser.add_argument("output", nargs="?", default=DEFAULT_OUTPUT, help=f"復元後SQLの出力先（既定: {DEFAULT_OUTPUT}）")
    args = parser.parse_args()

    input_path = resolve_path(args.input)
    output_path = resolve_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(input_path, "r", encoding="utf-8-sig") as f:
        src = f.read()

    restored = restore_sql(src)

    with open(output_path, "w", encoding="utf-8-sig", newline="\n") as f:
        f.write(restored)

    print(f"復元SQLを保存しました: {output_path}")


if __name__ == "__main__":
    main()

