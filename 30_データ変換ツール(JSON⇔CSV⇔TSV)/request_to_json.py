#パラメータを渡す形式でも作りたい
#今はURLを変換するだけ

import urllib.parse
import json
from pathlib import Path
from datetime import datetime

def request_to_json(request_str: str) -> dict:
    """
    クエリ文字列を辞書に変換する
    """
    parsed = urllib.parse.parse_qs(request_str)
    return {k: v[0] for k, v in parsed.items()}

def main():
    print("クエリ文字列を入力してください（例: loginId=0190019&pwd=n6hj*oA&smsgroup=teacher）")
    request_str = input(">>> ")

    # 変換処理
    data = request_to_json(request_str)

    # 整形したJSON文字列
    json_str = json.dumps(data, ensure_ascii=False, indent=4)

    # ファイル名生成: loginId + 日付時刻
    base_name = data.get("loginId", "request")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(f"{base_name}_{timestamp}.json")

    # ファイル保存
    output_file.write_text(json_str, encoding="utf-8")

    # 標準出力
    print("\n変換結果（JSON形式）:")
    print(json_str)

    # コピペ用（1行化）
    copy_paste_str = json.dumps(data, ensure_ascii=False)
    print("\n--- コピペ用（1行JSON）---")
    print(copy_paste_str)

    print(f"\n✅ JSONを {output_file.resolve()} に保存しました")

if __name__ == "__main__":
    main()
