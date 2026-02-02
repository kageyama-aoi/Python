from pathlib import Path
import sys

# ---------- 設定 ----------
MD_DIR = Path("md")
HTML_DIR = Path("html")

# ---------- 共通：停止＋説明 ----------
def stop(title: str, message: str):
    print("\n" + "=" * 60)
    print(f"⚠ {title}")
    print("-" * 60)
    print(message)
    print("=" * 60 + "\n")
    sys.exit(1)

# ---------- 事前チェック ----------
def check_environment():
    # md ディレクトリ
    if not MD_DIR.exists():
        stop(
            "md ディレクトリが見つかりません",
            f"以下のディレクトリを作成してください。\n\n  {MD_DIR.resolve()}"
        )

    # html ディレクトリ
    if not HTML_DIR.exists():
        stop(
            "html ディレクトリが見つかりません",
            f"以下のディレクトリを作成してください。\n\n  {HTML_DIR.resolve()}"
        )

    # html 書き込み権限
    if not HTML_DIR.is_dir() or not os_access_writable(HTML_DIR):
        stop(
            "html ディレクトリに書き込めません",
            "書き込み権限があるか確認してください。"
        )

    # md ファイル存在チェック
    md_files = list(MD_DIR.glob("*.md"))
    if not md_files:
        stop(
            "Markdown ファイルがありません",
            "md ディレクトリに .md ファイルを1つ以上配置してください。"
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

# ---------- メイン処理 ----------
def main():
    print("環境チェック中...")
    md_files = check_environment()
    print("環境チェック OK\n")

    import markdown  # ← ここで初めて import

    HTML_DIR.mkdir(exist_ok=True)

    extensions = ["fenced_code", "tables"]
    try:
        import pymdownx.tasklist  # noqa: F401
        extensions.append("pymdownx.tasklist")
    except Exception:
        print("注意: pymdown-extensions が未インストールのため、タスクリストは無効です。")

    links = []

    for md_file in sorted(md_files):
        html_name = md_file.stem + ".html"
        html_path = HTML_DIR / html_name

        try:
            text = md_file.read_text(encoding="utf-8")
        except Exception as e:
            stop("Markdown 読み込みに失敗しました", f"対象: {md_file}\n理由: {e}")

        try:
            body = markdown.markdown(
                text,
                extensions=extensions
            )
        except Exception as e:
            stop("Markdown 変換に失敗しました", f"対象: {md_file}\n理由: {e}")

        html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{md_file.stem}</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<a href="index.html">← 一覧へ</a>
<hr>
{body}
</body>
</html>
"""


        try:
            html_path.write_text(html, encoding="utf-8")
        except Exception as e:
            stop("HTML 書き込みに失敗しました", f"対象: {html_path}\n理由: {e}")
        links.append(f'<li><a href="{html_name}">{md_file.name}</a></li>')

    index_html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>Markdown Index</title>
</head>
<body>
<h1>Markdown 一覧</h1>
<ul>
{chr(10).join(links)}
</ul>
</body>
</html>
"""

    try:
        (HTML_DIR / "index.html").write_text(index_html, encoding="utf-8")
    except Exception as e:
        stop("index.html 書き込みに失敗しました", f"対象: {HTML_DIR / 'index.html'}\n理由: {e}")

    print("HTML 生成が完了しました")
    print(f"{HTML_DIR / 'index.html'} をブラウザで開いてください")

# ---------- 実行 ----------
if __name__ == "__main__":
    main()
