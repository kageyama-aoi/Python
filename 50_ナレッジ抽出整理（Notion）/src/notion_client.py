"""
Notion API 共通モジュール

HEADERS / extract_title / ANKEN_DATABASE_ID を一元管理する。
config.py は AIに読み込ませないこと（TOKEN等が含まれるため）。
"""

try:
    from config import NOTION_TOKEN
except ImportError:
    raise SystemExit("❌ config.py が見つかりません。config.py を作成してください。")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}

# 案件DB（https://www.notion.so/61d853d3fa614c878b22fa5cf9b6c0b1）
ANKEN_DATABASE_ID = "61d853d3fa614c878b22fa5cf9b6c0b1"


def extract_title(page):
    """ページタイトルを抽出"""
    try:
        props = page.get("properties", {})
        for key, val in props.items():
            if val.get("type") == "title":
                return "".join(t.get("plain_text", "") for t in val.get("title", []))
    except Exception:
        pass
    return "（タイトルなし）"
