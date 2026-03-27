# Pythonユニットテスト ナレッジ集
> 対象ファイル: `tests/test_notion_export.py`
> 作成日: 2026-03-27

---

## 1. ユニットテストとは

**ユニットテスト**とは、コードの「部品（関数）」を1つずつ独立して検証するテストです。

```
ユニットテスト  → 関数単体を検証（外部依存なし）
結合テスト     → 複数モジュールの連携を検証
E2Eテスト      → 実際にAPIを叩いて全体を検証
```

このプロジェクトで行っているのは**ユニットテスト**です。
Notion APIは呼ばず、関数にデータを渡して「戻り値が正しいか」だけを検証します。

---

## 2. テストファイルの全体構造

```python
import unittest                        # ← テスト用の標準ライブラリ
from unittest.mock import MagicMock    # ← モック用

class TestExtractTitle(unittest.TestCase):   # ← テストクラス
    def test_normal(self):                   # ← テストメソッド（test_ で始める）
        page = make_page("SQL集")
        self.assertEqual(extract_title(page), "SQL集")  # ← アサーション
```

**ルール：**
- テストクラスは `unittest.TestCase` を継承する
- テストメソッドは必ず `test_` で始める（始めないと実行されない）
- 1メソッド = 1検証（1つのことだけ確認する）

---

## 3. モック（Mock）とは

### なぜモックが必要か

`notion_sql_export.py` を import すると、冒頭でこのコードが走ります：

```python
from config import NOTION_TOKEN, OUTPUT_FILE, ...
```

しかし `config.py` はAPIトークンを含む機密ファイルなのでテスト環境には置けません。
そこで **「偽物のconfigモジュール」** を差し込みます。

### モックの作り方

```python
from unittest.mock import MagicMock

# 偽物のconfigを作る
mock_config = MagicMock()
mock_config.NOTION_TOKEN = "test_token"   # ← 値を設定
mock_config.OUTPUT_FILE = "sql_knowledge.md"
mock_config.FILTER_ANKEN_IDS = []

# Pythonのモジュールキャッシュに登録する（これが重要）
sys.modules['config'] = mock_config
```

`sys.modules` はPythonが「importしたモジュールを記憶している辞書」です。
ここに偽物を登録しておくと、`from config import ...` が本物ファイルの代わりに偽物を参照します。

### MagicMock とは

`MagicMock` はどんな属性・メソッドへのアクセスも自動で受け付けてくれる万能な偽物オブジェクトです。

```python
m = MagicMock()
m.anything    # → MagicMockオブジェクトが返る（エラーにならない）
m.foo()       # → 呼び出しても正常に返る
m.bar = "実際の値"  # ← 必要な属性だけ設定できる
```

---

## 4. sys.path の操作

```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
```

`tests/` から `src/` のファイルをimportするためのパス設定です。

| コード | 意味 |
|---|---|
| `__file__` | 現在のファイル（`tests/test_notion_export.py`）のパス |
| `os.path.dirname(__file__)` | `tests/` ディレクトリのパス |
| `'..', 'src'` | 1つ上に戻って `src/` に入る |
| `sys.path.insert(0, ...)` | 検索パスの先頭に追加（最優先で検索される） |

---

## 5. ヘルパー関数

テストデータを毎回手書きすると冗長になるため、**テスト用のデータ生成関数**を用意しています。

### make_page()

```python
def make_page(title_text):
    return {
        "properties": {
            "名前": {
                "type": "title",
                "title": [{"plain_text": title_text}]
            }
        }
    }
```

Notionのページオブジェクトは実際はもっと複雑ですが、テストに必要な最小構造だけ再現しています。
これを「**テストフィクスチャ**」と呼びます。

### make_block()

```python
def make_block(btype, text="", **kwargs):
    rich_text = [{"plain_text": text}] if text else []
    block = {
        "type": btype,
        btype: {"rich_text": rich_text, **kwargs},
        "has_children": False,
    }
    return block
```

`**kwargs` でブロック種別ごとの追加パラメータ（`language="sql"` など）を受け取れるようにしています。

---

## 6. テストケースの種類

良いテストは3種類をバランスよく書きます：

### 正常系（ハッピーパス）
一番よく使われる普通の入力で、期待通りの結果が返るかを確認します。

```python
def test_normal(self):
    """通常のタイトルが取得できる"""
    page = make_page("SQL集 2025-01-01")
    self.assertEqual(extract_title(page), "SQL集 2025-01-01")
```

### 異常系（エラーケース）
おかしな入力、存在しないデータ、Nullなど。**バグが潜みやすい場所**です。

```python
def test_no_title_property(self):
    """titleプロパティがない場合はデフォルト文字列を返す"""
    page = {"properties": {"タグ": {"type": "multi_select"}}}
    self.assertEqual(extract_title(page), "（タイトルなし）")

def test_date_none(self):
    """dateがNullの場合は空文字を返す"""
    page = {"properties": {"作成日": {"type": "date", "date": None}}}
    result = get_page_properties(page)
    self.assertEqual(result["作成日"], "")
```

### 境界値
空リスト・空文字・0件など「ちょうど端っこ」の値。

```python
def test_empty_blocks(self):
    """空リストは空文字を返す"""
    result = blocks_to_markdown([])
    self.assertEqual(result, "")

def test_empty_title(self):
    """空のタイトルは空文字を返す"""
    page = {"properties": {"名前": {"type": "title", "title": []}}}
    self.assertEqual(extract_title(page), "")
```

---

## 7. アサーション（検証メソッド）の使い分け

| メソッド | 用途 | 例 |
|---|---|---|
| `assertEqual(a, b)` | `a == b` であること | 戻り値が完全一致 |
| `assertIn(a, b)` | `a in b` であること | 出力文字列に特定のテキストが含まれる |
| `assertNotIn(a, b)` | `a not in b` であること | 不要な文字列が含まれないこと |
| `assertTrue(x)` | `x` が真であること | 条件が成立すること |
| `assertFalse(x)` | `x` が偽であること | 条件が不成立であること |
| `assertIsNone(x)` | `x is None` であること | 戻り値がNoneであること |

### assertEqual vs assertIn の選び方

```python
# assertEqual: 完全一致が必要な場合（IDや短い文字列）
self.assertEqual(extract_title(page), "SQL集")

# assertIn: 長い文字列の中に含まれるかだけ確認したい場合
result = blocks_to_markdown(blocks)
self.assertIn("# 大見出し", result)   # ← 全文一致は不要、存在確認だけでOK
```

---

## 8. テストメソッドの命名規則

```
test_{何を}_{どんな条件で}_{どうなるか}
```

このプロジェクトでは docstring で補足しています：

```python
def test_date_none(self):
    """dateがNullの場合は空文字を返す"""  ← 日本語で意図を説明
```

テスト名は**仕様書の代わり**になります。
テストが通る = 「`dateがNullの場合は空文字を返す`」という仕様が守られている、という意味です。

---

## 9. 今回のバグ発見：テストが役立った実例

### 発見したバグ（Issue #59）

`test_url_list_format` を書いたときに FAIL しました。

```python
def test_url_list_format(self):
    """URLリスト形式（MCPレスポンス）"""
    page = {"properties": {"案件": ["https://www.notion.so/1ce2b53c..."]}}
    ids = extract_relation_ids(page, "案件")
    self.assertEqual(ids, ["1ce2b53c..."])  # ← 期待値
    # 実際は [] が返ってきてFAIL
```

### 原因の流れ

```python
# 修正前のコード
val = props.get("案件")   # → ["https://..."] というリストが返る

if val.get("type") == "relation":  # ← list に .get() はない！
    ...                            #   AttributeError が発生
except Exception:
    pass                           # ← 例外を黙って握りつぶす
return []                          # ← 何事もなかったように空を返す
```

### 修正

```python
# 修正後
if isinstance(val, dict) and val.get("type") == "relation":
#  ↑ 先に「dictかどうか」を確認してから .get() を呼ぶ
```

### なぜ手動確認で気づけなかったか

- スクリプトは正常終了する（エラーが出ない）
- 絞り込みが効かず全ページ取得になる症状は、データが少ない間は「多少多く取れている」程度にしか見えない
- MCPレスポンス形式が来るケースは限定的で、通常の動作確認では再現しない

---

## 10. 今後テストを追加するときのガイド

### どの関数をテストすべきか

| テストすべき | テストしなくていい |
|---|---|
| 純粋関数（引数を受け取り値を返すだけ） | APIを実際に呼ぶ関数（`get_page_blocks` など） |
| 変換・整形ロジック | `main()` の全体フロー |
| 条件分岐が多い関数 | 1行の単純な処理 |

### 新しいテストの追加手順

```python
# 1. テストクラスに新しいメソッドを追加
class TestExtractTitle(unittest.TestCase):

    def test_新しいケース(self):
        """何を確認するかを日本語で書く"""
        # Arrange: テストデータを用意
        page = make_page("テスト")

        # Act: 関数を実行
        result = extract_title(page)

        # Assert: 結果を検証
        self.assertEqual(result, "テスト")
```

`Arrange → Act → Assert`（3A パターン）を意識するとテストが読みやすくなります。

### 実行コマンド

```bash
# 60_SQL抽出/ ディレクトリで実行
python -m unittest discover tests -v

# 特定のクラスだけ実行したい場合
python -m unittest tests.test_notion_export.TestExtractTitle -v

# 特定のメソッドだけ実行したい場合
python -m unittest tests.test_notion_export.TestExtractTitle.test_normal -v
```

---

## まとめ：このテストコードで使った技術

| 技術 | 用途 | 場所 |
|---|---|---|
| `unittest.TestCase` | テストクラスの基底クラス | 全テストクラス |
| `sys.modules` への差し込み | config.pyのモック化 | ファイル先頭 |
| `MagicMock` | 偽物オブジェクトの生成 | config モック |
| `sys.path.insert` | src/ のimportパス解決 | ファイル先頭 |
| ヘルパー関数 | テストデータの共通化 | `make_page` / `make_block` |
| `assertEqual` | 完全一致の検証 | ID・短い文字列 |
| `assertIn` | 部分一致の検証 | Markdown変換結果 |
| 正常系・異常系・境界値 | テストケースの分類 | 各テストメソッド |
