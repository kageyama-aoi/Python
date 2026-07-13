from pathlib import Path
import logging
import subprocess
import sys
import os

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
)

from frontmatter import (
    build_front_matter,
    normalize_tags,
    parse_csv_tags,
    parse_front_matter,
)
from md_store import (
    HTML_DIR,
    MD_DIR,
    collect_meta_options,
    make_unique_md_path,
    normalize_md_filename,
    resolve_md_path,
    sanitize_file_stem,
    update_md_file,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__)


@app.get("/")
@app.get("/meta")
def index():
    return render_template("meta_editor.html")


@app.get("/kb")
def kb_redirect():
    return redirect("/kb/", code=302)


@app.get("/kb/")
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


@app.get("/kb/<path:filename>")
def kb_asset(filename: str):
    safe_root = HTML_DIR.resolve()
    target = (safe_root / filename).resolve()
    allowed_suffixes = {".html", ".css"}
    if target.parent != safe_root or not target.exists() or target.suffix.lower() not in allowed_suffixes:
        return "Not Found", 404
    return send_from_directory(safe_root, filename)


@app.get("/picture/<path:filename>")
def picture_asset(filename: str):
    safe_root = Path("picture").resolve()
    target = (safe_root / filename).resolve()
    if target.parent != safe_root or not target.exists():
        return "Not Found", 404
    return send_from_directory(safe_root, filename)


@app.route("/import", methods=["GET", "POST"])
def import_text():
    title = ""
    category = ""
    tags_raw = ""
    body = ""
    message = ""
    error = ""
    build_msg = ""

    categories, all_tags = collect_meta_options()
    if "未分類" not in categories:
        categories.append("未分類")

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
            input_tags = parse_csv_tags(tags_raw)
            fm = build_front_matter(category or "未分類", input_tags)
            md_path.write_text(fm + "\n" + body + "\n", encoding="utf-8")
            message = f"保存しました: {md_path.name}"

            if action == "save_build":
                result = subprocess.run(
                    [sys.executable, "-X", "utf8", "build.py"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=Path(__file__).resolve().parent,
                )
                if result.returncode == 0:
                    build_msg = "build.py 実行成功（html/index.html を更新）"
                else:
                    error = "保存は成功しましたが build.py 実行に失敗しました。"
                    build_msg = (result.stderr or result.stdout).strip()[:600]

    return render_template(
        "import.html",
        title=title,
        category=category,
        tags_raw=tags_raw,
        body=body,
        message=message,
        error=error,
        build_msg=build_msg,
        categories=categories,
        all_tags=all_tags,
    )


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
        app.logger.warning("update 失敗: 対象ファイル不正 file=%s", file_name)
        return jsonify({"error": "invalid file"}), 400

    normalized_new = normalize_md_filename(str(new_file_name)) if str(new_file_name).strip() else md_path.name
    if not normalized_new:
        app.logger.warning("update 失敗: 新ファイル名不正 file=%s new_file=%s", file_name, new_file_name)
        return jsonify({"error": "invalid new file name"}), 400
    target_path = (MD_DIR / normalized_new).resolve()
    if target_path.parent != MD_DIR.resolve() or target_path.suffix.lower() != ".md":
        app.logger.warning("update 失敗: 新ファイルパス不正 file=%s new_file=%s", file_name, new_file_name)
        return jsonify({"error": "invalid new file path"}), 400
    if target_path != md_path and target_path.exists():
        app.logger.warning("update 失敗: リネーム先が既存 file=%s new_file=%s", file_name, normalized_new)
        return jsonify({"error": "file already exists"}), 409
    if target_path != md_path:
        md_path.rename(target_path)
        md_path = target_path

    update_md_file(md_path, category, [str(t) for t in tags])
    app.logger.info(
        "update 完了: file=%s -> %s category=%s tags=%d件", file_name, md_path.name, category, len(tags)
    )
    return jsonify({"ok": True, "file": md_path.name, "path": str(md_path)})


@app.post("/api/bulk_update")
def bulk_update():
    data = request.get_json(force=True)
    files = data.get("files", [])
    category = str(data.get("category", "未分類")).strip() or "未分類"
    tags = normalize_tags(data.get("tags", []))
    tag_mode = str(data.get("tag_mode", "append")).strip().lower()

    if not isinstance(files, list) or not files:
        app.logger.warning("bulk_update 失敗: 対象ファイル未選択")
        return jsonify({"error": "no files selected"}), 400
    if tag_mode not in {"append", "replace"}:
        app.logger.warning("bulk_update 失敗: tag_mode不正 tag_mode=%s", tag_mode)
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

    app.logger.info(
        "bulk_update 完了: 対象=%d件 更新=%d件 失敗=%d件 category=%s tags=%d件 tag_mode=%s",
        len(files), updated, len(failed), category, len(tags), tag_mode,
    )
    if failed:
        app.logger.warning("bulk_update 失敗ファイル: %s", ", ".join(failed))

    return jsonify({
        "ok": True,
        "updated": updated,
        "failed": failed,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
