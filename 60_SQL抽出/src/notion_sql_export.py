"""
Notion SQL集 → NotebookLM向けMarkdown一括エクスポートスクリプト

【使い方】
1. pip install requests
2. config.py に NOTION_TOKEN などの設定を記入（⚠️ AIに読み込ませないこと）
3. python notion_sql_export.py
4. 出力された sql_knowledge.md を NotebookLM にアップロード

【Notionインテグレーショントークンの取得方法】
https://www.notion.so/my-integrations にアクセスし、
「新しいインテグレーション」を作成 → トークンをコピー
※対象のNotionページにインテグレーションを「接続」する必要があります
"""

import re
import time
import requests
from datetime import datetime

# ===== 設定読み込み =====
# ⚠️ config.py に TOKEN等を記載してください（AIに読み込ませないこと）
try:
    from config import OUTPUT_FILE, DATABASE_ID, FILTER_ANKEN_IDS
except ImportError:
    raise SystemExit("❌ config.py が見つかりません。config.py を作成してください。")

from notion_client import HEADERS, extract_title


def search_sql_pages():
    """ナレッジDB内のSQL集ページを全件検索（ページネーション対応）"""
    print("🔍 SQL集ページを検索中...")
    all_results = []
    start_cursor = None

    while True:
        payload = {
            "query": "SQL集",
            "filter": {"property": "object", "value": "page"},
            "page_size": 100,
        }
        if start_cursor:
            payload["start_cursor"] = start_cursor

        resp = requests.post(
            "https://api.notion.com/v1/search",
            headers=HEADERS,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

        # タイトルが「SQL集」のページだけ絞り込む
        for page in data.get("results", []):
            title = extract_title(page)
            if not ("SQL" in title or "sql" in title.lower()):
                continue

            # 案件フィルタが指定されている場合は絞り込む
            if FILTER_ANKEN_IDS:
                anken_ids = extract_relation_ids(page, "案件")
                if not any(aid in FILTER_ANKEN_IDS for aid in anken_ids):
                    continue

            all_results.append(page)

        print(f"  取得済み: {len(all_results)}件")

        if not data.get("has_more"):
            break
        start_cursor = data.get("next_cursor")
        time.sleep(0.3)  # レート制限対策

    print(f"✅ 合計 {len(all_results)} ページ見つかりました\n")
    return all_results


def extract_relation_ids(page, prop_name):
    """リレーションプロパティからIDリストを抽出
    Notion APIはリレーションをURLまたはIDで返す場合がある
    例: ["https://www.notion.so/1ce2b53c7886496f99a1fbf3603c25e3"]
        または [{"id": "1ce2b53c-..."}]
    """
    try:
        props = page.get("properties", {})
        val = props.get(prop_name, {})
        ids = []

        # relation型（標準APIレスポンス）
        if isinstance(val, dict) and val.get("type") == "relation":
            for r in val.get("relation", []):
                raw = r.get("id", "")
                ids.append(raw.replace("-", ""))

        # URL文字列のリスト（MCPレスポンス形式）
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    # notion.so/XXXXXXXX 形式からIDを抽出
                    m = re.search(r'([0-9a-f]{32})$', item.replace("-", ""))
                    if m:
                        ids.append(m.group(1))

        return ids
    except Exception:
        pass
    return []


def get_page_blocks(page_id):
    """ページのブロックを再帰的に全取得（トグル内も含む）"""
    blocks = []
    start_cursor = None

    while True:
        url = f"https://api.notion.com/v1/blocks/{page_id}/children"
        params = {"page_size": 100}
        if start_cursor:
            params["start_cursor"] = start_cursor

        resp = requests.get(url, headers=HEADERS, params=params)
        if resp.status_code == 404:
            return blocks
        resp.raise_for_status()
        data = resp.json()

        for block in data.get("results", []):
            blocks.append(block)
            # 子ブロードがある場合（トグル、箇条書きなど）は再帰取得
            if block.get("has_children"):
                child_blocks = get_page_blocks(block["id"])
                block["_children"] = child_blocks

        if not data.get("has_more"):
            break
        start_cursor = data.get("next_cursor")
        time.sleep(0.2)

    return blocks


def blocks_to_markdown(blocks, depth=0):
    """ブロックをMarkdownテキストに変換"""
    lines = []
    indent = "  " * depth

    for block in blocks:
        btype = block.get("type", "")
        content = block.get(btype, {})

        # リッチテキストを結合
        def rich_text(rt_list):
            return "".join(t.get("plain_text", "") for t in rt_list)

        if btype == "paragraph":
            text = rich_text(content.get("rich_text", []))
            if text.strip():
                lines.append(f"{indent}{text}")

        elif btype in ("heading_1", "heading_2", "heading_3"):
            text = rich_text(content.get("rich_text", []))
            level = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}[btype]
            lines.append(f"\n{indent}{level} {text}")

        elif btype == "code":
            code = rich_text(content.get("rich_text", []))
            lang = content.get("language", "sql")
            lines.append(f"\n{indent}```{lang}")
            lines.append(code)
            lines.append(f"{indent}```\n")

        elif btype == "toggle":
            text = rich_text(content.get("rich_text", []))
            lines.append(f"\n{indent}#### 📌 {text}")
            # トグル内の子ブロックを展開
            children = block.get("_children", [])
            if children:
                lines.append(blocks_to_markdown(children, depth + 1))

        elif btype == "bulleted_list_item":
            text = rich_text(content.get("rich_text", []))
            lines.append(f"{indent}- {text}")

        elif btype == "numbered_list_item":
            text = rich_text(content.get("rich_text", []))
            lines.append(f"{indent}1. {text}")

        elif btype == "quote":
            text = rich_text(content.get("rich_text", []))
            lines.append(f"{indent}> {text}")

        elif btype == "divider":
            lines.append(f"\n{indent}---\n")

        elif btype == "callout":
            text = rich_text(content.get("rich_text", []))
            lines.append(f"{indent}> 💡 {text}")

        # トグル以外で子がある場合
        if btype != "toggle" and block.get("_children"):
            lines.append(blocks_to_markdown(block["_children"], depth + 1))

    return "\n".join(lines)


def get_page_properties(page):
    """ページのプロパティ（AI要約・キーワードなど）を取得"""
    props = page.get("properties", {})
    info = {}

    for key, val in props.items():
        vtype = val.get("type")
        if vtype == "rich_text":
            info[key] = "".join(
                t.get("plain_text", "") for t in val.get("rich_text", [])
            )
        elif vtype == "date":
            d = val.get("date")
            info[key] = d.get("start", "") if d else ""
        elif vtype == "multi_select":
            info[key] = ", ".join(
                o.get("name", "") for o in val.get("multi_select", [])
            )
        elif vtype == "select":
            s = val.get("select")
            info[key] = s.get("name", "") if s else ""

    return info


def main():
    print("=" * 60)
    print("  Notion SQL集 → NotebookLM向けMarkdown エクスポーター")
    print("=" * 60)
    print()

    # Step1: SQL集ページを全件検索
    pages = search_sql_pages()

    if not pages:
        print("❌ SQL集ページが見つかりませんでした。")
        print("   → インテグレーションが対象ページに接続されているか確認してください。")
        return

    # Step2: 各ページのコンテンツを取得してMarkdownに変換
    all_markdown = []
    all_markdown.append("# SQL集 ナレッジベース（NotebookLM向け）\n")
    all_markdown.append(f"> エクスポート日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    all_markdown.append(f"> ページ総数: {len(pages)}\n")
    all_markdown.append("\n---\n")

    # テーブル関係サマリーのプレースホルダー（/sql_export スキルが自動生成・更新する）
    all_markdown.append("## テーブル関係サマリー\n\n---\n")

    for i, page in enumerate(pages, 1):
        page_id = page["id"]
        title = extract_title(page)
        url = f"https://www.notion.so/{page_id.replace('-', '')}"
        updated = page.get("last_edited_time", "")[:10]

        print(f"📄 [{i}/{len(pages)}] {title} ({updated}) を取得中...")

        try:
            blocks = get_page_blocks(page_id)
            md_content = blocks_to_markdown(blocks)

            section = f"\n\n## {title}（更新日: {updated}）\n"
            section += f"> Notionリンク: {url}\n\n"
            section += md_content if md_content.strip() else "_（コンテンツなし）_"
            section += "\n\n---"

            all_markdown.append(section)
            time.sleep(0.3)

        except Exception as e:
            print(f"  ⚠️ エラー: {e}")
            all_markdown.append(f"\n\n## {title}（取得エラー）\n> {e}\n\n---")

    # Step3: ファイルに書き出し
    output = "\n".join(all_markdown)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\n✅ 完了！ '{OUTPUT_FILE}' に出力しました（{len(output):,} 文字）")
    print("\n📋 次のステップ:")
    print("   1. sql_knowledge.md を NotebookLM にアップロード")
    print("   2. 「このSQLを参考に〇〇するSQLを書いて」と質問する")


if __name__ == "__main__":
    main()
