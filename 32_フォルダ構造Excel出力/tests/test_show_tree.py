"""show_tree.build_report（CLI / GUI 共用のツリー生成）のテスト。"""
import os
import sys

import pytest

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "show_tree"))

from show_tree import build_report  # noqa: E402


@pytest.fixture
def sample_tree(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("x", encoding="utf-8")
    (tmp_path / "src" / "util.py").write_text("x", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("x", encoding="utf-8")
    (tmp_path / ".secret").write_text("x", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "app.cpython-312.pyc").write_text("x", encoding="utf-8")
    return tmp_path


def test_build_report_raises_on_missing_dir(tmp_path):
    with pytest.raises(ValueError):
        build_report(str(tmp_path / "nope"))


def test_build_report_has_header_and_summary(sample_tree):
    report = build_report(str(sample_tree))
    assert report[0].startswith("# Directory Tree")
    assert report[-1].startswith("# ") and "directories" in report[-1] and "files" in report[-1]


def _tree_nodes(report):
    """ヘッダー/サマリーを除いた、ツリー本体の枝行だけを連結して返す。"""
    return "\n".join(l for l in report if "── " in l)


def test_build_report_hides_hidden_and_default_ignores(sample_tree):
    nodes = _tree_nodes(build_report(str(sample_tree)))
    assert ".secret" not in nodes          # 隠しファイルは既定で非表示
    assert "__pycache__" not in nodes      # DEFAULT_IGNORE に含まれる


def test_build_report_show_hidden(sample_tree):
    assert ".secret" in _tree_nodes(build_report(str(sample_tree), show_hidden=True))


def test_build_report_ext_filter(sample_tree):
    nodes = _tree_nodes(build_report(str(sample_tree), ext=[".py"]))
    assert "app.py" in nodes
    assert "readme.md" not in nodes


def test_build_report_extra_ignore(sample_tree):
    nodes = _tree_nodes(build_report(str(sample_tree), ignore=["docs"]))
    assert "docs" not in nodes
    assert "src" in nodes


def test_build_report_depth_limits_recursion(sample_tree):
    nodes = _tree_nodes(build_report(str(sample_tree), depth=1))
    assert "src" in nodes
    assert "app.py" not in nodes  # 深さ1では src の中身までは降りない
