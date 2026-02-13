from pathlib import Path
import re
import sys

# ---------- 設定 ----------
MD_DIR = Path("md")
HTML_DIR = Path("html")
DEFAULT_CATEGORY_NAME = "未分類"
CATEGORY_ORDER_FILE = MD_DIR / "_categories.txt"

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

# ---------- Front Matter 解析 ----------
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
IMG_TAG_RE = re.compile(r"<img\b([^>]*?)(/?)>", re.I)

def parse_front_matter(text: str) -> tuple[dict, str]:
    """
    最低限の YAML フロントマターを解析して本文と分離する。
    対応: key: value / key: [a, b] / key:
         - a
         - b
    """
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text

    fm_text = m.group(1)
    body = text[m.end():]

    data: dict[str, object] = {}
    current_key = None

    for raw_line in fm_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("- ") and current_key:
            data.setdefault(current_key, [])
            if isinstance(data[current_key], list):
                data[current_key].append(line[2:].strip())
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key

            if value == "":
                # 以降の "- " リストを待つ
                data[key] = []
                continue

            # [a, b] 形式
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                items = [v.strip() for v in inner.split(",") if v.strip()]
                data[key] = items
            else:
                data[key] = value
            continue

    return data, body

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

    items = []

    for md_file in sorted(md_files):
        html_name = md_file.stem + ".html"
        html_path = HTML_DIR / html_name

        try:
            text = md_file.read_text(encoding="utf-8")
        except Exception as e:
            stop("Markdown 読み込みに失敗しました", f"対象: {md_file}\n理由: {e}")

        front_matter, content = parse_front_matter(text)
        category = str(front_matter.get("category") or DEFAULT_CATEGORY_NAME)
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
    ordered_categories = []
    seen = set()
    for c in category_order:
        if c in grouped and c not in seen:
            ordered_categories.append(c)
            seen.add(c)
    for c in sorted(grouped.keys()):
        if c not in seen:
            ordered_categories.append(c)

    # タグ一覧
    all_tags = sorted({t for item in items for t in item["tags"]})

    category_sections = []
    for category in ordered_categories:
        links = []
        for item in sorted(grouped[category], key=lambda x: x["file_name"].lower()):
            tags_attr = ",".join(item["tags"])
            links.append(
                f'<li class="md-item" data-title="{item["file_name"]}" '
                f'data-tags="{tags_attr}" data-category="{item["category"]}">'
                f'<a href="{item["html_name"]}">{item["file_name"]}</a>'
                f'</li>'
            )
        category_sections.append(
            f"""<details class="category" data-category="{category}" open>
<summary>{category} <span class="count" data-total="{len(links)}">({len(links)})</span></summary>
<ul>
{chr(10).join(links)}
</ul>
</details>"""
        )

    tag_buttons = []
    for tag in all_tags:
        tag_buttons.append(f'<button type="button" class="tag" data-tag="{tag}">#{tag}</button>')

    index_html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>Markdown Index</title>
<style>
  :root {{
    --max: 1200px;
    --gap: 1.25rem;
  }}
  body {{ font-family: system-ui, sans-serif; padding: 2rem; line-height: 1.6; }}
  .container {{ max-width: var(--max); margin: 0 auto; }}
  .toolbar {{ display: flex; flex-wrap: wrap; gap: 0.75rem 1rem; align-items: center; margin-bottom: 0.75rem; }}
  #search {{ flex: 1 1 320px; min-width: 220px; padding: 0.5rem; font-size: 1rem; }}
  .toolbar .controls {{ display: flex; gap: 0.5rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--gap); }}
  details.category {{ padding: 0.5rem 0.75rem; border: 1px solid #e3e3e3; border-radius: 8px; background: #fafafa; }}
  details.category > summary {{ cursor: pointer; font-weight: 600; }}
  details.category ul {{ margin: 0.5rem 0 0; padding-left: 1.2rem; }}
  .md-item.hidden {{ display: none; }}
  .count {{ color: #666; font-size: 0.9rem; }}
  .tagbar {{ margin: 0.5rem 0 1rem; display: flex; flex-wrap: wrap; gap: 0.5rem; }}
  .tag {{ border: 1px solid #bbb; background: #f7f7f7; padding: 0.25rem 0.6rem; border-radius: 999px; cursor: pointer; }}
  .tag.active {{ background: #333; color: #fff; border-color: #333; }}
  .clear {{ border: 1px dashed #999; background: #fff; }}
  .category.hidden {{ display: none; }}
  @media (max-width: 640px) {{
    body {{ padding: 1rem; }}
    .toolbar {{ flex-direction: column; align-items: stretch; }}
    .toolbar .controls {{ justify-content: flex-start; }}
  }}
</style>
</head>
<body>
<div class="container">
<h1>Markdown 一覧</h1>
<div class="toolbar">
  <input id="search" type="search" placeholder="検索: タイトル / カテゴリ / タグ" />
  <div class="controls">
    <button type="button" id="openAll">全て開く</button>
    <button type="button" id="closeAll">全て閉じる</button>
  </div>
</div>
<div class="tagbar" id="tagbar">
  <button type="button" class="tag clear" id="clearTags">タグ解除</button>
  {chr(10).join(tag_buttons)}
</div>
<div class="grid">
{chr(10).join(category_sections)}
</div>

<script>
  const search = document.getElementById('search');
  const items = Array.from(document.querySelectorAll('.md-item'));
  const categories = Array.from(document.querySelectorAll('details.category'));
  const tagButtons = Array.from(document.querySelectorAll('.tagbar .tag')).filter(b => b.id !== 'clearTags');
  const clearTags = document.getElementById('clearTags');
  const selectedTags = new Set();
  const openAll = document.getElementById('openAll');
  const closeAll = document.getElementById('closeAll');

  function normalize(v) {{
    return (v || '').toLowerCase();
  }}

  function filter() {{
    const q = normalize(search.value);
    const hasFilter = q.length > 0 || selectedTags.size > 0;
    items.forEach((el) => {{
      const title = normalize(el.dataset.title);
      const tags = normalize(el.dataset.tags);
      const category = normalize(el.dataset.category);
      const tagList = (el.dataset.tags || '').split(',').map(s => s.trim()).filter(Boolean);
      const hasSelectedTags = Array.from(selectedTags).every(t => tagList.includes(t));
      const hitText = !q || title.includes(q) || tags.includes(q) || category.includes(q);
      const hit = hitText && (selectedTags.size === 0 || hasSelectedTags);
      el.classList.toggle('hidden', !hit);
    }});

    categories.forEach((cat) => {{
      const visibleCount = cat.querySelectorAll('.md-item:not(.hidden)').length;
      const countEl = cat.querySelector('.count');
      const total = countEl?.dataset.total || '0';
      if (countEl) {{
        countEl.textContent = hasFilter
          ? '(' + visibleCount + '/' + total + ')'
          : '(' + total + ')';
      }}
      cat.classList.toggle('hidden', visibleCount === 0);
    }});
  }}

  tagButtons.forEach((btn) => {{
    btn.addEventListener('click', () => {{
      const tag = btn.dataset.tag;
      if (!tag) return;
      if (selectedTags.has(tag)) {{
        selectedTags.delete(tag);
        btn.classList.remove('active');
      }} else {{
        selectedTags.add(tag);
        btn.classList.add('active');
      }}
      filter();
    }});
  }});

  clearTags.addEventListener('click', () => {{
    selectedTags.clear();
    tagButtons.forEach((b) => b.classList.remove('active'));
    filter();
  }});

  openAll.addEventListener('click', () => {{
    categories.forEach((c) => c.open = true);
  }});

  closeAll.addEventListener('click', () => {{
    categories.forEach((c) => c.open = false);
  }});

  search.addEventListener('input', filter);
  filter();
</script>
</div>
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
