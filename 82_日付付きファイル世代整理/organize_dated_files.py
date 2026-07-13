import os
import re
import shutil
from datetime import datetime
import configparser

# -------------------------
# 設定ファイル読み込み
# -------------------------
config = configparser.ConfigParser()
if not config.read("config.ini", encoding="utf-8"):
    raise SystemExit(
        "config.ini が見つかりません。config.example.ini をコピーして作成してください。"
    )

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
invalid_date_files = []  # 8桁だが日付として不正なもの（例: _99999999）

for fn in files:
    full_path = os.path.join(TARGET_DIR, fn)
    if not os.path.isfile(full_path):
        continue

    m = date_pattern.search(fn)
    if not m:
        continue  # 日付が無いファイルはスキップ

    date_str = m.group(1)
    try:
        date_dt = datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        invalid_date_files.append(fn)
        continue

    # ベース名 = 日付部分を除いた部分
    base_name = date_pattern.sub("", fn)

    groups.setdefault(base_name, []).append((full_path, date_dt))

# -------------------------
# 3. ベース名ごとにソートし、移動対象を洗い出す
# -------------------------
# (ベース名, 世代数, 移動対象リスト) を先に集めてから表示する。
# 移動対象ゼロのグループまで逐次printすると、本当に動くファイルが
# ノイズに埋もれて dry-run の確認がしづらいため。
move_plan = []
no_move_groups = 0

for base_name, items in sorted(groups.items()):
    items_sorted = sorted(items, key=lambda x: x[1], reverse=True)
    old_items = items_sorted[KEEP:]
    if old_items:
        move_plan.append((base_name, len(items_sorted), old_items))
    else:
        no_move_groups += 1

total_files = sum(len(v) for v in groups.values())
total_moves = sum(len(old_items) for _, _, old_items in move_plan)

# -------------------------
# 4. 結果表示と移動実行
# -------------------------
print(f"対象: {TARGET_DIR}（{total_files}ファイル → {len(groups)}グループ）")

moved = 0
collisions = []

if move_plan:
    print(f"\n【移動対象 {total_moves}件】")
    for base_name, generation_count, old_items in move_plan:
        print(f"\n=== {base_name} ===（{generation_count}世代あり、最新{min(KEEP, generation_count)}件を残す）")
        for file_path, _ in old_items:
            fn = os.path.basename(file_path)
            dest = os.path.join(old_dir, fn)

            if os.path.exists(dest):
                collisions.append(fn)
                print(f"  警告: {OLD_DIR_NAME}\\ に同名ファイルがあるため移動しません: {fn}")
                continue

            if DRY_RUN:
                print(f"  移動予定: {fn} → {OLD_DIR_NAME}\\")
            else:
                shutil.move(file_path, dest)
                print(f"  移動完了: {file_path} → {dest}")
            moved += 1
else:
    print("\n移動対象はありません。")

# -------------------------
# 5. サマリ
# -------------------------
print()
if no_move_groups:
    print(f"移動なし: {no_move_groups}グループ（keep={KEEP}以内）")
if invalid_date_files:
    print(f"警告: 日付として不正なためスキップ: {invalid_date_files}")
if collisions:
    print(f"警告: {OLD_DIR_NAME}\\ と同名衝突のため未移動: {collisions}")

if DRY_RUN:
    print(f"[DRY-RUN] 移動予定 {moved}件。実際の移動は行っていません（config.ini で dry_run = false にすると実行）")
else:
    print(f"移動完了 {moved}件")
