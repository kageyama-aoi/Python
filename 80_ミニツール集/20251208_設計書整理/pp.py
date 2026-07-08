import os
import re
import shutil
from datetime import datetime
import configparser

# -------------------------
# 設定ファイル読み込み
# -------------------------
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

TARGET_DIR = config["settings"]["target_dir"]
KEEP = int(config["settings"]["keep"])
OLD_DIR_NAME = config["settings"]["old_dir_name"]
DRY_RUN = config["settings"].getboolean("dry_run")

# -------------------------
# 正規表現パターン
# -------------------------
# ファイル名の末尾に _YYYYMMDD が付いている想定
date_pattern = re.compile(r"_(\d{8})(?=\.)")

# -------------------------
# 1. 対象フォルダのチェック
# -------------------------
if not os.path.isdir(TARGET_DIR):
    raise Exception(f"対象フォルダが存在しません: {TARGET_DIR}")

old_dir = os.path.join(TARGET_DIR, OLD_DIR_NAME)
if not os.path.isdir(old_dir):
    if DRY_RUN:
        print(f"[DRY-RUN] old フォルダがないため作成予定: {old_dir}")
    else:
        os.makedirs(old_dir)

# -------------------------
# 2. ファイルを走査し、名前を分解
# -------------------------
files = os.listdir(TARGET_DIR)

# ベース名 → [(ファイルパス, 日付)] の辞書
groups = {}

for fn in files:
    full_path = os.path.join(TARGET_DIR, fn)
    if not os.path.isfile(full_path):
        continue

    m = date_pattern.search(fn)
    if not m:
        continue  # 日付が無いファイルはスキップ

    date_str = m.group(1)
    date_dt = datetime.strptime(date_str, "%Y%m%d")

    # ベース名 = 日付部分を除いた部分
    base_name = date_pattern.sub("", fn)

    groups.setdefault(base_name, []).append((full_path, date_dt))

# -------------------------
# 3. ベース名ごとにソートして3件残す
# -------------------------
for base_name, items in groups.items():

    # 日付降順でソート
    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)

    keep_items = items_sorted[:KEEP]
    old_items = items_sorted[KEEP:]

    print(f"\n=== {base_name} ===")
    print(f"残す: {[os.path.basename(p) for p, d in keep_items]}")
    print(f"移動対象: {[os.path.basename(p) for p, d in old_items]}")

    for file_path, _ in old_items:
        dest = os.path.join(old_dir, os.path.basename(file_path))

        if DRY_RUN:
            print(f"[DRY-RUN] → {dest} へ移動予定")
        else:
            shutil.move(file_path, dest)
            print(f"移動完了: {file_path} → {dest}")
