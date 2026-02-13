from pathlib import Path
import json
import re

from flask import Flask, jsonify, request

MD_DIR = Path("md")
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def parse_front_matter(text: str) -> tuple[dict, str]:
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
                data[key] = []
                continue

            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                items = [v.strip() for v in inner.split(",") if v.strip()]
                data[key] = items
            else:
                data[key] = value
            continue

    return data, body


def build_front_matter(category: str, tags: list[str]) -> str:
    lines = ["---", f"category: {category}", "tags:"]
    for t in tags:
        lines.append(f"  - {t}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def update_md_file(md_path: Path, category: str, tags: list[str]) -> None:
    text = md_path.read_text(encoding="utf-8")
    _, body = parse_front_matter(text)
    fm = build_front_matter(category, tags)
    md_path.write_text(fm + "\n" + body.lstrip("\n"), encoding="utf-8")


app = Flask(__name__)


@app.get("/")
def index():
    return """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>Markdown Meta Editor</title>
<style>
  :root { --max: 1200px; --gap: 0.75rem; }
  body { font-family: system-ui, sans-serif; padding: 2rem; }
  .container { max-width: var(--max); margin: 0 auto; }
  .toolbar { display: flex; flex-wrap: wrap; gap: 0.75rem 1rem; align-items: center; }
  #search { flex: 1 1 320px; min-width: 220px; padding: 0.5rem; font-size: 1rem; }
  table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
  th, td { border-bottom: 1px solid #e5e5e5; padding: 0.5rem; text-align: left; vertical-align: top; }
  th { background: #fafafa; position: sticky; top: 0; }
  input[type="text"] { width: 100%; padding: 0.4rem; }
  .row { display: grid; grid-template-columns: 2fr 1fr 2fr auto; gap: var(--gap); align-items: center; }
  .list { display: grid; gap: 0.5rem; margin-top: 1rem; }
  .card { border: 1px solid #e5e5e5; border-radius: 8px; padding: 0.75rem; background: #fff; }
  .muted { color: #666; font-size: 0.9rem; }
  .actions { display: flex; gap: 0.5rem; }
  .ok { color: #0a6; font-size: 0.9rem; }
  @media (max-width: 900px) {
    .row { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<div class="container">
  <h1>Markdown メタ編集</h1>
  <div class="toolbar">
    <input id="search" type="search" placeholder="検索: ファイル名 / カテゴリ / タグ" />
    <button type="button" id="reload">再読み込み</button>
  </div>
  <div class="list" id="list"></div>
  <p class="muted">保存後に静的HTMLを更新するには `python build.py` を実行してください。</p>
</div>

<script>
  const listEl = document.getElementById('list');
  const searchEl = document.getElementById('search');
  const reloadBtn = document.getElementById('reload');
  let items = [];

  function normalize(v) { return (v || '').toLowerCase(); }

  function render() {
    const q = normalize(searchEl.value);
    listEl.innerHTML = '';
    items
      .filter(i => {
        if (!q) return true;
        return normalize(i.file).includes(q)
          || normalize(i.category).includes(q)
          || normalize(i.tags.join(',')).includes(q);
      })
      .forEach(i => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
          <div class="row">
            <div>
              <div><strong>${i.file}</strong></div>
              <div class="muted">${i.path}</div>
            </div>
            <div>
              <label class="muted">カテゴリ</label>
              <input type="text" value="${i.category}">
            </div>
            <div>
              <label class="muted">タグ（カンマ区切り）</label>
              <input type="text" value="${i.tags.join(', ')}">
            </div>
            <div class="actions">
              <button type="button">保存</button>
              <span class="ok" style="display:none;">保存済み</span>
            </div>
          </div>
        `;
        const inputs = card.querySelectorAll('input');
        const saveBtn = card.querySelector('button');
        const ok = card.querySelector('.ok');
        saveBtn.addEventListener('click', async () => {
          const category = inputs[0].value.trim() || '未分類';
          const tags = inputs[1].value.split(',').map(s => s.trim()).filter(Boolean);
          saveBtn.disabled = true;
          const res = await fetch('/api/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file: i.file, category, tags })
          });
          saveBtn.disabled = false;
          if (res.ok) {
            ok.style.display = 'inline';
            setTimeout(() => ok.style.display = 'none', 1200);
            i.category = category;
            i.tags = tags;
          } else {
            alert('保存に失敗しました');
          }
        });
        listEl.appendChild(card);
      });
  }

  async function load() {
    const res = await fetch('/api/items');
    items = await res.json();
    render();
  }

  searchEl.addEventListener('input', render);
  reloadBtn.addEventListener('click', load);
  load();
</script>
</body>
</html>
"""


@app.get("/api/items")
def items():
    out = []
    for md_path in sorted(MD_DIR.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        fm, _ = parse_front_matter(text)
        category = str(fm.get("category") or "未分類")
        tags = fm.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        if not isinstance(tags, list):
            tags = []
        out.append({
            "file": md_path.name,
            "path": str(md_path),
            "category": category,
            "tags": tags,
        })
    return jsonify(out)


@app.post("/api/update")
def update():
    data = request.get_json(force=True)
    file_name = data.get("file", "")
    category = data.get("category", "未分類")
    tags = data.get("tags", [])

    md_path = (MD_DIR / file_name).resolve()
    if md_path.parent != MD_DIR.resolve() or not md_path.exists() or md_path.suffix != ".md":
        return jsonify({"error": "invalid file"}), 400

    if not isinstance(tags, list):
        return jsonify({"error": "invalid tags"}), 400

    update_md_file(md_path, category, [str(t) for t in tags])
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
