"""create_project.py の特性テスト。

テンプレート実体を 90_ひな形/templates/ の実ファイルへ切り出したこと（#180）で、
生成結果が壊れていないかを固定する。
"""
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "create_project.py"


def _child_env() -> dict:
    # サブプロセスの stdout を "utf-8" として decode するので、子プロセス自身にも
    # utf-8 で出すよう指定する（Windowsの既定ロケール(cp932)のままだと、shell次第で
    # decode に失敗し stdout が None になる。scripts/run_all_tests.py と同じ対策）。
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _generate(tmp_path: Path, project_name: str) -> Path:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), project_name, "--dest", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", env=_child_env(),
    )
    assert result.returncode == 0, result.stderr
    return tmp_path / project_name


def test_generates_expected_structure(tmp_path):
    project_dir = _generate(tmp_path, "99_テスト用ツール")

    for relpath in (
        ".gitignore", "README.md", "requirements.txt",
        "config/main.yaml", "src/__init__.py", "src/main.py",
        "src/config_manager.py", "src/utils/__init__.py", "src/utils/logger.py",
    ):
        assert (project_dir / relpath).is_file(), f"missing: {relpath}"

    for relpath in ("src/handlers", "config/modes", "docs", "data/input", "scripts", "tests"):
        assert (project_dir / relpath).is_dir(), f"missing dir: {relpath}"


def test_project_name_is_substituted(tmp_path):
    project_dir = _generate(tmp_path, "99_テスト用ツール")

    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# 99_テスト用ツール")
    assert "%project_name%" not in readme

    main_yaml = (project_dir / "config" / "main.yaml").read_text(encoding="utf-8")
    assert 'app_name: "99_テスト用ツール"' in main_yaml
    assert "%project_name%" not in main_yaml


def test_generated_main_runs(tmp_path):
    project_dir = _generate(tmp_path, "99_テスト用ツール")

    result = subprocess.run(
        [sys.executable, "src/main.py"],
        cwd=project_dir, capture_output=True, text=True, encoding="utf-8",
        env=_child_env(),
    )
    assert result.returncode == 0, result.stderr
    assert "Hello, 99_テスト用ツール!" in result.stdout


def test_missing_template_file_cleans_up_partial_directory(tmp_path):
    """テンプレートファイルが欠けている場合、中途半端なプロジェクトフォルダを残さない。"""
    templates_dir = Path(__file__).resolve().parent.parent / "templates"
    target = templates_dir / "requirements.txt"
    backup = target.with_suffix(".txt.bak")
    target.rename(backup)
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "99_テスト用ツール", "--dest", str(tmp_path)],
            capture_output=True, text=True, encoding="utf-8", env=_child_env(),
        )
    finally:
        backup.rename(target)

    assert result.returncode == 0  # create_structure は例外を投げずreturnする
    assert "Error" in result.stdout
    assert not (tmp_path / "99_テスト用ツール").exists()


def test_refuses_to_overwrite_existing_directory(tmp_path):
    project_dir = _generate(tmp_path, "99_テスト用ツール")
    marker = project_dir / "untouched.txt"
    marker.write_text("keep me", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "99_テスト用ツール", "--dest", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", env=_child_env(),
    )
    assert "already exists" in result.stdout
    assert marker.read_text(encoding="utf-8") == "keep me"
