import json
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

# src/ の1つ上（プロジェクトルート）を基準にする。cwdに依存しないため、
# run.batから起動しても直接 `python src/request_to_json.py` を実行しても同じ場所を指す。
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "output"


def request_to_json(request_str: str) -> dict:
    """
    クエリ文字列を辞書に変換する
    """
    parsed = urllib.parse.parse_qs(request_str)
    return {k: v[0] for k, v in parsed.items()}


def main() -> int:
    # CLI引数で渡された場合はそれを使う（GUIのテキスト入力欄から呼び出す想定）。
    # 引数が無ければ従来通り対話入力にフォールバックする。
    if len(sys.argv) > 1:
        request_str = sys.argv[1]
    else:
        print("クエリ文字列を入力してください（例: loginId=0190019&pwd=n6hj*oA&smsgroup=teacher）")
        request_str = input(">>> ")

    if not request_str.strip():
        print("\nエラー: クエリ文字列が空です。", file=sys.stderr)
        return 1

    # 変換処理
    data = request_to_json(request_str)

    # 整形したJSON文字列
    json_str = json.dumps(data, ensure_ascii=False, indent=4)

    # ファイル名生成: loginId + 日付時刻
    base_name = data.get("loginId", "request")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{base_name}_{timestamp}.json"

    # ファイル保存
    output_file.write_text(json_str, encoding="utf-8")

    # 標準出力
    print("\n変換結果（JSON形式）:")
    print(json_str)

    # コピペ用（1行化）
    copy_paste_str = json.dumps(data, ensure_ascii=False)
    print("\n--- コピペ用（1行JSON）---")
    print(copy_paste_str)

    print(f"\nJSONを生成: {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
