"""Markdown フロントマターの解析・生成・タグ正規化の共通モジュール。

app.py（メタ編集・取込GUI）と build.py（HTML一括生成）の両方から使う。
ここが parse_front_matter の唯一の実装（重複配置しないこと）。
"""
import re

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


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


def build_front_matter(category: str, tags: list[str]) -> str:
    lines = ["---", f"category: {category}", "tags:"]
    for t in tags:
        lines.append(f"  - {t}")
    lines.append("---")
    return "\n".join(lines) + "\n"


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


def parse_csv_tags(raw_text: str) -> list[str]:
    tags: list[str] = []
    for part in raw_text.split(","):
        tag = part.strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags
