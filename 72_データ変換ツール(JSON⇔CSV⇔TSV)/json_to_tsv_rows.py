import json
import csv
from pathlib import Path


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


def find_latest_json():
    json_files = sorted(
        Path(".").glob("*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if not json_files:
        raise FileNotFoundError("JSONファイルが見つかりません。")
    return json_files[0]


def main():
    latest_json = find_latest_json()
    print("処理対象 JSON:", latest_json)

    with latest_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    rows = flatten_with_levels(data)

    out_path = Path("output_levels.tsv")
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Level", "Key", "Value"])
        writer.writerows(rows)

    print(f"✅ TSV を {out_path.resolve()} に保存しました")


if __name__ == "__main__":
    main()
