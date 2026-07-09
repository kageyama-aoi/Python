"""md/・html/ ディレクトリ配下の Markdown ファイル操作の共通モジュール。

MD_DIR / HTML_DIR の定義もここに一本化する（実行時カレントは 40_ 直下を前提）。
"""
from pathlib import Path
import re
from datetime import datetime

from frontmatter import build_front_matter, normalize_tags, parse_front_matter

MD_DIR = Path("md")
HTML_DIR = Path("html")


def update_md_file(md_path: Path, category: str, tags: list[str]) -> None:
    text = md_path.read_text(encoding="utf-8")
    _, body = parse_front_matter(text)
    fm = build_front_matter(category, tags)
    md_path.write_text(fm + "\n" + body.lstrip("\n"), encoding="utf-8")


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
