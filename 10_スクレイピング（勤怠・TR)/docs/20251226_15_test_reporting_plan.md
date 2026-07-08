# テスト結果レポート化計画

## 1. 目的
`test_handlers.py` などの単体テスト実行時に、画面に結果を表示するだけでなく、ログファイル（テキストやMarkdown）として記録を残す。
これにより、「どの関数がOKだったか」を後から振り返れるようにする。

## 2. 実現案

### 案1: 標準機能でのログ保存 (Lv.1 - 即時対応)
Pythonの `unittest` は結果を標準エラー出力(stderr)に出します。これをリダイレクトでファイルに保存します。

**実行コマンド:**
```bash
# -v オプションで詳細(関数名)を表示し、結果をファイルに保存
python test_handlers.py -v 2> logs/test_result.txt
```

**出力イメージ (test_result.txt):**
```text
test_crowdlog_execution (test_handlers.TestHandlers) ... OK
test_factory_logic (test_handlers.TestHandlers) ... OK
test_task_report_execution (test_handlers.TestHandlers) ... OK

----------------------------------------------------------------------
Ran 3 tests in 0.002s

OK
```
*   **メリット**: コード変更不要。
*   **デメリット**: ファイルが毎回上書きされる（追記モード `2>>` も可能だが読みづらい）。

---

### 案2: カスタムランナーの実装 (Lv.2 - 推奨)
テストを実行し、その結果を整形して Markdown ファイルに書き出す専用スクリプト `scripts/run_tests.py` を作成する。

**仕組み:**
1.  `unittest.TestLoader` でテストを読み込む。
2.  テストを実行し、成功・失敗のリストを取得する。
3.  日付入りのファイル名（例: `logs/test_report_20251226.md`）に結果を表形式で書き込む。

**出力イメージ (Markdown):**
```markdown
# Test Report - 2025-12-26 15:30:00

| Test Module | Function Name | Result | Message |
|---|---|---|---|
| test_handlers | test_crowdlog_execution | ✅ OK | - |
| test_handlers | test_factory_logic | ✅ OK | - |
| test_handlers | test_task_report_execution | ❌ FAIL | Error info... |

**Summary**: Run 3 tests. 2 passed, 1 failed.
```

*   **メリット**: 見やすく、履歴として管理しやすい。Git管理もしやすい。
*   **デメリット**: 専用の実行スクリプトを1つ作る必要がある。

---

### 案3: Pytestの導入 (Lv.3 - 将来的)
Pythonの標準的なテストツール `pytest` を導入する。

**実行コマンド:**
```bash
pip install pytest pytest-html
pytest --html=report.html
```

*   **メリット**: ブラウザで見られるリッチなHTMLレポートが自動生成される。
*   **デメリット**: ライブラリのインストールが必要（`requirements.txt`への追加）。

## 3. 推奨手順 (案2の実装)

今の環境（標準ライブラリ中心）を維持しつつ、要望の「何の関数を回してOKだったか」を明確に残すには、**案2** がベストです。

### 実装ステップ
1.  `logs/test_reports/` ディレクトリを作成。
2.  `scripts/run_tests.py` を作成（コードは後述）。
3.  今後は `python scripts/run_tests.py` でテストを実行する。

このスクリプトがあれば、リファクタリングのたびに「実行してレポートを見る」というサイクルが確立できます。
