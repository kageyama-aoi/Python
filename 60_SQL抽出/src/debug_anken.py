"""
デバッグ用スクリプト debug_anken.py
案件DBへのAPIアクセス状況を確認します
AIに読み込ませてOK（TOKEN含まない）
"""

import requests

try:
    from config import NOTION_TOKEN
except ImportError:
    raise SystemExit("❌ config.py が見つかりません")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

ANKEN_DATABASE_ID = "61d853d3fa614c878b22fa5cf9b6c0b1"

print("=" * 60)
print("  APIデバッグ")
print("=" * 60)

# ① DBメタ情報を取得
print("\n① データベース情報を取得中...")
resp = requests.get(
    f"https://api.notion.com/v1/databases/{ANKEN_DATABASE_ID}",
    headers=HEADERS,
)
print(f"   ステータスコード: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"   DB名: {data.get('title', [{}])[0].get('plain_text', '不明')}")
    print("   ✅ DBアクセス成功！")
elif resp.status_code == 404:
    print("   ❌ 404 Not Found")
    print("   → このDBにインテグレーションが接続されていない可能性があります")
    print(f"   → https://www.notion.so/{ANKEN_DATABASE_ID} を開いて")
    print("      「…」→「接続」→ インテグレーションを追加してください")
elif resp.status_code == 401:
    print("   ❌ 401 Unauthorized")
    print("   → NOTION_TOKEN が正しくない可能性があります")
else:
    print(f"   ❌ エラー: {resp.text}")

# ② クエリ実行
print("\n② DBクエリ実行中...")
resp2 = requests.post(
    f"https://api.notion.com/v1/databases/{ANKEN_DATABASE_ID}/query",
    headers=HEADERS,
    json={"page_size": 10},
)
print(f"   ステータスコード: {resp2.status_code}")
if resp2.status_code == 200:
    data2 = resp2.json()
    results = data2.get("results", [])
    print(f"   取得件数: {len(results)}")
    for page in results:
        props = page.get("properties", {})
        for key, val in props.items():
            if val.get("type") == "title":
                name = "".join(t.get("plain_text", "") for t in val.get("title", []))
                print(f"   → {name}  (id: {page['id']})")
    print("   ✅ クエリ成功！")
else:
    print(f"   ❌ エラー: {resp2.text}")

print()
