"""
Notion API 共通モジュール

HEADERS / extract_title / ANKEN_DATABASE_ID を一元管理する。
config.py は AIに読み込ませないこと（TOKEN等が含まれるため）。
"""

_CONFIG_ERROR = (
    "config.py が見つかりません。src/config.py に NOTION_TOKEN を定義してください。"
)

try:
    from config import NOTION_TOKEN

    HEADERS = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
except ImportError:
    # import 時に例外を投げると pytest 等の収集を巻き込んで落ちる
    # （SystemExit だと INTERNALERROR）。import は通し、HEADERS を
    # 実際に参照した時点で分かりやすく落とす。
    def __getattr__(name):
        if name == "HEADERS":
            raise RuntimeError(_CONFIG_ERROR)
        raise AttributeError(name)

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
