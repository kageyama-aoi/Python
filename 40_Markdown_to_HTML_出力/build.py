from pathlib import Path
import re
import sys

from jinja2 import Environment, FileSystemLoader, select_autoescape

from frontmatter import parse_front_matter
from md_store import HTML_DIR, MD_DIR

# ---------- 設定 ----------
DEFAULT_CATEGORY_NAME = "未分類"
CATEGORY_ORDER_FILE = MD_DIR / "_categories.txt"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

# ---------- 共通：停止＋説明 ----------
def stop(title: str, message: str):
    print("\n" + "=" * 60)
    print(f"⚠ {title}")
    print("-" * 60)
    print(message)
    print("=" * 60 + "\n")
    sys.exit(1)


def log_info(message: str):
    print(f"[INFO] {message}")


def log_ok(message: str):
    print(f"[OK]   {message}")


def log_read(message: str):
    print(f"[READ] {message}")


def print_warning_summary(warnings: list[str]):
    print("\n" + "=" * 56)
    print("WARNING SUMMARY")
    print("=" * 56)
    if not warnings:
        print("- 警告はありません。")
    else:
        for warning in warnings:
            print(f"- {warning}")
    print("=" * 56 + "\n")

# ---------- 事前チェック ----------
def check_and_prepare_structure():
    log_info("フォルダ構成チェックを開始します")

    if not MD_DIR.exists():
        try:
            MD_DIR.mkdir(parents=True, exist_ok=True)
            log_info(f"md ディレクトリを作成しました: {MD_DIR.resolve()}")
        except Exception as e:
            stop("md ディレクトリの作成に失敗しました", f"対象: {MD_DIR.resolve()}\n理由: {e}")
    elif not MD_DIR.is_dir():
        stop("md のパスがディレクトリではありません", f"対象: {MD_DIR.resolve()}")
    else:
        log_ok(f"md ディレクトリを確認しました: {MD_DIR.resolve()}")

    if not HTML_DIR.exists():
        try:
            HTML_DIR.mkdir(parents=True, exist_ok=True)
            log_info(f"html ディレクトリを作成しました: {HTML_DIR.resolve()}")
        except Exception as e:
            stop("html ディレクトリの作成に失敗しました", f"対象: {HTML_DIR.resolve()}\n理由: {e}")
    elif not HTML_DIR.is_dir():
        stop("html のパスがディレクトリではありません", f"対象: {HTML_DIR.resolve()}")
    else:
        log_ok(f"html ディレクトリを確認しました: {HTML_DIR.resolve()}")

    if not os_access_writable(HTML_DIR):
        stop("html ディレクトリに書き込めません", "書き込み権限があるか確認してください。")
    log_ok("html ディレクトリの書き込み権限を確認しました")


def check_environment(warnings: list[str]):
    md_files = sorted(MD_DIR.glob("*.md"))
    if not md_files:
        warnings.append(
            "md ディレクトリに Markdown ファイルがありません。"
            " .md ファイルを追加して再実行してください。"
        )
    return md_files

def os_access_writable(path: Path) -> bool:
    try:
        test_file = path / ".write_test"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
        return True
    except Exception:
        return False

# ---------- HTML 加工 ----------
IMG_TAG_RE = re.compile(r"<img\b([^>]*?)(/?)>", re.I)

def add_default_img_width_attr(html: str, width: int = 1000) -> str:
    """
    width 未指定の img タグにだけ width 属性を付与する。
    既存の width 指定は上書きしない。
    """
    def repl(match: re.Match) -> str:
        attrs = match.group(1)
        closing = match.group(2) or ""
        if re.search(r"\bwidth\s*=", attrs, flags=re.I):
            return match.group(0)
        return f'<img{attrs} width="{width}"{closing}>'

    return IMG_TAG_RE.sub(repl, html)

# ---------- メイン処理 ----------
def main():
    warnings: list[str] = []
    check_and_prepare_structure()
    md_files = check_environment(warnings)

    import markdown  # ← ここで初めて import

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
        keep_trailing_newline=True,
    )
    article_template = env.get_template("kb_article.html")
    index_template = env.get_template("kb_index.html")

    extensions = ["fenced_code", "tables"]
    try:
        import pymdownx.tasklist  # noqa: F401
        extensions.append("pymdownx.tasklist")
    except Exception:
        warnings.append("pymdown-extensions が未インストールのため、タスクリストは無効です。")

    # カテゴリ順（任意）
    category_order = []
    if CATEGORY_ORDER_FILE.exists():
        try:
            for raw_line in CATEGORY_ORDER_FILE.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                category_order.append(line)
        except Exception as e:
            stop("カテゴリ順ファイルの読み込みに失敗しました", f"対象: {CATEGORY_ORDER_FILE}\n理由: {e}")
    else:
        warnings.append(f"{CATEGORY_ORDER_FILE} が見つかりません。カテゴリ順はデフォルト順で処理します。")

    items = []
    uncategorized_count = 0

    for md_file in sorted(md_files):
        html_name = md_file.stem + ".html"
        html_path = HTML_DIR / html_name

        try:
            log_read(f"{md_file.name} を読み込み中...")
            text = md_file.read_text(encoding="utf-8")
            log_ok(f"{md_file.name} 読み込み成功 ({len(text):,} 文字)")
        except Exception as e:
            stop("Markdown 読み込みに失敗しました", f"対象: {md_file}\n理由: {e}")

        front_matter, content = parse_front_matter(text)
        category = str(front_matter.get("category") or DEFAULT_CATEGORY_NAME)
        if category == DEFAULT_CATEGORY_NAME:
            uncategorized_count += 1
        tags = front_matter.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if not isinstance(tags, list):
            tags = []

        try:
            body = markdown.markdown(
                content,
                extensions=extensions
            )
            body = add_default_img_width_attr(body, width=1000)
            log_ok(f"{md_file.name} を HTML に変換しました")
        except Exception as e:
            stop("Markdown 変換に失敗しました", f"対象: {md_file}\n理由: {e}")

        html = article_template.render(title=md_file.stem, body=body)

        try:
            html_path.write_text(html, encoding="utf-8")
            log_ok(f"{html_name} を出力しました")
        except Exception as e:
            stop("HTML 書き込みに失敗しました", f"対象: {html_path}\n理由: {e}")
        items.append({
            "html_name": html_name,
            "file_name": md_file.name,
            "category": category,
            "tags": tags,
        })

    # カテゴリごとに分類
    grouped: dict[str, list[dict]] = {}
    for item in items:
        grouped.setdefault(item["category"], []).append(item)

    # カテゴリ順の決定（指定があれば先頭に、残りは昇順）
    # 未分類は常に最後に配置する。
    ordered_categories = []
    seen = set()
    for c in category_order:
        if c == DEFAULT_CATEGORY_NAME:
            continue
        if c in grouped and c not in seen:
            ordered_categories.append(c)
            seen.add(c)
    for c in sorted(grouped.keys()):
        if c == DEFAULT_CATEGORY_NAME:
            continue
        if c not in seen:
            ordered_categories.append(c)
    if DEFAULT_CATEGORY_NAME in grouped:
        ordered_categories.append(DEFAULT_CATEGORY_NAME)

    # タグ一覧
    all_tags = sorted({t for item in items for t in item["tags"]})

    # テンプレートに渡すカテゴリ構造
    # 注意: キー名を "items" にすると Jinja側の cat.items が dict.items メソッドに
    # 解決されて TypeError になるため "entries" とする。
    categories_data = [
        {
            "name": category,
            "entries": [
                {
                    "html_name": item["html_name"],
                    "file_name": item["file_name"],
                    "category": item["category"],
                    "tags_csv": ",".join(item["tags"]),
                }
                for item in sorted(grouped[category], key=lambda x: x["file_name"].lower())
            ],
        }
        for category in ordered_categories
    ]

    index_html = index_template.render(categories=categories_data, all_tags=all_tags)

    try:
        (HTML_DIR / "index.html").write_text(index_html, encoding="utf-8")
    except Exception as e:
        stop("index.html 書き込みに失敗しました", f"対象: {HTML_DIR / 'index.html'}\n理由: {e}")

    if uncategorized_count > 0:
        warnings.append(
            f"category 未指定の Markdown が {uncategorized_count} 件あります。"
            f"未指定分は '{DEFAULT_CATEGORY_NAME}' で表示されます。"
        )

    print("HTML 生成が完了しました")
    print(f"{HTML_DIR / 'index.html'} をブラウザで開いてください")
    print_warning_summary(warnings)

# ---------- 実行 ----------
if __name__ == "__main__":
    main()
