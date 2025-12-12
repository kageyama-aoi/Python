import json
import os
import shutil
from datetime import datetime


# -----------------------------
# JSON → leaf path 展開
# -----------------------------
def extract_paths(obj, prefix=""):
    paths = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            paths.extend(extract_paths(v, new_prefix))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_prefix = f"{prefix}[{i}]"
            paths.extend(extract_paths(item, new_prefix))
    else:
        # leaf
        paths.append((prefix, obj))
    return paths


# -----------------------------
# パスを階層ごとに分割
# -----------------------------
def split_path(path):
    """
    'courses[0].conditions[1].child.update.meta.note'
     → ['courses','[0]','conditions','[1]','child','update','meta','note']
    """
    parts = []
    temp = ""
    i = 0
    while i < len(path):
        if path[i] == "[":
            # 配列インデックス抽出
            j = i
            while j < len(path) and path[j] != "]":
                j += 1
            j += 1  # ']'含める
            parts.append(path[i:j])
            i = j
            temp = ""
        elif path[i] == ".":
            if temp:
                parts.append(temp)
                temp = ""
            i += 1
        else:
            temp += path[i]
            i += 1

    if temp:
        parts.append(temp)

    return parts


# -----------------------------
# 最新 JSON ファイル取得
# -----------------------------
from pathlib import Path

def find_latest_json():
    p = Path(".")
    json_files = sorted(
        p.glob("*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    if not json_files:
        raise FileNotFoundError("JSONファイルが見つかりません。")

    return json_files[0]



# -----------------------------
# TSV を構築（階層ごとに縦展開）
# -----------------------------
def build_tsv_with_levels(paths):
    split_paths = [split_path(p) for p, _ in paths]
    max_depth = max(len(sp) for sp in split_paths)

    # rows[0]〜rows[max_depth] を作成
    rows = [[] for _ in range(max_depth + 1)]

    for (path, value), segments in zip(paths, split_paths):
        for depth in range(max_depth):
            if depth < len(segments):
                rows[depth].append(segments[depth])
            else:
                rows[depth].append("")
        rows[max_depth].append("" if value is None else str(value))

    # -------------------------------
    # ★ 正しいルールで矢印に変換
    # -------------------------------
    for r in range(max_depth):   # 値行は除外
        prev = None
        for c in range(len(rows[r])):
            cur = rows[r][c]

            # 置換条件：
            # 1) 空ではない
            # 2) 前の文字と同じ
            # 3) segment が leaf 値ではない（'value', 'input_month', 'has_target' などは除外）
            is_leaf_like = (cur in ["value", "input_month", "has_target", "updated_records", "created_records"])

            if prev is not None and cur == prev and cur != "" and not is_leaf_like:
                rows[r][c] = "→"
            else:
                prev = cur


    return "\n".join("\t".join(row) for row in rows)



# -----------------------------
# JSON → TSV に変換
# -----------------------------
def json_to_tsv(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    paths = extract_paths(data)  # (path,value)
    # JSON 順序を尊重するため、そのまま順番で使う
    tsv = build_tsv_with_levels(paths)
    return tsv


# -----------------------------
# TSV 保存（古い output は old へ移動）
# -----------------------------
def save_with_timestamp(tsv_text, prefix="output"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"{prefix}_{timestamp}.tsv"

    os.makedirs("old", exist_ok=True)

    # 既存 output_* 移動
    for file in os.listdir("."):
        if file.startswith(prefix) and file.endswith(".tsv"):
            shutil.move(file, os.path.join("old", file))

    with open(new_filename, "w", encoding="utf-8") as f:
        f.write(tsv_text)

    return new_filename


# -----------------------------
# メイン処理
# -----------------------------
if __name__ == "__main__":
    latest_json = find_latest_json()
    print("処理対象 JSON:", latest_json)

    tsv_output = json_to_tsv(latest_json)
    saved = save_with_timestamp(tsv_output)

    print("TSV を生成:", saved)
