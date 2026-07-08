"""
案件ID一覧取得スクリプト list_anken.py

【使い方】
1. python list_anken.py
2. 表示された案件一覧から絞り込みたいもののIDをコピー
3. config.py の FILTER_ANKEN_IDS に貼り付け

⚠️ このスクリプト自体はAIに読み込ませてOKです（TOKEN等は含まない）

【アプローチについて】
  Notion APIの仕様上、リレーション型プロパティは
  search/query APIで値が返らないため、
  案件DBを直接クエリして一覧を取得しています。
"""

import time
import requests

from notion_client import HEADERS, ANKEN_DATABASE_ID, extract_title


def query_all_anken():
    """案件DBを直接クエリして全案件を取得"""
    all_pages = []
    start_cursor = None

    while True:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor

        resp = requests.post(
            f"https://api.notion.com/v1/databases/{ANKEN_DATABASE_ID}/query",
            headers=HEADERS,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        all_pages.extend(data.get("results", []))

        if not data.get("has_more"):
            break
        start_cursor = data.get("next_cursor")
        time.sleep(0.3)

    return all_pages


def main():
    print("=" * 60)
    print("  案件ID一覧取得ツール")
    print("=" * 60)
    print()
    print("🔍 案件DBを直接クエリ中...")

    try:
        pages = query_all_anken()
    except requests.HTTPError as e:
        print(f"❌ エラー: {e}")
        print("   → 案件DBにインテグレーションが接続されているか確認してください")
        return

    print(f"   → {len(pages)} 件の案件が見つかりました\n")

    # 案件一覧を名前順にソート
    anken_list = []
    for page in pages:
        page_id = page["id"].replace("-", "")
        name = extract_title(page)
        anken_list.append((name, page_id))

    anken_list.sort(key=lambda x: x[0])

    # ===== 結果表示 =====
    print("=" * 60)
    print("  案件一覧")
    print("=" * 60)
    for name, page_id in anken_list:
        print(f"  {name:<30} {page_id}")

    # ===== config.py用の出力 =====
    print()
    print("=" * 60)
    print("  ↓ config.py の FILTER_ANKEN_IDS にコピー")
    print("=" * 60)
    print()
    print("FILTER_ANKEN_IDS = [")
    for name, page_id in anken_list:
        print(f'    "{page_id}",  # {name}')
    print("]")
    print()


if __name__ == "__main__":
    main()
