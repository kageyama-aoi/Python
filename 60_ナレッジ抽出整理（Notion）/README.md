# Project: 60_ナレッジ抽出整理（Notion）

Notion上に蓄積されたナレッジ（SQL集・サポートMTG議事録・メール対応・Notion API・テスト知見など）を抽出し、NotebookLM等で参照しやすいMarkdownナレッジ集として整理するプロジェクトです。

* これは2026-03-27 に自動生成されたプロジェクトである（当初は「60_SQL抽出」という名前でSQL集の抽出のみを対象にしていたが、対象がNotion上の複数ナレッジに広がったためリネームした）
* 初期構築担当ツール名：Claude Code Sonnet 4.6
* このプロジェクトでは、生成AIおよびスキルを積極的に活用して開発する

## 主なスクリプト

| ファイル | 説明 |
| --- | --- |
| `src/notion_sql_export.py` | Notion上の「SQL集」ページを検索し、`sql_knowledge.md`としてエクスポート |
| `src/notion_client.py` | Notion API共通処理 |
| `src/list_anken_ids.py` | 案件IDの一覧取得 |

## 出力

`.output/` 配下に、SQL・サポートMTG・メール・Notion API・テストなど各種ナレッジのMarkdownが生成されます。
