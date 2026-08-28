"""launcher_gui の tkinter 非依存ヘルパーのテスト。

GUI ウィジェット（_TagListEditor / LauncherApp）は表示環境が要るためここでは扱わない。
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from launcher_gui import merge_unique, split_tokens


# ---- split_tokens ----

def test_split_tokens_comma_and_space():
    assert split_tokens(".a, .b  .c") == [".a", ".b", ".c"]


def test_split_tokens_drops_empty_and_trims():
    assert split_tokens("  .a ,, .b , ") == [".a", ".b"]


def test_split_tokens_newlines():
    assert split_tokens("OLD\nbackup\n  logs") == ["OLD", "backup", "logs"]


def test_split_tokens_empty():
    assert split_tokens("   ") == []


# ---- merge_unique ----

def test_merge_unique_appends_only_new_preserving_order():
    assert merge_unique([".log", ".tmp"], [".tmp", ".bak", ".log", ".png"]) == \
        [".log", ".tmp", ".bak", ".png"]


def test_merge_unique_dedups_within_additions():
    assert merge_unique([], ["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_merge_unique_no_additions_returns_copy():
    original = ["x", "y"]
    result = merge_unique(original, [])
    assert result == original and result is not original
