"""
show_tree.py
────────────
指定フォルダのディレクトリ構成をツリー表示する。
script_launcher.py のログエリアに出力して Claude に貼り付けて共有するのに便利。

使い方:
  python show_tree.py [ルートパス] [オプション]

オプション:
  --depth  N        表示する階層の深さ（デフォルト: 4）
  --all            隠しファイル（.で始まるもの）も表示
  --ext    .py .md  指定拡張子のファイルだけ表示（複数指定可）
  --ignore node_modules .git  除外フォルダ名（複数指定可）

例:
  python show_tree.py C:/Users/me/projects --depth 3 --ignore node_modules .git __pycache__
"""

import os
import sys
import argparse
from datetime import datetime

# ============================================================
# デフォルト設定（引数なしで実行したときに使われる）
# ============================================================
DEFAULT_ROOT   = "."            # 起点ディレクトリ（"." = このスクリプトと同じ場所）
DEFAULT_DEPTH  = 4              # 表示階層数
DEFAULT_IGNORE = {              # 常に除外するフォルダ・ファイル名
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", "dist", "build", ".DS_Store",
}
# ============================================================

PIPE  = "│   "
TEE   = "├── "
LAST  = "└── "
BLANK = "    "


def build_tree(root, max_depth, show_hidden, ext_filter, ignore_set):
    lines = []
    abs_root = os.path.abspath(root)
    lines.append(abs_root)

    def _walk(path, prefix, depth):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            lines.append(prefix + LAST + "[アクセス不可]")
            return

        # フィルタリング
        entries = [
            e for e in entries
            if e.name not in ignore_set
            and (show_hidden or not e.name.startswith("."))
            and (not ext_filter or e.is_dir() or os.path.splitext(e.name)[1] in ext_filter)
        ]

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = LAST if is_last else TEE
            suffix = "/" if entry.is_dir() else ""
            lines.append(prefix + connector + entry.name + suffix)

            if entry.is_dir():
                extension = BLANK if is_last else PIPE
                _walk(entry.path, prefix + extension, depth + 1)

    _walk(abs_root, "", 1)
    return lines


def main():
    parser = argparse.ArgumentParser(description="ディレクトリツリーを表示する")
    parser.add_argument("root", nargs="?", default=DEFAULT_ROOT, help="起点ディレクトリ")
    parser.add_argument("--depth",  type=int, default=DEFAULT_DEPTH, help="表示階層数")
    parser.add_argument("--all",    action="store_true", help="隠しファイルも表示")
    parser.add_argument("--ext",    nargs="*", default=[], help="拡張子フィルタ（例: .py .md）")
    parser.add_argument("--ignore", nargs="*", default=[], help="除外するフォルダ・ファイル名")
    args = parser.parse_args()

    root = args.root
    if not os.path.isdir(root):
        print(f"[ERROR] ディレクトリが見つかりません: {root}", file=sys.stderr)
        sys.exit(1)

    ignore_set = DEFAULT_IGNORE | set(args.ignore)
    ext_filter = set(args.ext) if args.ext else None

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"# Directory Tree  ({ts})")
    print(f"# depth={args.depth}  hidden={'ON' if args.all else 'OFF'}  "
          f"ext={list(ext_filter) if ext_filter else 'ALL'}  "
          f"ignore={sorted(ignore_set)}")
    print()

    lines = build_tree(root, args.depth, args.all, ext_filter, ignore_set)
    for line in lines:
        print(line)

    # サマリー
    dirs  = sum(1 for l in lines[1:] if l.rstrip().endswith("/"))
    files = sum(1 for l in lines[1:] if not l.rstrip().endswith("/") and ("├" in l or "└" in l))
    print()
    print(f"# {dirs} directories, {files} files (depth≤{args.depth})")


if __name__ == "__main__":
    main()
