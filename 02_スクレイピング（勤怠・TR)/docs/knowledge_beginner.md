# ナレッジ集 - 初心者編
> このプロジェクトのコードを読み解くための基礎知識

---

## 1. Pythonのファイルとimportの関係

Pythonではファイル1つが「モジュール」になります。
別のファイルの機能を使いたいときは `import` で読み込みます。

```python
# main.py の冒頭より
import config          # config.py を読み込む
import browser_utils   # browser_utils.py を読み込む
import gui             # gui.py を読み込む
```

**ポイント:** `import` したファイルの中の関数は `ファイル名.関数名()` で呼び出せます。

```python
config.load_config("config/main.yaml")   # config.py の load_config() を呼ぶ
gui.get_user_input_gui()                 # gui.py の get_user_input_gui() を呼ぶ
```

---

## 2. 関数とは何か

「処理のまとまり」に名前をつけたものです。
何度も使う処理を関数にしておくと、呼び出すだけで済みます。

```python
# browser_utils.py より
def navigate(driver, url, timeout=30):
    driver.get(url)
    wait_for_page_load(driver, timeout)
```

`def` で始まる行が関数の定義です。
`navigate(driver, url)` と書くだけでこの処理が丸ごと実行されます。

---

## 3. クラスとは何か

「データ」と「処理」をセットにしたものです。
`class` で定義し、`インスタンス = クラス名()` で使い始めます。

```python
# main.py より（簡略化）
handler = ShimamuraSearchHandler(driver, context)  # クラスから「インスタンス」を作る
handler.execute()                                   # インスタンスの処理を実行する
```

`__init__` という関数はインスタンスを作るときに自動で呼ばれる初期化処理です。

```python
class ShimamuraSearchHandler:
    def __init__(self, driver, context):
        self.driver = driver     # self.XXX に保存すると後で使える
        self.context = context
```

---

## 4. Seleniumとは何か

Pythonからブラウザを操作するライブラリです。
このプロジェクトでは「Chromeを自動で動かしてWebページを操作する」ために使っています。

```python
# ブラウザを開く
driver = webdriver.Chrome()

# URLへ移動する
driver.get("https://example.com")

# ページ上の要素を見つけてクリックする
driver.find_element(By.NAME, "submit").click()
```

このプロジェクトでは `browser_utils.py` がSeleniumの操作をまとめています。
直接Seleniumを書くのではなく、`browser_utils.navigate()` のように関数経由で使います。

---

## 5. YAMLとは何か

設定を書くためのファイル形式です（`.yaml` 拡張子）。
Pythonのコードを変えなくても、YAMLを書き換えるだけで動作を変えられます。

```yaml
# config/modes/task_report/shimamura.yaml より
task_report_settings:
  shimamura_search:
    target_status: "22.Upload check"
    new_status: "07.Merge Rq."
```

Pythonからはこう読み込みます：

```python
config.CONF.get('task_report_settings', {}).get('shimamura_search', {})
```

`CONF` は読み込んだYAMLの内容がまるごと入った辞書です。

---

## 6. エラーが出たときの読み方

エラーメッセージは下から読むのが基本です。

```
Traceback (most recent call last):
  File "main.py", line 54, in main        ← どのファイルの何行目か
    browser_utils.navigate(driver, url)   ← 実行していたコード
selenium.common.exceptions.NoSuchElementException: ...  ← エラーの種類と内容
```

**よく出るエラー:**

| エラー名 | 意味 |
|---------|------|
| `NoSuchElementException` | 指定した要素がページ上に見つからない |
| `ElementNotInteractableException` | 要素はあるが操作できない状態（非表示など） |
| `TimeoutException` | 指定した時間内に条件が満たされなかった |
| `FileNotFoundError` | 指定したファイルが存在しない |

---

## 7. `if __name__ == "__main__":` とは何か

`main.py` の末尾にある不思議な行です。

```python
if __name__ == "__main__":
    main()
```

「このファイルを直接実行したときだけ `main()` を呼ぶ」という意味です。
他のファイルから `import` されたときは `main()` が自動で実行されません。
