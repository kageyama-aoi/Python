from pathlib import Path
import re
import subprocess
from datetime import datetime
from html import escape

from flask import Flask, jsonify, request, send_file

MD_DIR = Path("md")
HTML_DIR = Path("html")
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


def normalize_tags(raw_tags: object) -> list[str]:
    if isinstance(raw_tags, str):
        tag = raw_tags.strip()
        return [tag] if tag else []
    if not isinstance(raw_tags, list):
        return []
    result: list[str] = []
    for t in raw_tags:
        tag = str(t).strip()
        if tag and tag not in result:
            result.append(tag)
    return result


def resolve_md_path(file_name: str) -> Path | None:
    md_path = (MD_DIR / file_name).resolve()
    if md_path.parent != MD_DIR.resolve() or not md_path.exists() or md_path.suffix != ".md":
        return None
    return md_path


def sanitize_file_stem(title: str) -> str:
    stem = re.sub(r"[\\/:*?\"<>|]", " ", title)
    stem = re.sub(r"\s+", " ", stem).strip()
    stem = stem.replace(".", "_")
    if not stem:
        return "untitled"
    return stem[:60]


def normalize_md_filename(raw_name: str) -> str | None:
    name = (raw_name or "").strip()
    if not name:
        return None
    name = re.sub(r"[\\/:*?\"<>|]", " ", name)
    name = Path(name).name.strip()
    if not name:
        return None
    if not name.lower().endswith(".md"):
        name = f"{name}.md"
    stem = Path(name).stem.strip()
    stem = re.sub(r"\s+", " ", stem)
    if not stem:
        return None
    return f"{stem}.md"


def parse_csv_tags(raw_text: str) -> list[str]:
    tags: list[str] = []
    for part in raw_text.split(","):
        tag = part.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def make_unique_md_path(base_stem: str) -> Path:
    date_prefix = datetime.now().strftime("%Y%m%d")
    candidate = MD_DIR / f"{date_prefix}_{base_stem}.md"
    if not candidate.exists():
        return candidate
    idx = 2
    while True:
        alt = MD_DIR / f"{date_prefix}_{base_stem}_{idx}.md"
        if not alt.exists():
            return alt
        idx += 1


def collect_meta_options() -> tuple[list[str], list[str]]:
    categories: set[str] = set()
    tags: set[str] = set()
    for md_path in sorted(MD_DIR.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        fm, _ = parse_front_matter(text)
        category = str(fm.get("category") or "").strip()
        if category:
            categories.add(category)
        for t in normalize_tags(fm.get("tags") or []):
            if t:
                tags.add(t)
    sorted_categories = sorted(categories, key=lambda x: x.lower())
    sorted_tags = sorted(tags, key=lambda x: x.lower())
    return sorted_categories, sorted_tags


app = Flask(__name__)


@app.get("/")
@app.get("/meta")
def index():
    return """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>Markdown Meta Editor</title>
<style>
  :root {
    --max: 1120px;
    --gap: 0.75rem;
    --space-1: 0.5rem;
    --space-2: 0.75rem;
    --space-3: 1rem;
    --space-4: 1.5rem;
    --radius-1: 10px;
  }
  body { font-family: system-ui, sans-serif; padding: var(--space-4); background: #f5f7fa; margin: 0; line-height: 1.6; }
  .container { max-width: var(--max); margin: 0 auto; }
  .topnav { display: flex; flex-wrap: wrap; gap: 0.8rem; margin: 0.2rem 0 0.9rem; }
  .topnav a { color: #0f4c81; text-decoration: none; border-bottom: 1px solid #0f4c81; }
  .topnav a:hover { opacity: 0.85; }
  .toolbar { display: flex; flex-wrap: wrap; gap: 0.75rem 1rem; align-items: center; }
  #search { flex: 1 1 320px; min-width: 220px; padding: var(--space-1); font-size: 1rem; }
  input[type="text"], select, button { font-size: 0.95rem; }
  input[type="text"], select { width: 100%; padding: 0.42rem var(--space-1); box-sizing: border-box; min-height: 2.2rem; }
  button { padding: 0.42rem 0.7rem; min-height: 2.2rem; }
  .row {
    display: grid;
    grid-template-columns: minmax(220px, 1.2fr) minmax(180px, 0.9fr) minmax(260px, 1.5fr) auto;
    gap: var(--gap);
    align-items: center;
  }
  .list { display: grid; gap: 0.5rem; margin-top: 1rem; }
  .card { border: 1px solid #e5e5e5; border-radius: var(--radius-1); padding: 0.6rem 0.7rem; background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }
  .file-col { display: grid; gap: 0.3rem; }
  .select-line { white-space: nowrap; }
  .filename-input { font-weight: 600; }
  .file-path { font-size: 0.82rem; }
  .field-group { display: grid; gap: 0.2rem; }
  .inline-row { display: flex; gap: 0.4rem; align-items: center; }
  .inline-row > * { flex: 1 1 auto; }
  .muted { color: #666; font-size: 0.9rem; }
  .actions { display: flex; gap: 0.5rem; align-items: center; }
  .ok { color: #0a6; font-size: 0.9rem; }
  .bulk-panel { border: 1px solid #ddd; border-radius: var(--radius-1); padding: 0.75rem; background: #fff; margin-top: 0.6rem; }
  .bulk-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0.6rem; align-items: end; }
  .bulk-row { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem; }
  .bulk-actions { display: flex; justify-content: flex-end; }
  .bulk-field { display: grid; gap: 0.3rem; }
  .bulk-tag-mode { margin-top: 0.2rem; margin-bottom: 0; }
  .tag-editor { border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.35rem 0.45rem; background: #fbfdff; }
  .tag-editor summary { cursor: pointer; user-select: none; }
  .tag-editor[open] summary { margin-bottom: 0.35rem; }
  .tag-chips { display: flex; flex-wrap: wrap; gap: 0.35rem; min-height: 1.5rem; align-items: center; }
  .tag-chip { border: 1px solid #bbb; background: #f7f7f7; border-radius: 999px; padding: 0.15rem 0.55rem; cursor: pointer; }
  .tag-chip:hover { background: #eee; }
  @media (max-width: 1100px) {
    .row { grid-template-columns: 1fr 1fr; }
    .actions { grid-column: 1 / -1; }
    .bulk-grid { grid-template-columns: 1fr; }
    .bulk-actions { justify-content: flex-start; }
  }
  @media (max-width: 760px) {
    body { padding: var(--space-3); }
    .row { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
<div class="container">
  <h1>Markdown メタ編集</h1>
  <div class="topnav">
    <a href="/kb" target="_blank" rel="noopener">Markdown一覧を開く</a>
    <a href="/import" target="_blank" rel="noopener">テキスト取込を開く</a>
  </div>
  <div class="toolbar">
    <input id="search" type="search" placeholder="検索: ファイル名 / カテゴリ / タグ" />
    <button type="button" id="reload">再読み込み</button>
  </div>
  <div class="toolbar">
    <label><input type="checkbox" id="filterCategoryMissing"> category未設定のみ</label>
    <label><input type="checkbox" id="filterTagsMissing"> tags未設定のみ</label>
    <label><input type="checkbox" id="filterEitherMissing"> どちらか未設定</label>
  </div>
  <div class="bulk-panel">
    <div class="bulk-row">
      <label><input type="checkbox" id="selectAllVisible"> 表示中を全選択</label>
      <span class="muted" id="selectedInfo">選択: 0 件</span>
    </div>
    <div class="bulk-grid">
      <div class="bulk-field">
        <label class="muted">一括カテゴリ</label>
        <select id="bulkCategorySelect"></select>
        <input type="text" id="bulkCategoryCustom" placeholder="カテゴリを自由入力">
      </div>
      <div class="bulk-field">
        <label class="muted">一括タグ（カンマ区切り）</label>
        <input type="text" id="bulkTagsInput" list="tagOptions" placeholder="例: 手順,運用,TODO_確認">
        <div class="bulk-row bulk-tag-mode">
          <label><input type="radio" name="bulkTagMode" value="append" checked> 既存へ追加</label>
          <label><input type="radio" name="bulkTagMode" value="replace"> 置換</label>
        </div>
      </div>
      <div class="bulk-actions">
        <button type="button" id="bulkApply">一括適用</button>
      </div>
    </div>
  </div>
  <datalist id="tagOptions"></datalist>
  <div class="list" id="list"></div>
  <p class="muted">保存後に静的HTMLを更新するには `python build.py` を実行してください。</p>
</div>

<script>
  const listEl = document.getElementById('list');
  const searchEl = document.getElementById('search');
  const reloadBtn = document.getElementById('reload');
  const filterCategoryMissingEl = document.getElementById('filterCategoryMissing');
  const filterTagsMissingEl = document.getElementById('filterTagsMissing');
  const filterEitherMissingEl = document.getElementById('filterEitherMissing');
  const selectAllVisibleEl = document.getElementById('selectAllVisible');
  const selectedInfoEl = document.getElementById('selectedInfo');
  const bulkCategorySelectEl = document.getElementById('bulkCategorySelect');
  const bulkCategoryCustomEl = document.getElementById('bulkCategoryCustom');
  const bulkTagsInputEl = document.getElementById('bulkTagsInput');
  const bulkApplyEl = document.getElementById('bulkApply');
  const tagOptionsEl = document.getElementById('tagOptions');
  let items = [];
  let categoryOptions = [];
  let tagOptions = [];
  const selectedFiles = new Set();

  function normalize(v) { return (v || '').toLowerCase(); }

  function uniqueSorted(values) {
    return Array.from(new Set(values.filter(Boolean))).sort((a, b) => a.localeCompare(b, 'ja'));
  }

  function renderOptionList(el, values) {
    el.innerHTML = values.map(v => `<option value="${v}"></option>`).join('');
  }

  function renderCategorySelectOptions() {
    const options = categoryOptions.map(c => `<option value="${c}">${c}</option>`).join('');
    bulkCategorySelectEl.innerHTML = options;
    if (categoryOptions.length > 0) {
      bulkCategorySelectEl.value = categoryOptions[0];
      if (!bulkCategoryCustomEl.value.trim()) {
        bulkCategoryCustomEl.value = categoryOptions[0];
      }
    }
  }

  function updateSelectedInfo(visibleFiles) {
    selectedInfoEl.textContent = `選択: ${selectedFiles.size} 件`;
    const allVisibleSelected = visibleFiles.length > 0 && visibleFiles.every(f => selectedFiles.has(f));
    selectAllVisibleEl.checked = allVisibleSelected;
  }

  function splitCsvTags(rawText) {
    return (rawText || '')
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)
      .filter((t, idx, arr) => arr.indexOf(t) === idx);
  }

  function render() {
    const q = normalize(searchEl.value);
    listEl.innerHTML = '';
    const visibleItems = items
      .filter(i => {
        if (!q) return true;
        return normalize(i.file).includes(q)
          || normalize(i.category).includes(q)
          || normalize(i.tags.join(',')).includes(q);
      })
      .filter(i => {
        const byCategoryMissing = !filterCategoryMissingEl.checked || i.category_missing;
        const byTagsMissing = !filterTagsMissingEl.checked || i.tags_missing;
        const byEitherMissing = !filterEitherMissingEl.checked || (i.category_missing || i.tags_missing);
        return byCategoryMissing && byTagsMissing && byEitherMissing;
      });

    visibleItems.forEach(i => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
          <div class="row">
            <div class="file-col">
              <label class="muted select-line"><input type="checkbox" class="row-select" ${selectedFiles.has(i.file) ? 'checked' : ''}> 選択</label>
              <input type="text" class="filename-input" value="${i.file}" aria-label="ファイル名">
              <div class="muted file-path">${i.path}</div>
            </div>
            <div class="field-group">
              <label class="muted">カテゴリ</label>
              <div class="inline-row">
                <select class="category-select">
                  ${categoryOptions.map(c => `<option value="${c}" ${c === i.category ? 'selected' : ''}>${c}</option>`).join('')}
                </select>
                <input type="text" class="category-custom" value="${i.category}" placeholder="カテゴリを自由入力">
              </div>
            </div>
            <div class="field-group">
              <details class="tag-editor">
                <summary class="muted">タグ編集（<span class="tag-count">${(i.tags || []).length}</span>）</summary>
                <div class="tag-chips"></div>
                <div class="inline-row">
                  <input type="text" class="tag-input" list="tagOptions" placeholder="タグを入力して追加">
                  <button type="button" class="add-tag-input">追加</button>
                </div>
                <div class="inline-row">
                  <select class="tag-select">
                    <option value="">既存タグを選択</option>
                    ${tagOptions.map(t => `<option value="${t}">${t}</option>`).join('')}
                  </select>
                  <button type="button" class="add-tag-select">追加</button>
                </div>
              </details>
            </div>
            <div class="actions">
              <button type="button" class="save-btn">保存</button>
              <span class="ok" style="display:none;">保存済み</span>
            </div>
          </div>
        `;
        const categorySelect = card.querySelector('.category-select');
        const categoryCustom = card.querySelector('.category-custom');
        const rowSelect = card.querySelector('.row-select');
        const filenameInput = card.querySelector('.filename-input');
        const filePathEl = card.querySelector('.file-path');
        const saveBtn = card.querySelector('.save-btn');
        const chipsEl = card.querySelector('.tag-chips');
        const tagCountEl = card.querySelector('.tag-count');
        const tagInput = card.querySelector('.tag-input');
        const addTagInputBtn = card.querySelector('.add-tag-input');
        const tagSelect = card.querySelector('.tag-select');
        const addTagSelectBtn = card.querySelector('.add-tag-select');
        const ok = card.querySelector('.ok');
        let tagsState = Array.isArray(i.tags) ? [...i.tags] : [];

        categorySelect.addEventListener('change', () => {
          const selectedCategory = (categorySelect.value || '').trim();
          if (selectedCategory) {
            categoryCustom.value = selectedCategory;
          }
        });

        rowSelect.addEventListener('change', () => {
          if (rowSelect.checked) {
            selectedFiles.add(i.file);
          } else {
            selectedFiles.delete(i.file);
          }
          updateSelectedInfo(visibleItems.map(v => v.file));
        });

        function renderTagChips() {
          chipsEl.innerHTML = '';
          if (tagsState.length === 0) {
            const empty = document.createElement('span');
            empty.className = 'muted';
            empty.textContent = 'タグなし';
            chipsEl.appendChild(empty);
            if (tagCountEl) tagCountEl.textContent = '0';
            return;
          }
          if (tagCountEl) tagCountEl.textContent = String(tagsState.length);
          tagsState.forEach((tag) => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'tag-chip';
            chip.dataset.tag = tag;
            chip.title = 'クリックで削除';
            chip.textContent = '#' + tag + ' ×';
            chipsEl.appendChild(chip);
          });
        }

        function addTag(rawTag) {
          const tag = (rawTag || '').trim();
          if (!tag) return;
          if (tagsState.includes(tag)) return;
          tagsState.push(tag);
          renderTagChips();
        }

        chipsEl.addEventListener('click', (event) => {
          const target = event.target;
          if (!(target instanceof HTMLElement)) return;
          const tag = target.dataset.tag;
          if (!tag) return;
          tagsState = tagsState.filter((t) => t !== tag);
          renderTagChips();
        });

        addTagInputBtn.addEventListener('click', () => {
          addTag(tagInput.value);
          tagInput.value = '';
        });

        tagInput.addEventListener('keydown', (event) => {
          if (event.key !== 'Enter') return;
          event.preventDefault();
          addTag(tagInput.value);
          tagInput.value = '';
        });

        addTagSelectBtn.addEventListener('click', () => {
          addTag(tagSelect.value);
        });

        renderTagChips();

        saveBtn.addEventListener('click', async () => {
          const oldFile = i.file;
          const newFile = (filenameInput?.value || '').trim() || oldFile;
          const category = categoryCustom.value.trim() || categorySelect.value.trim() || '未分類';
          const tags = [...tagsState];
          saveBtn.disabled = true;
          const res = await fetch('/api/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file: oldFile, new_file: newFile, category, tags })
          });
          saveBtn.disabled = false;
          if (res.ok) {
            const result = await res.json();
            ok.style.display = 'inline';
            setTimeout(() => ok.style.display = 'none', 1200);
            if (result.file && result.file !== oldFile) {
              if (selectedFiles.has(oldFile)) {
                selectedFiles.delete(oldFile);
                selectedFiles.add(result.file);
              }
              i.file = result.file;
              i.path = result.path || `md\\${result.file}`;
              if (filenameInput) filenameInput.value = result.file;
              if (filePathEl) filePathEl.textContent = i.path;
            }
            i.category = category;
            i.tags = tags;
            i.category_missing = category.trim() === '' || category === '未分類';
            i.tags_missing = tags.length === 0;
          } else {
            let err = '保存に失敗しました';
            try {
              const payload = await res.json();
              if (payload && payload.error) err = `保存に失敗しました: ${payload.error}`;
            } catch (_) {}
            alert(err);
          }
        });
        listEl.appendChild(card);
      });
    updateSelectedInfo(visibleItems.map(v => v.file));
  }

  async function load() {
    const res = await fetch('/api/items');
    items = await res.json();
    categoryOptions = uniqueSorted(items.map(i => (i.category || '').trim()));
    tagOptions = uniqueSorted(items.flatMap(i => (i.tags || []).map(t => (t || '').trim())));
    renderCategorySelectOptions();
    renderOptionList(tagOptionsEl, tagOptions);
    render();
  }

  bulkCategorySelectEl.addEventListener('change', () => {
    const selectedCategory = (bulkCategorySelectEl.value || '').trim();
    if (selectedCategory) {
      bulkCategoryCustomEl.value = selectedCategory;
    }
  });

  selectAllVisibleEl.addEventListener('change', () => {
    const q = normalize(searchEl.value);
    const visibleFiles = items
      .filter(i => {
        if (!q) return true;
        return normalize(i.file).includes(q)
          || normalize(i.category).includes(q)
          || normalize(i.tags.join(',')).includes(q);
      })
      .filter(i => {
        const byCategoryMissing = !filterCategoryMissingEl.checked || i.category_missing;
        const byTagsMissing = !filterTagsMissingEl.checked || i.tags_missing;
        const byEitherMissing = !filterEitherMissingEl.checked || (i.category_missing || i.tags_missing);
        return byCategoryMissing && byTagsMissing && byEitherMissing;
      })
      .map(i => i.file);
    if (selectAllVisibleEl.checked) {
      visibleFiles.forEach(f => selectedFiles.add(f));
    } else {
      visibleFiles.forEach(f => selectedFiles.delete(f));
    }
    render();
  });

  bulkApplyEl.addEventListener('click', async () => {
    if (selectedFiles.size === 0) {
      alert('一括適用するファイルを選択してください。');
      return;
    }
    const category = bulkCategoryCustomEl.value.trim() || bulkCategorySelectEl.value.trim() || '未分類';
    const tags = splitCsvTags(bulkTagsInputEl.value);
    const modeEl = document.querySelector('input[name="bulkTagMode"]:checked');
    const tagMode = modeEl ? modeEl.value : 'append';

    bulkApplyEl.disabled = true;
    const res = await fetch('/api/bulk_update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        files: Array.from(selectedFiles),
        category: category,
        tags: tags,
        tag_mode: tagMode
      })
    });
    bulkApplyEl.disabled = false;
    if (!res.ok) {
      alert('一括適用に失敗しました。');
      return;
    }
    const result = await res.json();
    if (Array.isArray(result.failed) && result.failed.length > 0) {
      alert(`一括適用完了: ${result.updated}件更新 / 失敗: ${result.failed.length}件`);
    } else {
      alert(`一括適用完了: ${result.updated}件更新`);
    }
    await load();
  });

  searchEl.addEventListener('input', render);
  filterCategoryMissingEl.addEventListener('change', render);
  filterTagsMissingEl.addEventListener('change', render);
  filterEitherMissingEl.addEventListener('change', render);
  reloadBtn.addEventListener('click', load);
  load();
</script>
</body>
</html>
"""


@app.get("/kb")
def kb():
    index_path = HTML_DIR / "index.html"
    if not index_path.exists():
        return """<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><title>KB未生成</title></head>
<body>
<h1>html/index.html が見つかりません</h1>
<p>先に <code>python build.py</code> を実行してください。</p>
<p><a href="/">メタ編集へ戻る</a></p>
</body></html>""", 404
    return send_file(index_path.resolve())


@app.route("/import", methods=["GET", "POST"])
def import_text():
    title = ""
    category = ""
    tags_raw = ""
    body = ""
    message = ""
    error = ""
    build_msg = ""

    categories, tags = collect_meta_options()
    if "未分類" not in categories:
        categories.append("未分類")
    category_options_html = "".join(
        f'<option value="{escape(c)}">{escape(c)}</option>' for c in categories
    )
    tag_options_html = "".join(
        f'<option value="{escape(t)}"></option>' for t in tags
    )

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        category_text = (request.form.get("category") or "").strip()
        category_select = (request.form.get("category_select") or "").strip()
        category = category_text or category_select
        tags_raw = (request.form.get("tags") or "").strip()
        body = (request.form.get("body") or "").strip()
        action = (request.form.get("action") or "save").strip()

        if not title:
            error = "タイトルは必須です。"
        elif not body:
            error = "本文は必須です。"
        else:
            safe_stem = sanitize_file_stem(title)
            md_path = make_unique_md_path(safe_stem)
            tags = parse_csv_tags(tags_raw)
            fm = build_front_matter(category or "未分類", tags)
            md_path.write_text(fm + "\n" + body + "\n", encoding="utf-8")
            message = f"保存しました: {md_path.name}"

            if action == "save_build":
                result = subprocess.run(
                    ["python", "build.py"],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).resolve().parent,
                )
                if result.returncode == 0:
                    build_msg = "build.py 実行成功（html/index.html を更新）"
                else:
                    error = "保存は成功しましたが build.py 実行に失敗しました。"
                    build_msg = (result.stderr or result.stdout).strip()[:600]

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>テキスト取込</title>
<style>
  :root {{
    --max: 1120px;
    --space-1: 0.5rem;
    --space-2: 0.75rem;
    --space-3: 1rem;
    --space-4: 1.5rem;
    --radius-1: 10px;
  }}
  body {{ font-family: system-ui, sans-serif; padding: var(--space-4); background: #ffffff; margin: 0; line-height: 1.6; color: #0f172a; }}
  .container {{ max-width: var(--max); margin: 0 auto; background: transparent; border: 0; border-radius: 0; padding: 0; }}
  h1 {{ margin: 0 0 0.6rem; }}
  .topnav {{ display: flex; flex-wrap: wrap; gap: 0.8rem; margin-bottom: 0.8rem; }}
  .topnav a {{ color: #0f4c81; text-decoration: none; border-bottom: 1px solid #0f4c81; }}
  .topnav a:hover {{ opacity: 0.85; }}
  .grid {{ display: grid; gap: 0.7rem; padding: var(--space-3); border: 1px solid #e2e8f0; border-radius: var(--radius-1); background: #fbfdff; }}
  label {{ display: grid; gap: 0.3rem; }}
  .inline-row {{ display: flex; gap: 0.5rem; align-items: center; }}
  .inline-row > * {{ flex: 1 1 auto; }}
  input[type="text"], textarea {{ width: 100%; padding: var(--space-1); box-sizing: border-box; font-size: 0.95rem; border: 1px solid #d9e2ec; border-radius: 8px; background: #f8fafc; }}
  select {{ width: 100%; padding: var(--space-1); box-sizing: border-box; font-size: 0.95rem; min-height: 2.2rem; border: 1px solid #d9e2ec; border-radius: 8px; background: #f8fafc; }}
  textarea {{ min-height: 360px; resize: vertical; background: #f4f7fb; }}
  input[type="text"]:focus, select:focus, textarea:focus {{ outline: 2px solid #93c5fd; outline-offset: 0; border-color: #93c5fd; background: #ffffff; }}
  .actions {{ display: flex; gap: 0.6rem; margin-top: 0.6rem; }}
  button {{ padding: 0.5rem 0.8rem; font-size: 0.95rem; min-height: 2.2rem; border: 1px solid #cbd5e1; border-radius: 8px; background: #ffffff; }}
  .ok {{ color: #047857; }}
  .err {{ color: #b91c1c; }}
  .status {{ min-height: 5.2rem; margin-top: 0.7rem; padding: 0.6rem 0.75rem; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; }}
  .status p {{ margin: 0.2rem 0; }}
  .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; white-space: pre-wrap; min-height: 2.2rem; }}
  @media (max-width: 760px) {{
    body {{ padding: var(--space-3); }}
    .actions {{ flex-wrap: wrap; }}
  }}
</style>
</head>
<body>
  <div class="container">
    <h1>プレーンテキスト取込</h1>
    <div class="topnav">
      <a href="/kb" target="_blank" rel="noopener">Markdown一覧を開く</a>
      <a href="/" target="_blank" rel="noopener">メタ編集を開く</a>
    </div>
    <form method="post" class="grid">
      <label>タイトル（必須）<input type="text" name="title" value="{escape(title)}" required></label>
      <label>カテゴリ候補
        <select name="category_select" id="categorySelect">
          <option value="">候補から選択（任意）</option>
          {category_options_html}
        </select>
      </label>
      <label>カテゴリ（任意）<input type="text" name="category" id="categoryInput" value="{escape(category)}" placeholder="未入力時は 未分類"></label>
      <label>タグ（任意・カンマ区切り）
        <input type="text" name="tags" id="tagsInput" list="tagOptionsImport" value="{escape(tags_raw)}" placeholder="例: 手順,運用">
        <datalist id="tagOptionsImport">
          {tag_options_html}
        </datalist>
      </label>
      <div class="inline-row">
        <select id="tagSelect">
          <option value="">既存タグを選択</option>
          {"".join(f'<option value="{escape(t)}">{escape(t)}</option>' for t in tags)}
        </select>
        <button type="button" id="addTagBtn">タグ追加</button>
      </div>
      <label>本文（必須）<textarea name="body" required>{escape(body)}</textarea></label>
      <div class="actions">
        <button type="submit" name="action" value="save">保存</button>
        <button type="submit" name="action" value="save_build">保存してビルド</button>
        <button type="reset">入力クリア</button>
      </div>
    </form>
    <div class="status">
      <p class="ok">{escape(message)}</p>
      <p class="err">{escape(error)}</p>
      <p class="mono">{escape(build_msg)}</p>
    </div>
  </div>
  <script>
    const categorySelect = document.getElementById('categorySelect');
    const categoryInput = document.getElementById('categoryInput');
    const tagsInput = document.getElementById('tagsInput');
    const tagSelect = document.getElementById('tagSelect');
    const addTagBtn = document.getElementById('addTagBtn');

    if (categorySelect && categoryInput) {{
      categorySelect.addEventListener('change', () => {{
        const selected = (categorySelect.value || '').trim();
        if (selected) categoryInput.value = selected;
      }});
    }}

    function addTagToInput(rawTag) {{
      const tag = (rawTag || '').trim();
      if (!tag || !tagsInput) return;
      const current = (tagsInput.value || '')
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);
      if (current.includes(tag)) return;
      current.push(tag);
      tagsInput.value = current.join(',');
    }}

    if (addTagBtn && tagSelect) {{
      addTagBtn.addEventListener('click', () => {{
        addTagToInput(tagSelect.value);
      }});
    }}
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
        tags = normalize_tags(fm.get("tags") or [])
        out.append({
            "file": md_path.name,
            "path": str(md_path),
            "category": category,
            "tags": tags,
            "category_missing": category.strip() == "" or category == "未分類",
            "tags_missing": len(tags) == 0,
        })
    return jsonify(out)


@app.post("/api/update")
def update():
    data = request.get_json(force=True)
    file_name = data.get("file", "")
    new_file_name = data.get("new_file", "")
    category = data.get("category", "未分類")
    tags = normalize_tags(data.get("tags", []))

    md_path = resolve_md_path(file_name)
    if md_path is None:
        return jsonify({"error": "invalid file"}), 400

    normalized_new = normalize_md_filename(str(new_file_name)) if str(new_file_name).strip() else md_path.name
    if not normalized_new:
        return jsonify({"error": "invalid new file name"}), 400
    target_path = (MD_DIR / normalized_new).resolve()
    if target_path.parent != MD_DIR.resolve() or target_path.suffix.lower() != ".md":
        return jsonify({"error": "invalid new file path"}), 400
    if target_path != md_path and target_path.exists():
        return jsonify({"error": "file already exists"}), 409
    if target_path != md_path:
        md_path.rename(target_path)
        md_path = target_path

    update_md_file(md_path, category, [str(t) for t in tags])
    return jsonify({"ok": True, "file": md_path.name, "path": str(md_path)})


@app.post("/api/bulk_update")
def bulk_update():
    data = request.get_json(force=True)
    files = data.get("files", [])
    category = str(data.get("category", "未分類")).strip() or "未分類"
    tags = normalize_tags(data.get("tags", []))
    tag_mode = str(data.get("tag_mode", "append")).strip().lower()

    if not isinstance(files, list) or not files:
        return jsonify({"error": "no files selected"}), 400
    if tag_mode not in {"append", "replace"}:
        return jsonify({"error": "invalid tag_mode"}), 400

    updated = 0
    failed: list[str] = []
    for file_name in files:
        md_path = resolve_md_path(str(file_name))
        if md_path is None:
            failed.append(str(file_name))
            continue
        text = md_path.read_text(encoding="utf-8")
        fm, _ = parse_front_matter(text)
        current_tags = normalize_tags(fm.get("tags") or [])
        if tag_mode == "replace":
            final_tags = tags
        else:
            final_tags = current_tags[:]
            for t in tags:
                if t not in final_tags:
                    final_tags.append(t)

        update_md_file(md_path, category, final_tags)
        updated += 1

    return jsonify({
        "ok": True,
        "updated": updated,
        "failed": failed,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
