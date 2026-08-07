import json
import sys
from datetime import datetime
from pathlib import Path

# src/ の1つ上（プロジェクトルート）を基準にする。cwdに依存しないため、
# run.batから起動しても直接 `python src/json_to_tsv_columns.py` を実行しても同じ場所を指す。
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_DIR = BASE_DIR / "data" / "output"
LEAF_LIKE_KEYS_CONFIG = BASE_DIR / "config" / "leaf_like_keys.json"

# is_leaf_likeの既定値（config/leaf_like_keys.jsonが無い場合のフォールバック）。
# 元は関数内に直書きされていた特定JSON構造向けの項目名。
DEFAULT_LEAF_LIKE_KEYS = ["value", "input_month", "has_target", "updated_records", "created_records"]


class JsonToTsvError(RuntimeError):
    """このスクリプトの、原因を人間向けに説明するエラー。"""


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
            # 配列インデックス抽出。'courses[0]' のように直前にキー名が続いている場合、
            # tempに貯めた 'courses' をここでflushしないと無言で消えてしまう
            # （実際に見つかったバグ。配列を含むパスのほぼ全パターンで親キー名が
            # 欠落していた）。
            if temp:
                parts.append(temp)
                temp = ""
            j = i
            while j < len(path) and path[j] != "]":
                j += 1
            j += 1  # ']'含める
            parts.append(path[i:j])
            i = j
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


def load_leaf_like_keys():
    """config/leaf_like_keys.json から矢印省略の対象外にするキー名一覧を読む。
    無い・壊れている場合は既定値にフォールバックする（設定ファイルはGUIの「設定を編集」で作成できる）。"""
    try:
        data = json.loads(LEAF_LIKE_KEYS_CONFIG.read_text(encoding="utf-8"))
        keys = data.get("leaf_like_keys")
        if isinstance(keys, list) and keys:
            return keys
    except (OSError, json.JSONDecodeError):
        pass
    return DEFAULT_LEAF_LIKE_KEYS


# -----------------------------
# 最新 JSON ファイル取得
# -----------------------------
def find_latest_json(input_dir: Path = INPUT_DIR) -> Path:
    json_files = sorted(
        input_dir.glob("*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if not json_files:
        raise JsonToTsvError(
            f"'{input_dir}/' にJSONファイルが見つかりませんでした。\n"
            f"→ 変換したいJSONを '{input_dir}/' フォルダに置いてから再実行してください。"
        )
    return json_files[0]


# -----------------------------
# TSV を構築（階層ごとに縦展開）
# -----------------------------
def build_tsv_with_levels(paths, leaf_like_keys=None):
    if leaf_like_keys is None:
        leaf_like_keys = DEFAULT_LEAF_LIKE_KEYS

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
    # 同じ値が連続する場合は「→」に置き換えて省略表示する
    # -------------------------------
    for r in range(max_depth):   # 値行は除外
        prev = None
        for c in range(len(rows[r])):
            cur = rows[r][c]

            # 置換条件：
            # 1) 空ではない
            # 2) 前の文字と同じ
            # 3) segment が leaf 値ではない（leaf_like_keysに含まれるものは省略しない）
            is_leaf_like = cur in leaf_like_keys

            if prev is not None and cur == prev and cur != "" and not is_leaf_like:
                rows[r][c] = "→"
            else:
                prev = cur

    return "\n".join("\t".join(row) for row in rows)


# -----------------------------
# JSON → TSV に変換
# -----------------------------
def json_to_tsv(json_path, leaf_like_keys=None):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    paths = extract_paths(data)  # (path,value)
    # JSON 順序を尊重するため、そのまま順番で使う
    return build_tsv_with_levels(paths, leaf_like_keys=leaf_like_keys)


# -----------------------------
# TSV 保存（タイムスタンプ付きファイル名。data/output/には過去分もそのまま残る）
# -----------------------------
def save_with_timestamp(tsv_text, output_dir: Path = OUTPUT_DIR, prefix="output"):
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / f"{prefix}_{timestamp}.tsv"
    out_path.write_text(tsv_text, encoding="utf-8")
    return out_path


def main() -> int:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    try:
        json_path = input_path if input_path else find_latest_json()
        if not json_path.exists():
            raise JsonToTsvError(f"指定されたJSONファイルが見つかりません:\n{json_path}")

        print(f"処理対象 JSON: {json_path}")
        leaf_like_keys = load_leaf_like_keys()
        tsv_output = json_to_tsv(json_path, leaf_like_keys=leaf_like_keys)
        saved = save_with_timestamp(tsv_output)
        print(f"TSV を生成: {saved}")
    except JsonToTsvError as exc:
        print(f"\nエラー: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
