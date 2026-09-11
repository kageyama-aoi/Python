#!/usr/bin/env python3
"""各ツールの pytest を「ツールごとに独立したプロセス」で実行して集計する。

このリポジトリはツールが 1 つずつ独立しており（`src/` を `sys.path` に足す
`tests/conftest.py`、`config` 等の同名モジュール、`test_main.py` の重複、
`11_` を外すと数字始まりで壊れるフォルダ名）、リポジトリルートで
`python -m pytest` を一発実行すると collection 段階で衝突・異常終了する。

各ツールの流儀（`cd <tool> && python -m pytest tests/`）をそのまま
サブプロセスで回し、結果だけを集める。

使い方:
    python scripts/run_all_tests.py             # 全ツールを実行、1つでも失敗で exit 1
    python scripts/run_all_tests.py --warn-only # 失敗しても exit 0（フックの警告用）
    python scripts/run_all_tests.py --list      # 対象ツールを列挙するだけ
    python scripts/run_all_tests.py -k NAME     # tests/ の親フォルダ名で対象を絞る（部分一致）

pytest の終了コード: 0=全通過 / 1=失敗あり / 5=テスト0件(=スキップ扱い) / その他=異常。
標準ライブラリのみ。Python 3.10+。
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PER_TOOL_TIMEOUT = 600  # 秒

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "_archive",
}

# pytest 終了コード（https://docs.pytest.org/en/stable/reference/exit-codes.html）
EXIT_OK = 0
EXIT_TESTS_FAILED = 1
EXIT_NO_TESTS = 5


def find_test_dirs(root: Path) -> list[Path]:
    """`tests/` ディレクトリを持つフォルダ（＝テスト対象ユニット）を集める。"""
    units: list[Path] = []
    for tests_dir in root.rglob("tests"):
        if not tests_dir.is_dir():
            continue
        parts = set(tests_dir.relative_to(root).parts)
        if parts & EXCLUDE_DIRS:
            continue
        if not any(tests_dir.glob("test_*.py")):
            continue
        units.append(tests_dir.parent)
    return sorted(set(units))


def run_one(unit: Path) -> tuple[int, float, str]:
    """1 ユニットで pytest を実行し (終了コード, 所要秒, 末尾出力) を返す。"""
    start = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
            cwd=unit,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PER_TOOL_TIMEOUT,
            env=_child_env(),
        )
        elapsed = time.monotonic() - start
        tail = _last_line(proc.stdout) or _last_line(proc.stderr)
        return proc.returncode, elapsed, tail
    except subprocess.TimeoutExpired:
        return 124, time.monotonic() - start, f"タイムアウト（{PER_TOOL_TIMEOUT}s）"


def _child_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _last_line(text: str | None) -> str:
    if not text:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="対象を列挙して終了")
    ap.add_argument("--warn-only", action="store_true",
                    help="失敗があっても exit 0（フックの警告モード用）")
    ap.add_argument("-k", dest="filter", default="",
                    help="tests/ の親フォルダ名で対象を絞る（部分一致）")
    args = ap.parse_args(argv)

    units = find_test_dirs(REPO_ROOT)
    if args.filter:
        needle = args.filter.lower()
        units = [u for u in units if needle in u.name.lower()]

    if not units:
        print("対象ユニットが見つかりませんでした。")
        return 0

    if args.list:
        for u in units:
            print(rel(u))
        return 0

    print(f"run_all_tests: {len(units)} ユニットを実行します\n")
    passed: list[str] = []
    skipped: list[str] = []
    failed: list[tuple[str, int, str]] = []

    for u in units:
        name = rel(u)
        print(f"  ▶ {name} ... ", end="", flush=True)
        code, elapsed, tail = run_one(u)
        if code == EXIT_OK:
            passed.append(name)
            print(f"OK ({elapsed:.1f}s)  {tail}")
        elif code == EXIT_NO_TESTS:
            skipped.append(name)
            print(f"skip（テスト0件, {elapsed:.1f}s）")
        else:
            failed.append((name, code, tail))
            print(f"NG (exit {code}, {elapsed:.1f}s)  {tail}")

    print()
    print("=" * 70)
    print(f"通過 {len(passed)} / 失敗 {len(failed)} / スキップ {len(skipped)}"
          f"（計 {len(units)}）")
    if failed:
        print("\n失敗したユニット:")
        for name, code, tail in failed:
            print(f"  - {name}  (exit {code})  {tail}")
        if args.warn_only:
            print("\n（--warn-only のため exit 0 で終了します）")
    print("=" * 70)
    return 1 if failed and not args.warn_only else 0


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


if __name__ == "__main__":
    sys.exit(main())
