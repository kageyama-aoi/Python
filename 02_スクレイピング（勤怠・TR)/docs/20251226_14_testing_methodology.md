# テスト手法と検証のノウハウ (Testing Methodology)

## 1. はじめに
本プロジェクトでは、リファクタリング後の動作検証のために `unittest` と `unittest.mock` を使用した単体テストを導入しました。
ブラウザ操作を伴う自動化ツールにおいて、実際にブラウザを起動せずに「ロジックが正しいか」を検証する手法は、開発スピードと品質を両立させるために非常に重要です。

## 2. なぜ単体テストが必要か
- **リファクタリングの安心感**: コードの構造を大きく変えた際（今回のようなハンドラの分割など）、既存の機能が壊れていないかを瞬時に確認できます。
- **デバッグの効率化**: ブラウザの起動を待つ必要がないため、数秒でテストが完了します。
- **仕様の明文化**: テストコードを見れば、「`cl` の時はどのクラスが呼ばれるべきか」といった仕様が一目でわかります。

## 3. モック（Mock）を活用したテスト手法
今回使用した `unittest.mock` は、特定の関数やオブジェクトを「偽物（モック）」に置き換えるライブラリです。

### 3.1 `browser_utils` のモック化
実際にブラウザを操作する `browser_utils.input_text` などをモックに置き換えることで、以下のメリットがあります：
- ターゲットサイトがメンテナンス中でもテストが可能。
- 実際に値を入力することなく、入力しようとした「値」や「セレクタ」が正しいかだけを検証できる。

### 3.2 依存関係の注入 (Dependency Injection)
`BaseHandler` は `driver` を引数として受け取ります。テスト時には本物の `webdriver.Chrome()` ではなく、`MagicMock()` を渡すことで、ドライバの挙動をシミュレートしています。

## 4. テストコードの解説 (`test_handlers.py`)

### 4.1 ファクトリロジックの検証
```python
def test_factory_logic(self):
    context_cl = {'schools_type': 'cl'}
    handler_wrapper = FormAutomationHandler(self.mock_driver, context_cl)
    self.assertIsInstance(handler_wrapper.handler, CrowdLogHandler)
```
`FormAutomationHandler` がコンテキストに応じて正しい具象クラス（`CrowdLogHandler` 等）を生成しているかを検証します。

### 4.2 実行フローの検証 (`@patch` の使用)
```python
@patch('handlers.task_report_handler.browser_utils')
def test_task_report_execution(self, mock_utils):
    # ...実行...
    self.assertTrue(mock_utils.input_text.called)
```
`@patch` デコレータを使うことで、そのテストの間だけ `browser_utils` をモックに差し替えます。これにより、実際のブラウザ操作をスキップしつつ、関数が呼ばれたかどうかを確認できます。

## 5. 今後の活用方法
新しいハンドラ（例：`AttendanceHandler`）を追加した際は、以下の手順でテストを拡張してください。

1.  `test_factory_logic` に、新しい `schools_type` でそのハンドラが生成されるかのテストを追加。
2.  新しいテストメソッド `test_attendance_execution` を作成。
3.  固有のロジック（特定の値が置換されているか等）を `self.assertEqual` などで検証。

このようにテストコードをメンテナンスし続けることで、ツールが大規模になっても安定した品質を維持できます。
