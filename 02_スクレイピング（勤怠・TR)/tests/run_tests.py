"""
テスト実行 & 結果保存スクリプト。
pytest の出力を UTF-8 (BOM付き) で .output/ に保存する。
BOM付きにすることで Windows のメモ帳・Excel でそのまま開ける。

使い方:
    python tests/run_tests.py
"""
import subprocess
import sys
import os
from datetime import datetime

# プロジェクトルートを基準にする
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT_DIR, ".output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
output_file = os.path.join(OUTPUT_DIR, f"test_{timestamp}.txt")

print("=" * 60)
print(f" テスト実行: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f" 出力先: {output_file}")
print("=" * 60)

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,   # stderr を stdout にマージ
    env=env,
    cwd=ROOT_DIR,
)

output = result.stdout.decode("utf-8", errors="replace")

# コンソールに表示
print(output)

# UTF-8 BOM付きで保存（Windows のメモ帳でそのまま開ける）
with open(output_file, "w", encoding="utf-8-sig") as f:
    f.write(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 60 + "\n\n")
    f.write(output)

print("=" * 60)
if result.returncode == 0:
    print(" [PASS] 全テスト成功")
else:
    print(" [FAIL] 失敗したテストがあります")
print(f" 結果を保存しました: {output_file}")
print("=" * 60)

sys.exit(result.returncode)
