"""run_all_tests.py の特性テスト（現行挙動の固定）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import run_all_tests as r  # noqa: E402


def test_find_test_dirs_discovers_known_units():
    units = r.find_test_dirs(r.REPO_ROOT)
    names = {u.name for u in units}
    # 代表的なユニットが拾えていること
    assert "34_Fixed2Excel" in names
    assert "scripts" in names
    # tests/ の親が対象（tests/ 自身ではない）
    assert all(u.name != "tests" for u in units)


def test_find_test_dirs_excludes_archive_and_venv():
    units = r.find_test_dirs(r.REPO_ROOT)
    for u in units:
        parts = set(u.relative_to(r.REPO_ROOT).parts)
        assert not (parts & {"_archive", ".venv", "venv", "node_modules"})


def test_list_mode_returns_zero(capsys):
    rc = r.main(["--list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "scripts" in out


def test_filter_narrows_units(capsys):
    rc = r.main(["--list", "-k", "34_Fixed2Excel"])
    assert rc == 0
    lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    assert lines == ["34_Fixed2Excel"]


def test_exit_codes_constants():
    assert r.EXIT_OK == 0
    assert r.EXIT_NO_TESTS == 5
