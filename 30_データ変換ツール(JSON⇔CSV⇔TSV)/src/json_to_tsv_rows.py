import csv
import json
import sys
from datetime import datetime
from pathlib import Path

# src/ の1つ上（プロジェクトルート）を基準にする。cwdに依存しないため、
# run.batから起動しても直接 `python src/json_to_tsv_rows.py` を実行しても同じ場所を指す。
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_DIR = BASE_DIR / "data" / "output"


class JsonToTsvError(RuntimeError):
    """このスクリプトの、原因を人間向けに説明するエラー。"""


def flatten_with_levels(data, parent_key="", level=0):
    """
    JSONを「レベル番号」「キー」「値」で縦展開する形式に変換
    """
    rows = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                # ネスト開始
                rows.append([f"L{level}", k, ""])
                child_rows = flatten_with_levels(v, parent_key=k, level=level + 1)
                rows.extend(child_rows)
            else:
                # プリミティブ値
                rows.append([f"L{level}", k, "" if v is None else v])
    elif isinstance(data, list):
        # 配列はカンマ区切りで文字列化
        rows.append([f"L{level}", parent_key, ",".join("" if x is None else str(x) for x in data)])
    else:
        # その他の値
        rows.append([f"L{level}", parent_key, "" if data is None else data])
    return rows


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


def main() -> int:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    try:
        json_path = input_path if input_path else find_latest_json()
        if not json_path.exists():
            raise JsonToTsvError(f"指定されたJSONファイルが見つかりません:\n{json_path}")

        print(f"処理対象 JSON: {json_path}")

        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        rows = flatten_with_levels(data)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUT_DIR / f"output_levels_{timestamp}.tsv"
        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["Level", "Key", "Value"])
            writer.writerows(rows)

        print(f"TSV を生成: {out_path}")
    except JsonToTsvError as exc:
        print(f"\nエラー: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
