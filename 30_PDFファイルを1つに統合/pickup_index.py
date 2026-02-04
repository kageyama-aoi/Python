import ast
import csv
import sys
from pathlib import Path

# ==============================
# 設定：探索ルートは現在ディレクトリ
# ==============================
ROOT_DIR = Path.cwd()
OUTPUT_DIR = ROOT_DIR / "output"

# 除外ディレクトリ（必要に応じて追加）
EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    OUTPUT_DIR.name,
}

# ==============================
# 共通：停止＋説明
# ==============================
def stop(title: str, message: str):
    print("\n" + "=" * 60)
    print(f"⚠ {title}")
    print("-" * 60)
    print(message)
    print("=" * 60 + "\n")
    sys.exit(1)

# ==============================
# Pythonファイル探索（再帰）
# ==============================
py_files = []
for path in ROOT_DIR.rglob("*.py"):
    if any(part in EXCLUDE_DIRS for part in path.parts):
        continue
    py_files.append(path)

if not py_files:
    stop(
        "Pythonファイルが見つかりません",
        f"{ROOT_DIR.resolve()} 配下に .py ファイルがありません。"
    )

OUTPUT_DIR.mkdir(exist_ok=True)

# ==============================
# index 抽出
# ==============================
index = []

for py_file in py_files:
    try:
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
        doc = ast.get_docstring(tree)
    except Exception:
        print(f"⚠ 読み飛ばし: {py_file}（解析失敗）")
        continue

    if not doc:
        continue  # docstringなしは静かにスキップ

    meta = {}
    for line in doc.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()

    index.append({
        "path": str(py_file.relative_to(ROOT_DIR)),
        **meta
    })

if not index:
    stop(
        "docstring付きPythonコードがありません",
        "docstring（\"\"\" \"\"\"）を持つPythonファイルが見つかりませんでした。"
    )

# ==============================
# CSV出力（入力名を流用）
# ==============================
project_name = ROOT_DIR.name
output_file = OUTPUT_DIR / f"{project_name}_index.csv"

fieldnames = sorted({k for item in index for k in item.keys()})

try:
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(index)
except Exception as e:
    stop(
        "CSVファイルの書き込みに失敗しました",
        f"出力先: {output_file.resolve()}\n\nエラー内容:\n{e}"
    )

# ==============================
# 正常終了
# ==============================
print("\n✅ index CSV を生成しました")
print(f"探索ルート: {ROOT_DIR.resolve()}")
print(f"出力ファイル: {output_file.resolve()}")
print(f"件数: {len(index)}")
print("Excel / pandas / Notion でそのまま検索できます。\n")
