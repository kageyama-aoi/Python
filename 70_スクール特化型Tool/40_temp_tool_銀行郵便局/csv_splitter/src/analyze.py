"""入力ファイルの事前解析ヘルパー（エンコード判定・行数カウント・先頭行プレビュー等）。

GUI から使う純粋なロジック層。tkinter に依存しない。
"""
import csv
from pathlib import Path


def _detect_encoding_from_file(path: Path) -> str:
    with open(path, "rb") as f:
        raw = f.read(4)
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return "utf-16"
    for enc in ("utf-8", "shift_jis", "cp932"):
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                f.read(65536)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "不明"


def _count_rows(path: Path) -> int:
    count = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            count += chunk.count(b"\n")
    return count


def _fmt_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _read_first_row(path: Path, enc: str, delim: str) -> tuple[int, str]:
    try:
        with open(path, "r", encoding=enc, newline="") as f:
            reader = csv.reader(f, delimiter=delim)
            row = next(reader, [])
        col_count = len(row)
        preview = ", ".join(str(v) for v in row[:8])
        if len(row) > 8:
            preview += f" ... (+{len(row) - 8}列)"
        return col_count, preview
    except (OSError, UnicodeDecodeError, LookupError, csv.Error):
        return 0, "(読み取り失敗)"


def _suggest_rows(total_rows: int) -> str:
    if total_rows <= 0:
        return "不明"
    per_file = max(1000, total_rows // 10)
    if per_file >= 10000:
        per_file = round(per_file / 10000) * 10000
    elif per_file >= 1000:
        per_file = round(per_file / 1000) * 1000
    return f"{per_file:,} 行（全体を約10ファイルに分割）"
