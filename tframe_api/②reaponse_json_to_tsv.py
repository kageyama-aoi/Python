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
                child_rows = flatten_with_levels(v, parent_key=k, level=level+1)
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

def main():
    # JSON入力（ここはファイル読み込みにしてもOK）
    json_text = r'''{
        "tcnToken": "rg0cje91s0kte6ku7jfakkukom",
        "code": "000",
        "name": "Success",
        "message": "正常に処理しました。",
        "count": 1,
        "teacher": {
            "lastName": "田中景",
            "firstName": "はなこ",
            "lastNameFurigana": "",
            "firstNameFurigana": "",
            "gender": "",
            "birthdate": null,
            "phone1Number": "",
            "phone2Number": "",
            "email1": "t.kageyama2@technopian.com",
            "email2": "",
            "idnumber": "190019",
            "personStatus": "11",
            "enrollDate": null,
            "leaveDate": null,
            "zeiKubun": "2",
            "accountIdName": "",
            "primaryAddressPostalcode": "",
            "primaryAddressState": "",
            "primaryAddressCity": "",
            "primaryAddressStreet": "",
            "primaryAddressKana": ""
        },
        "branch": {
            "branchAreaId": "関東",
            "branchBranchCode": "01",
            "branchName": "東京"
        }
    }'''

    data = json.loads(json_text)

    rows = flatten_with_levels(data)

    # TSV出力
    out_path = Path("output_levels.tsv")
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["Level", "Key", "Value"])
        writer.writerows(rows)

    print(f"✅ TSV を {out_path.resolve()} に保存しました")

if __name__ == "__main__":
    main()
