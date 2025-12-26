import os
import sys

def create_structure(project_name):
    # 定義: 作成するディレクトリ構造
    dirs = [
        "src",
        "src/handlers",
        "src/utils",
        "config",
        "config/modes",
        "docs",
        "data/input",
        "data/output",
        "data/temp",
        "logs",
        "scripts",
        "tests"
    ]

    # 定義: 作成するファイルとその中身
    files = {
        ".gitignore": "# General
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
virtualenv/
.env

# Distribution / Packaging
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Logs
*.log
logs/

# IDE
.vscode/
.idea/

# OS
desktop.ini
.DS_Store
",
        "README.md": f"# {project_name}\n\n## 概要\nここにプロジェクトの概要を記述します。\n\n## セットアップ\n```bash\npython -m venv venv\nvirtual\Scripts\activate\npip install -r requirements.txt\n```\n\n## 実行\n```bash\npython src/main.py\n```",
        "requirements.txt": "pyyaml\nruamel.yaml\n",
        "config/main.yaml": "app_name: \"{project_name}\"\nversion: \"0.1.0\"\nlog_level: \"INFO\"\n",
        "src/__init__.py": "",
        "src/main.py": "import os\nimport sys\n\n# プロジェクトルートをパスに追加\nsys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n\nfrom src.utils.logger import setup_logger\nfrom src.config_manager import ConfigManager\n\ndef main():\n    logger = setup_logger()\n    logger.info(\"Application started.\")\n    \n    # 設定の読み込み例\n    config = ConfigManager().load_config()\n    logger.info(f\"Loaded config for: {config.get('app_name', 'Unknown')}\")\n\n    print(f\"Hello, {config.get('app_name')}!\")\n\nif __name__ == \"__main__\":\n    main()\n",
        "src/config_manager.py": "import yaml\nimport os\n\nclass ConfigManager:\n    def __init__(self, config_path=\"config/main.yaml\"):\n        self.config_path = config_path\n\n    def load_config(self):\n        if not os.path.exists(self.config_path):\n            return {}\n        with open(self.config_path, 'r', encoding='utf-8') as f:\n            return yaml.safe_load(f)\n",
        "src/utils/__init__.py": "",
        "src/utils/logger.py": "import logging\nimport os\nfrom datetime import datetime\n\ndef setup_logger(name=\"app\", log_dir=\"logs\"):\n    os.makedirs(log_dir, exist_ok=True)\n    logger = logging.getLogger(name)\n    \n    if logger.hasHandlers():\n        return logger\n        \n    logger.setLevel(logging.INFO)\n\n    # Console Handler\n    ch = logging.StreamHandler()\n    ch.setLevel(logging.INFO)\n    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')\n    ch.setFormatter(formatter)\n    logger.addHandler(ch)\n\n    # File Handler\n    log_filename = datetime.now().strftime(\"%Y%m%d\") + \".log\"
    fh = logging.FileHandler(os.path.join(log_dir, log_filename), encoding='utf-8')\n    fh.setLevel(logging.INFO)\n    fh.setFormatter(formatter)\n    logger.addHandler(fh)\n\n    return logger\n",
    }

    # カレントディレクトリに作成
    base_path = os.path.join(os.getcwd(), project_name)

    if os.path.exists(base_path):
        print(f"Error: Directory '{project_name}' already exists.")
        return

    print(f"Creating project '{project_name}' at {base_path}...")

    # ディレクトリ作成
    os.makedirs(base_path)
    for d in dirs:
        os.makedirs(os.path.join(base_path, d), exist_ok=True)
        # package化
        if d.startswith("src") and d != "src":
             open(os.path.join(base_path, d, "__init__.py"), 'a').close()

    # ファイル作成
    for filename, content in files.items():
        file_path = os.path.join(base_path, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print("Done! Project structure created successfully.")
    print("-" * 30)
    print(f"cd {project_name}")
    print("python -m venv venv")
    print("venv\Scripts\activate")
    print("pip install -r requirements.txt")
    print("python src/main.py")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_project.py <project_name>")
    else:
        create_structure(sys.argv[1])
