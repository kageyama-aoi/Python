"""check_doc_refs.py の特性テスト（現行挙動の固定）。

repo 全体の pytest はツール横断の収集エラーがあり通らないため、
このテストは `python -m pytest scripts/` 単体で実行する想定。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import check_doc_refs as c  # noqa: E402


def test_looks_like_path_positive():
    assert c.looks_like_path("src/utils/logger.py")
    assert c.looks_like_path("34_Fixed2Excel/src/gui.py")
    assert c.looks_like_path("docs/plan.md")


def test_looks_like_path_negative():
    # スラッシュ無しの裸名・空白入り（コマンド行）・リポジトリ外
    assert not c.looks_like_path("run.bat")
    assert not c.looks_like_path("git log src/foo.py")
    assert not c.looks_like_path(".venv/Scripts/activate.ps1")
    # 末尾が構成ディレクトリ名だけ = 「形」の説明
    assert not c.looks_like_path("src/handlers")
    assert not c.looks_like_path("src/utils")


def test_is_placeholder():
    assert c.is_placeholder("config/{mode}.yaml")
    assert c.is_placeholder("md/Example.md")
    assert c.is_placeholder("path/to/file.py")
    assert not c.is_placeholder("34_Fixed2Excel/src/gui.py")


def test_clean_token_strips_line_numbers_and_bang():
    assert c.clean_token("`src/main.py:123`") == "src/main.py"
    assert c.clean_token("!md/foo.md") == "md/foo.md"


def test_resolve_path_against_repo(tmp_path):
    root = tmp_path
    (root / "90_ひな形").mkdir()
    doc = root / "90_ひな形" / "readme.md"
    doc.write_text("x", encoding="utf-8")
    (root / "90_ひな形" / "scripts").mkdir()
    (root / "90_ひな形" / "scripts" / "create_project.py").write_text("x", encoding="utf-8")
    assert c.resolve_path("scripts/create_project.py", doc, root)
    assert not c.resolve_path("scripts/missing.py", doc, root)


def test_extract_candidates_skips_fenced_blocks():
    text = "line `real/ref.py`\n```\n`fenced/ref.py`\n```\nafter\n"
    toks = [t for _, t in c.extract_candidates(text)]
    assert "real/ref.py" in toks
    assert "fenced/ref.py" not in toks


def test_is_meaningful_symbol_excludes_builtins():
    # import 経由でも組み込み名は除外される（dir(builtins) 由来であること）
    assert not c.is_meaningful_symbol("print")
    assert not c.is_meaningful_symbol("open")
    assert not c.is_meaningful_symbol("sorted")
    assert c.is_meaningful_symbol("build_symbol_index")


def test_main_runs_and_returns_int():
    rc = c.main(["--quiet"])
    assert rc == 0
    rc_check = c.main(["--check", "--quiet"])
    assert rc_check in (0, 1)
