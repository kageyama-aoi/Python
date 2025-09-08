# GUIアプリケーションのテスト入門 (`unittest`版)

このドキュメントは、`open_shortcut` アプリケーションのテストコード (`test_main.py`) がどのように書かれているかを解説し、新しいテストを自分で作成できるようになることを目的としています。

## 1. なぜテストを書くのか？

コードを修正したり、新しい機能を追加したりしたときに、「以前まで動いていた機能が、今回の修正で壊れていないか？」と不安になることがあります。

テストコードは、このような不安を解消するための「自動チェックツール」です。

- **安心感**: 修正後にテストを実行すれば、基本的な動作が保証されていることを確認できます。
- **品質向上**: バグ（不具合）を早期に発見できます。
- **効率化**: 毎回手動でボタンをクリックして確認する手間が省けます。

## 2. テストの仕組み

### テストの道具箱

今回のテストでは、Pythonに標準で付属している以下のライブラリを使用します。

- **`unittest`**: Pythonの標準テストフレームワーク。テストの構造（クラスやメソッド）や、結果を検証するための様々な機能を提供します。
- **`unittest.mock`**: 「偽物」のオブジェクト（モック）を作成するライブラリ。これを使うことで、テストに不都合な処理を置き換えることができます。

### GUIテストのアプローチ

GUIアプリケーションのテストでは、実際に画面を表示してマウスでクリックするわけではありません。代わりに、以下の手順でテストを行います。

1.  **副作用の排除**: フォルダを開く(`os.startfile`)やブラウザを起動する(`webbrowser.open_new_tab`)といった、テスト中に実行されると困る処理を、`unittest.mock`を使って何もしない「偽物」の関数に置き換えます。
2.  **操作のシミュレート**: ボタンのクリックは、Tkinterのウィジェットが持つ `.invoke()` メソッドを呼び出すことで擬似的に実行します。
3.  **結果の検証**: ボタンがクリックされた結果、「偽物」の関数が**意図した通りの引数で呼び出されたか**を確認します。

## 3. テストコードを読んでみよう (`test_main.py`の解説)

それでは、実際のコードを見ていきましょう。

### 3.1. 準備と後片付け (`setUp` / `tearDown`)

```python
class TestDirectoryOpenerApp(unittest.TestCase):
    def setUp(self):
        """各テストの前に実行されるセットアップ処理。"""
        # 1. 設定ファイルのパスを絶対パスに書き換える
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        DirectoryOpenerApp.CONFIG_FILE = os.path.join(project_root, "data", "config.json")

        # 2. テスト用のウィンドウを作成し、非表示にする
        self.root = tk.Tk()
        self.root.withdraw()

        # 3. アプリケーションのインスタンスを作成
        self.app = DirectoryOpenerApp(self.root)

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ処理。"""
        if self.root.winfo_exists():
            self.root.destroy()
```

- `setUp`メソッドは、各テストメソッド（`test_...`）が**実行される直前**に毎回呼び出されます。
  1.  テストをどこから実行しても設定ファイルを見つけられるように、パスを絶対パスに固定しています。
  2.  テスト中にGUIウィンドウが画面に表示されないように、`self.root.withdraw()`で非表示にしています。
  3.  テスト対象のアプリケーション本体 (`DirectoryOpenerApp`) を準備します。
- `tearDown`メソッドは、各テストメソッドが**実行された直後**に毎回呼び出されます。テストで使ったウィンドウを破棄し、次のテストに影響が出ないようにします。

### 3.2. テストケースの基本構造 (AAAパターン)

個々のテストメソッドは、一般的に **AAA (Arrange, Act, Assert)** という3つのステップで構成されます。

- **Arrange (準備)**: テストに必要な変数や条件を準備します。
- **Act (実行)**: テストしたい関数やメソッドを呼び出します。
- **Assert (検証)**: 実行結果が期待通りかを確認します。

### 3.3. テストケース①: ディレクトリを開くボタン

```python
@patch('os.startfile')
def test_open_directory_button_click(self, mock_startfile):
    """「ディレクトリを開く」ボタンが正しくos.startfileを呼び出すかテストする。"""
    # Arrange (準備)
    button_name = "Documents"
    button_display_text = f"📁 {button_name}"
    expected_path = "C:\\Users\\kageyama\\Documents"

    # Act (実行)
    button = self.find_button_recursively(self.app.page_container, button_display_text)
    button.invoke() # ボタンクリックをシミュレート

    # Assert (検証)
    mock_startfile.assert_called_once_with(os.path.expandvars(expected_path))
    self.assertIn(button_name, self.app.status_label.cget("text"))
```

#### `@patch('os.startfile')` の魔法

これが `unittest.mock` の機能です。

- `@patch('os.startfile')`と書くことで、このテストメソッドが実行されている間だけ、`os.startfile`が「偽物」（モック）に置き換わります。
- 置き換えられた偽物の関数は、引数 `mock_startfile` としてテストメソッドに渡されます。
- これにより、実際にフォルダが開かれるのを防ぎつつ、「どんな引数で呼ばれたか」を後から確認できます。

#### 検証 (Assert)

- `mock_startfile.assert_called_once_with(...)`: `mock_startfile`（偽物の`os.startfile`）が、`expected_path`という引数で、ちょうど1回だけ呼び出されたことを確認します。
- `self.assertIn(...)`: ステータスバーのテキストに、ボタンの名前が含まれていることを確認します。

### 3.4. テストケース②: ページを切り替えるボタン

```python
def test_show_page_button_click(self):
    """「ページ切り替え」ボタンが正しくページを切り替えるかテストする。"""
    # Arrange
    button_display_text = "→ テストメニューへ"
    target_page_name = "test_tframe"

    # Act
    button = self.find_button_recursively(self.app.page_container, button_display_text)
    button.invoke()

    # Assert
    expected_title = self.app.config["pages"][target_page_name]["window_title"]
    self.assertEqual(self.app.master.title(), expected_title)
```

このテストでは、外部の関数を呼び出すわけではないので `@patch` は不要です。
代わりに、ボタンをクリックした結果、アプリケーションの内部状態（この場合はウィンドウのタイトル）が期待通りに変化したかを `self.assertEqual` で検証しています。

## 4. 新しいテストを追加するには？ (実践編)

`config.json`に新しいボタンを追加した際のテスト作成手順を見てみましょう。

**例: パラメータ付きURLを開くボタンのテストを追加する**

1.  **テストメソッドを作成する**
    `test_` で始まる名前の新しいメソッドを `TestDirectoryOpenerApp` クラス内に追加します。

    ```python
    @patch('webbrowser.open_new_tab')
    def test_parameterized_url_button_click(self, mock_open_new_tab):
        """パラメータ付きURLボタンが正しく動作するかテストする。"""
        # ここにAAAを書いていく
    ```

2.  **準備 (Arrange)**
    `config.json` を参考に、ボタン名、表示テキスト、期待されるURLなどの情報を変数として準備します。

    ```python
    # (メソッド内)
    # Arrange
    self.app.show_page("test_shimamura") # まず目的のページに移動
    button_name = "testサイト"
    button_display_text = f"⚙️ {button_name}"
    # このテストでは、パラメータ入力欄は空のままボタンを押すことを想定
    expected_url = "https://tcns.shimamura.co.jp/"
    ```

3.  **実行 (Act)**
    ヘルパー関数を使ってボタンを探し、`.invoke()` でクリックをシミュレートします。

    ```python
    # (メソッド内)
    # Act
    button = self.find_button_recursively(self.app.page_container, button_display_text)
    button.invoke()
    ```

4.  **検証 (Assert)**
    `webbrowser.open_new_tab` が、期待通りのURLで呼び出されたかを確認します。

    ```python
    # (メソッド内)
    # Assert
    mock_open_new_tab.assert_called_once_with(expected_url)
    ```

これで新しいテストが一つ完成です！この手順に従えば、様々な機能のテストを自分でも作成できるようになります。