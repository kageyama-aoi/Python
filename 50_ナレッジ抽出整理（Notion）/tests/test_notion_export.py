"""
ユニットテスト: notion_sql_export / notion_client

テスト対象: APIを呼ばない純粋関数
  - extract_title         (notion_client.py)
  - extract_relation_ids  (notion_sql_export.py)
  - blocks_to_markdown    (notion_sql_export.py)
  - get_page_properties   (notion_sql_export.py)

実行方法:
  cd 50_ナレッジ抽出整理（Notion）
  python -m pytest tests/ -v
  または
  python -m unittest discover tests
"""

import sys
import os
import unittest
from unittest.mock import MagicMock

# src/ を import パスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# config.py のモック（TOKEN等の機密情報を含むため実ファイルは読まない）
mock_config = MagicMock()
mock_config.NOTION_TOKEN = "test_token"
mock_config.OUTPUT_FILE = "sql_knowledge.md"
mock_config.DATABASE_ID = "test_db_id"
mock_config.FILTER_ANKEN_IDS = []
sys.modules['config'] = mock_config

from notion_client import extract_title
from notion_sql_export import extract_relation_ids, blocks_to_markdown, get_page_properties


# ===== ヘルパー =====

def make_page(title_text):
    """テスト用のNotionページオブジェクトを生成"""
    return {
        "properties": {
            "名前": {
                "type": "title",
                "title": [{"plain_text": title_text}]
            }
        }
    }


def make_block(btype, text="", **kwargs):
    """テスト用のNotionブロックオブジェクトを生成"""
    rich_text = [{"plain_text": text}] if text else []
    block = {
        "type": btype,
        btype: {"rich_text": rich_text, **kwargs},
        "has_children": False,
    }
    return block


# ===== extract_title =====

class TestExtractTitle(unittest.TestCase):

    def test_normal(self):
        """通常のタイトルが取得できる"""
        page = make_page("SQL集 2025-01-01")
        self.assertEqual(extract_title(page), "SQL集 2025-01-01")

    def test_empty_title(self):
        """空のタイトルは空文字を返す"""
        page = {"properties": {"名前": {"type": "title", "title": []}}}
        self.assertEqual(extract_title(page), "")

    def test_no_title_property(self):
        """titleプロパティがない場合はデフォルト文字列を返す"""
        page = {"properties": {"タグ": {"type": "multi_select", "multi_select": []}}}
        self.assertEqual(extract_title(page), "（タイトルなし）")

    def test_empty_properties(self):
        """propertiesが空の場合はデフォルト文字列を返す"""
        page = {"properties": {}}
        self.assertEqual(extract_title(page), "（タイトルなし）")

    def test_multiple_text_runs(self):
        """複数のテキストランが結合される"""
        page = {
            "properties": {
                "名前": {
                    "type": "title",
                    "title": [
                        {"plain_text": "SQL集"},
                        {"plain_text": " (2025)"},
                    ]
                }
            }
        }
        self.assertEqual(extract_title(page), "SQL集 (2025)")


# ===== extract_relation_ids =====

class TestExtractRelationIds(unittest.TestCase):

    def test_standard_relation(self):
        """relation型の標準APIレスポンス"""
        page = {
            "properties": {
                "案件": {
                    "type": "relation",
                    "relation": [
                        {"id": "1ce2b53c-7886-496f-99a1-fbf3603c25e3"},
                    ]
                }
            }
        }
        ids = extract_relation_ids(page, "案件")
        self.assertEqual(ids, ["1ce2b53c788649 6f99a1fbf3603c25e3".replace(" ", "")])

    def test_url_list_format(self):
        """URLリスト形式（MCPレスポンス）"""
        page = {
            "properties": {
                "案件": [
                    "https://www.notion.so/1ce2b53c7886496f99a1fbf3603c25e3"
                ]
            }
        }
        ids = extract_relation_ids(page, "案件")
        self.assertEqual(ids, ["1ce2b53c7886496f99a1fbf3603c25e3"])

    def test_missing_property(self):
        """プロパティが存在しない場合は空リストを返す"""
        page = {"properties": {}}
        ids = extract_relation_ids(page, "案件")
        self.assertEqual(ids, [])

    def test_empty_relation(self):
        """relationが空の場合は空リストを返す"""
        page = {
            "properties": {
                "案件": {"type": "relation", "relation": []}
            }
        }
        ids = extract_relation_ids(page, "案件")
        self.assertEqual(ids, [])


# ===== blocks_to_markdown =====

class TestBlocksToMarkdown(unittest.TestCase):

    def test_paragraph(self):
        """paragraphブロックが変換される"""
        blocks = [make_block("paragraph", "これはテスト文章です")]
        result = blocks_to_markdown(blocks)
        self.assertIn("これはテスト文章です", result)

    def test_empty_paragraph_skipped(self):
        """空のparagraphは出力されない"""
        blocks = [make_block("paragraph", "")]
        result = blocks_to_markdown(blocks)
        self.assertEqual(result.strip(), "")

    def test_heading_levels(self):
        """見出しレベルが正しく変換される"""
        blocks = [
            make_block("heading_1", "大見出し"),
            make_block("heading_2", "中見出し"),
            make_block("heading_3", "小見出し"),
        ]
        result = blocks_to_markdown(blocks)
        self.assertIn("# 大見出し", result)
        self.assertIn("## 中見出し", result)
        self.assertIn("### 小見出し", result)

    def test_code_block(self):
        """コードブロックが```で囲まれる"""
        block = make_block("code", "SELECT * FROM contacts", language="sql")
        result = blocks_to_markdown([block])
        self.assertIn("```sql", result)
        self.assertIn("SELECT * FROM contacts", result)
        self.assertIn("```", result)

    def test_bulleted_list(self):
        """箇条書きが「- 」付きで変換される"""
        blocks = [make_block("bulleted_list_item", "項目A")]
        result = blocks_to_markdown(blocks)
        self.assertIn("- 項目A", result)

    def test_numbered_list(self):
        """番号付きリストが「1. 」付きで変換される"""
        blocks = [make_block("numbered_list_item", "手順1")]
        result = blocks_to_markdown(blocks)
        self.assertIn("1. 手順1", result)

    def test_quote(self):
        """引用が「> 」付きで変換される"""
        blocks = [make_block("quote", "重要な注意事項")]
        result = blocks_to_markdown(blocks)
        self.assertIn("> 重要な注意事項", result)

    def test_divider(self):
        """区切り線が「---」に変換される"""
        blocks = [{"type": "divider", "divider": {}, "has_children": False}]
        result = blocks_to_markdown(blocks)
        self.assertIn("---", result)

    def test_callout(self):
        """コールアウトが「> 💡」付きで変換される"""
        blocks = [make_block("callout", "ポイント")]
        result = blocks_to_markdown(blocks)
        self.assertIn("> 💡 ポイント", result)

    def test_toggle_with_children(self):
        """トグルブロックと子ブロックが展開される"""
        child = make_block("paragraph", "子ブロックの内容")
        toggle = make_block("toggle", "トグルタイトル")
        toggle["_children"] = [child]
        result = blocks_to_markdown([toggle])
        self.assertIn("トグルタイトル", result)
        self.assertIn("子ブロックの内容", result)

    def test_empty_blocks(self):
        """空リストは空文字を返す"""
        result = blocks_to_markdown([])
        self.assertEqual(result, "")


# ===== get_page_properties =====

class TestGetPageProperties(unittest.TestCase):

    def test_rich_text(self):
        """rich_textプロパティが取得される"""
        page = {
            "properties": {
                "メモ": {
                    "type": "rich_text",
                    "rich_text": [{"plain_text": "テストメモ"}]
                }
            }
        }
        result = get_page_properties(page)
        self.assertEqual(result["メモ"], "テストメモ")

    def test_date(self):
        """dateプロパティが取得される"""
        page = {
            "properties": {
                "作成日": {
                    "type": "date",
                    "date": {"start": "2025-01-01"}
                }
            }
        }
        result = get_page_properties(page)
        self.assertEqual(result["作成日"], "2025-01-01")

    def test_date_none(self):
        """dateがNullの場合は空文字を返す"""
        page = {
            "properties": {
                "作成日": {"type": "date", "date": None}
            }
        }
        result = get_page_properties(page)
        self.assertEqual(result["作成日"], "")

    def test_multi_select(self):
        """multi_selectプロパティがカンマ区切りで取得される"""
        page = {
            "properties": {
                "タグ": {
                    "type": "multi_select",
                    "multi_select": [{"name": "SQL"}, {"name": "Notion"}]
                }
            }
        }
        result = get_page_properties(page)
        self.assertEqual(result["タグ"], "SQL, Notion")

    def test_select(self):
        """selectプロパティが取得される"""
        page = {
            "properties": {
                "ステータス": {
                    "type": "select",
                    "select": {"name": "完了"}
                }
            }
        }
        result = get_page_properties(page)
        self.assertEqual(result["ステータス"], "完了")

    def test_select_none(self):
        """selectがNullの場合は空文字を返す"""
        page = {
            "properties": {
                "ステータス": {"type": "select", "select": None}
            }
        }
        result = get_page_properties(page)
        self.assertEqual(result["ステータス"], "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
