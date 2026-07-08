# ナレッジ集 - 中級者編
> 初心者編を読んだ次のステップ。「なぜそう書くのか」を理解する

---

## 1. クラスの継承と抽象クラス

`BaseHandler` はすべてのハンドラの「共通の型」を定義しています。

```python
# handlers/base_handler.py
from abc import ABC, abstractmethod

class BaseHandler(ABC):
    def __init__(self, driver, context):
        self.driver = driver
        self.context = context

    @abstractmethod
    def execute(self):
        pass   # サブクラスで必ず実装しなければならない
```

`ABC` (Abstract Base Class) を継承すると、`@abstractmethod` をつけたメソッドを
実装しないサブクラスはエラーになります。「実装漏れ」をコードで防げます。

```python
class CrowdLogHandler(BaseHandler):
    def execute(self):      # これを書かないとエラー
        ...

class TaskReportHandler(BaseHandler):
    def execute(self):      # これを書かないとエラー
        ...
```

**なぜ使うか:** 新しいハンドラを追加するとき「execute() を必ず書く」というルールを
コード自体に埋め込めるため、チームや将来の自分へのドキュメントになります。

---

## 2. ファクトリパターン

`handler_factory.py` で使っているパターンです。
「条件によって異なるオブジェクトを生成する」処理を1箇所にまとめます。

```python
# handler_factory.py
class HandlerFactory:
    def __init__(self, driver, context):
        self.handler = self._create_handler()

    def _create_handler(self):
        school_type = self.context.get('schools_type')
        if school_type == 'cl':
            return CrowdLogHandler(self.driver, self.context)
        else:
            return TaskReportHandler(self.driver, self.context)

    def execute(self):
        self.handler.execute()
```

呼び出し側（`main.py`）は「どのハンドラか」を気にしなくてよくなります：

```python
# main.py - school_typeが何であれこの1行で済む
HandlerFactory(driver, context).execute()
```

---

## 3. Seleniumの要素取得パターン

`browser_utils.py` を使う前提での3つの基本操作です。

```python
# 1. 名前で要素を取得する（<input name="username">）
browser_utils.find_element(driver, "name", "username")

# 2. CSSセレクタで取得する（より詳細に絞り込める）
browser_utils.find_element(driver, "css", "select[name='status_edit']")

# 3. リンクテキストで取得する（<a>タグのテキスト）
browser_utils.find_element(driver, "link text", "ログイン")
```

**CSSセレクタが重要な理由:**
ページに同じ `name` の要素が複数あるとき、`name="status"` だけでは最初にマッチした
要素が返ります。`select[name='status_edit']` のようにタグ名も指定すると意図した
要素に絞り込めます（このプロジェクトで実際に発生したバグの原因でした）。

---

## 4. 例外処理のパターン

```python
# main.py
try:
    # 失敗するかもしれない処理
    handler.execute()
except Exception as e:
    logger.error(f"An error occurred: {e}", exc_info=True)
    raise e    # 再度例外を投げる（呼び出し元にも伝える）
```

`exc_info=True` をつけるとスタックトレース（どの行でエラーが起きたか）も
ログファイルに記録されます。`raise e` で再度例外を投げることで処理を止めています。

**try-except を使いすぎない:** エラーを握りつぶす（例外を無視する）と、
問題が起きても気づけなくなります。本当に無視していい例外だけにしましょう。

```python
# browser_utils.py - body クリックのエラーは致命的でないため無視している例
def click_body(driver):
    try:
        find_element(driver, "tag", "body").click()
    except Exception:
        pass   # これは意図的な無視（コメントで理由を書くとなお良い）
```

---

## 5. JavaScript実行による操作

Seleniumの通常操作（`click()`, `send_keys()`）では動かない場合、
JavaScriptを直接実行することで解決できます。

```python
# 要素の値をJSで直接セットする（send_keysより高速）
driver.execute_script("arguments[0].value = arguments[1];", elem, text)

# クリックをJSで実行（要素が他の要素に隠れている場合など）
driver.execute_script("arguments[0].click();", target_element)
```

`arguments[0]`, `arguments[1]` はPython側から渡した引数です。
`execute_script("...", arg1, arg2)` の `arg1` が `arguments[0]` に対応します。

---

## 6. セレクトボックス操作でハマったバグと解決策

このプロジェクトで起きた実際のバグです。

**問題:** `select_by_visible_text()` でドロップダウンを変更しても、
保存時にステータスが変わらなかった。

**原因:** Seleniumはドロップダウンの値を変えられるが、ページのJavaScriptが
`change` イベントを受け取っていないと、フォーム送信時に内部状態が更新されない。

**解決策:** 値を変えた後に `change` イベントを明示的に発火させる：

```python
# browser_utils.py の select_option_by_text()
elem = find_element(driver, attribute, element)
Select(elem).select_by_visible_text(visible_text)
# changeイベントをdispatchしてページの内部状態を更新する
driver.execute_script(
    "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", elem
)
```

---

## 7. ページ読み込みの待機

Seleniumで「要素が見つからない」エラーが起きる原因の多くは「ページがまだ読み込み中」です。

```python
# browser_utils.py
def wait_for_page_load(driver, timeout=30):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
```

`document.readyState == "complete"` はブラウザが「ページの読み込みが完全に終わった」
と判断した状態です。`timeout` 秒待っても完了しない場合は `TimeoutException` になります。

`implicitly_wait(10)` との違い：
- `implicitly_wait` : 要素を探すときに最大10秒待つ（要素単位）
- `wait_for_page_load` : ページ全体の読み込み完了を待つ（ページ単位）
