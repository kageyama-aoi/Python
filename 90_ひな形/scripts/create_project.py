import argparse
import os
from pathlib import Path

# 生成する実ファイルの正実装は 90_ひな形/templates/ 配下（00_project_standard.md §5参照）。
# このスクリプトに埋め込むと二重管理になるため、テンプレートファイルを読み込んで使う。
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

# 定義: 作成するディレクトリ構造
DIRS = [
    "src",
    "src/handlers",
    "src/utils",
    "config",
    "config/modes",
    "docs",
    "data/input",
    "data/output",
    "data/temp",
    "data/logs",
    "scripts",
    "tests",
]

# 定義: 生成先パス -> templates/ 配下のテンプレートファイル。
# テンプレート内の %project_name% はプロジェクト名に置換される
# （string-template-refactor スキルの %item% プレースホルダー方式に統一）。
TEMPLATE_FILES = {
    ".gitignore": "gitignore",
    "README.md": "README.md",
    "requirements.txt": "requirements.txt",
    "config/main.yaml": "config/main.yaml",
    "src/main.py": "src/main.py",
    "src/config_manager.py": "src/config_manager.py",
    "src/utils/logger.py": "src/utils/logger.py",
}

# 中身が不要な空ファイル（テンプレート化の対象外）
EMPTY_FILES = [
    "src/__init__.py",
    "src/utils/__init__.py",
]


def render_template(template_relpath: str, project_name: str) -> str:
    """templates/ 配下のファイルを読み込み、%project_name% を置換して返す。"""
    text = (TEMPLATES_DIR / template_relpath).read_text(encoding="utf-8")
    return text.replace("%project_name%", project_name)


def create_structure(project_name, dest_dir=None):
    # 出力先: --dest 指定があればそのディレクトリ直下、なければカレントディレクトリ直下（従来どおり）
    parent_dir = os.path.abspath(dest_dir) if dest_dir else os.getcwd()
    if not os.path.isdir(parent_dir):
        print(f"Error: Destination directory '{parent_dir}' does not exist.")
        return
    base_path = os.path.join(parent_dir, project_name)

    if os.path.exists(base_path):
        print(f"Error: Directory '{project_name}' already exists.")
        return

    print(f"Creating project '{project_name}' at {base_path}...")

    # ディレクトリ作成
    os.makedirs(base_path)
    for d in DIRS:
        os.makedirs(os.path.join(base_path, d), exist_ok=True)
        # package化
        if d.startswith("src") and d != "src":
            open(os.path.join(base_path, d, "__init__.py"), 'a').close()

    # 空ファイル作成
    for relpath in EMPTY_FILES:
        file_path = os.path.join(base_path, relpath)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        open(file_path, 'a').close()

    # テンプレートからファイル生成（%project_name% を置換）
    for dest_relpath, template_relpath in TEMPLATE_FILES.items():
        content = render_template(template_relpath, project_name)
        file_path = os.path.join(base_path, dest_relpath)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    print("Done! Project structure created successfully.")
    print("-" * 30)
    print(f"cd {project_name}")
    print("python -m venv venv")
    print(r"venv\Scripts\activate")
    print("pip install -r requirements.txt")
    print("python src/main.py")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="標準構成のPythonプロジェクトを生成する"
    )
    parser.add_argument("project_name", help="作成するプロジェクト名（例: NN_ツール名）")
    parser.add_argument(
        "--dest",
        default=None,
        help="生成先の親ディレクトリ（省略時はカレントディレクトリ直下に作成）",
    )
    args = parser.parse_args()
    create_structure(args.project_name, dest_dir=args.dest)
