# 07 Python 構文集

このプロジェクトのコードに実際に登場している Python 構文を、
出てくるコードと一緒に解説します。

> **学習の進め方**：
> IT新人向け → 中級者向け → 上級者向けの順に読んでください。
> 「ここに書いてあるコードが読める」を目標にしています。

---

## IT新人向け：まずここから

### 1. f-string（文字列フォーマット）

変数を文字列の中に埋め込む構文です。`{}` の中に変数名を書きます。

**登場箇所**：`config_manager.py`, `gui_add_pattern_dialog.py`

```python
key = "abc"
label = "ABC案件"

# f-string（Python 3.6 以降）
message = f"パターン '{label}' を追加しました。"
# → "パターン 'ABC案件' を追加しました。"

# エラーメッセージでも使う
raise ValueError(f"キー '{key}' は既に存在します。")
```

`f"..."` の f は format（フォーマット）の略です。
`{}` の中は式なので計算も書けます：`f"合計: {1 + 2}"` → `"合計: 3"`

---

### 2. with 文（ファイルを安全に開く）

**登場箇所**：`config.py`, `config_manager.py`

```python
# with なし（古い書き方・問題あり）
f = open("config/main.yaml", "r", encoding="utf-8")
data = yaml.safe_load(f)
f.close()  # ← 忘れるとファイルが開きっぱなしになる

# with あり（現代的な書き方）
with open("config/main.yaml", "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
# ← ここを出ると自動で f.close() が呼ばれる
```

`with` ブロックを抜けると**必ず後処理（close）が実行**されます。
例外が起きても安全に閉じてくれます。

---

### 3. try / except（例外処理）

エラーが起きても処理を続けるための構文です。

**登場箇所**：`config.py`, `gui_add_pattern_dialog.py`

```python
# gui_add_pattern_dialog.py の save() 関数
try:
    manager = ConfigManager()
    manager.add_pattern(key=key, label=label, ...)  # ここでエラーが起きるかも
    messagebox.showinfo("成功", f"パターン '{label}' を追加しました。")
    dialog.destroy()
    on_saved_callback()
except ValueError as e:
    # ValueError（重複キーなど）のとき
    messagebox.showerror("エラー", str(e))
except Exception as e:
    # その他の予期しないエラーのとき
    messagebox.showerror("保存エラー", str(e))
```

**使い分け**：
- `except ValueError` → 予測できる特定のエラーに対処
- `except Exception` → 予測できない全てのエラーに対処（最後の砦）

---

### 4. 複数の戻り値（タプル）

Python の関数は複数の値を一度に返せます。

**登場箇所**：`config_manager.py`

```python
def load_for_edit(self, mode_key):
    ...
    return target_data, file_path  # 2つの値を返す

# 受け取り側（タプルアンパッキング）
data, path = manager.load_for_edit("h")
# data に target_data、path に file_path が入る

# 片方だけ必要な場合は _ で無視する慣習
data, _ = manager.load_for_edit("h")
```

---

### 5. デフォルト引数

関数の引数に「デフォルト値」を設定できます。省略した場合に使われます。

**登場箇所**：`browser_utils.py`, `config.py`

```python
# 定義（= でデフォルト値を指定）
def create_driver(width: int = 1000, height: int = 1000, implicit_wait: int = 10):
    ...

def load_config(config_path="config/main.yaml"):
    ...

# 呼び出し
create_driver()                  # width=1000, height=1000, implicit_wait=10
create_driver(width=800)         # width=800, height=1000, implicit_wait=10
create_driver(800, 600)          # width=800, height=600（位置で指定）
load_config()                    # config_path="config/main.yaml"
load_config("config/test.yaml") # 別のファイルを指定
```

---

### 6. 辞書の .get() と .items()

辞書からデータを取り出すときによく使うメソッドです。

**登場箇所**：`config.py`, `gui.py`

```python
conf = {"menus": {"tr_options": [...]}, "app": {...}}

# .get() → キーがなくても KeyError にならない
menus = conf.get("menus", {})       # なければ {} を返す
schools = conf.get("zzz_unknown")    # なければ None を返す

# [] → キーがないと KeyError（エラー）になる
menus = conf["menus"]               # "menus" がなければ KeyError

# .items() → キーと値のペアをループで取り出す
fields = {"Schools": "shimamura", "Project": "SMMs001PH"}
for field_key, field_val in fields.items():
    print(f"{field_key}: {field_val}")
# → Schools: shimamura
# → Project: SMMs001PH
```

---

### 7. pass 文

「何もしない」を明示的に書く構文です。

**登場箇所**：`base_handler.py`

```python
@abstractmethod
def execute(self):
    pass  # サブクラスで実装するので、ここは何もしない
```

空のブロックは文法エラーになるため、「意図的に空にしている」と示すために使います。

---

### 8. プライベートメソッド（`_` prefix）

名前の先頭に `_` をつけると「外から直接呼ばないでください」という意味の慣習です。

**登場箇所**：`config.py`, `gui.py`

```python
class SelectionApp:
    def _create_widgets(self):   # ← 内部実装。外から呼ばない
        ...

    def _on_mode_change(self):   # ← 内部イベント処理。外から呼ばない
        ...
```

`_` は Python の文法的な制限ではなく「チームの約束」です。
外から呼ぼうとすれば呼べますが、「設計的に公開していない」というサインです。

---

## 中級者向け：実用構文を理解する

### 9. リスト内包表記（List Comprehension）

リストをシンプルに生成する構文です。

**登場箇所**：`gui_add_pattern_dialog.py`, `config_manager.py`, テストファイル

```python
tr_options = [
    {"key": "h", "label": "標準"},
    {"key": "y", "label": "Yamaha"},
]

# 通常の for ループ
keys = []
for opt in tr_options:
    keys.append(opt["key"])
# keys = ["h", "y"]

# リスト内包表記（1行で同じことができる）
keys = [opt["key"] for opt in tr_options]
# keys = ["h", "y"]

# 条件付き（if でフィルタリング）
keys = [opt["key"] for opt in tr_options if opt["key"] != "h"]
# keys = ["y"]  ← "h" を除いたリスト
```

**実際のコード**：
```python
# config_manager.py
existing_keys = [opt['key'] for opt in config.CONF.get('menus', {}).get('tr_options', [])]
```

---

### 10. next() + ジェネレータ式

リストから「条件に合う最初の1件」を取り出す慣用句です。

**登場箇所**：`gui.py`

```python
tr_options = [
    {"key": "h", "label": "標準"},
    {"key": "y", "label": "Yamaha"},
]
current_tr_key = "y"

# for ループで書いた場合
found = None
for opt in tr_options:
    if opt["key"] == current_tr_key:
        found = opt
        break

# next() + ジェネレータ式（1行で同じことができる）
found = next((opt for opt in tr_options if opt["key"] == current_tr_key), None)
#       ↑                                                                   ↑
#   最初の1件を取る                                          見つからなかった場合のデフォルト値
```

`None` の部分を変えれば「見つからなかったときの値」をカスタムできます。

---

### 11. 三項演算子（条件式）

if/else を1行で書く構文です。

**登場箇所**：`gui_add_pattern_dialog.py`

```python
projects = ["SMMs001PH", "SMMN003PH"]

# 通常の if/else
if projects:
    default = projects[0]
else:
    default = ""

# 三項演算子（1行で同じ）
default = projects[0] if projects else ""
#          ↑ trueの値   ↑ 条件    ↑ falseの値
```

シンプルな条件分岐を読みやすく書けます。
複雑な条件には使わない方が読みやすいです。

---

### 12. lambda 式（無名関数）

名前のない小さな関数を作る構文です。

**登場箇所**：`browser_utils.py`, テストの monkeypatch

```python
# 通常の関数定義
def is_loaded(d):
    return d.execute_script("return document.readyState") == "complete"

# lambda（同じ処理を1行で）
is_loaded = lambda d: d.execute_script("return document.readyState") == "complete"

# 実際のコード：WebDriverWait の条件として直接渡す
WebDriverWait(driver, timeout).until(
    lambda d: d.execute_script("return document.readyState") == "complete"
)

# monkeypatch で「何もしない関数」に差し替える
monkeypatch.setattr("config.config.load_dotenv", lambda: None)
```

「1回しか使わない・短い処理」を渡すときに便利です。

---

### 13. クロージャ（ネストされた関数）

関数の中で定義された関数が、外の変数を参照できる仕組みです。

**登場箇所**：`gui_add_pattern_dialog.py`

```python
def open_add_pattern_dialog(parent, on_saved_callback):
    key_var = tk.StringVar()   # 外の変数

    def save():                # 内側の関数（クロージャ）
        key = key_var.get()    # ← 外の変数 key_var を参照できる！
        manager.add_pattern(key=key, ...)
        on_saved_callback()    # ← on_saved_callback も参照できる

    ttk.Button(dialog, text="追加", command=save)  # save を渡す
```

`save()` は `key_var` や `on_saved_callback` を「記憶」しています。
`command=save` でボタンに渡しても、後で呼ばれたとき正しく動きます。

**なぜ使うか**：ボタンの `command` には引数なしの関数しか渡せません。
クロージャを使うと、必要な変数を「包み込んで」渡せます。

---

### 14. isinstance()（型チェック）

変数が特定の型かどうかを確認します。

**登場箇所**：`config.py` の `_deep_merge()`

```python
def _deep_merge(base_dict, update_dict):
    for key, value in update_dict.items():
        if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
            # valueが辞書 かつ base_dictにも同じキーがある かつ base側も辞書
            _deep_merge(base_dict[key], value)  # 再帰でマージ
        else:
            base_dict[key] = value  # 辞書でなければ上書き

# isinstance の基本
isinstance(42, int)       # True
isinstance("abc", str)    # True
isinstance({}, dict)      # True
isinstance([], (list, tuple))  # True（複数の型を確認できる）
```

---

### 15. global 宣言

関数の外で定義した変数を、関数の中で「書き換える」ときに必要です。

**登場箇所**：`config.py`

```python
CONF = {}  # モジュールレベルで定義

def load_config():
    global CONF       # ← これがないと、ローカル変数として扱われる
    CONF.clear()
    CONF.update(yaml.safe_load(f))
```

**なぜ `global` が必要か**：

```python
x = 10

def change():
    x = 99        # ← global なし：新しいローカル変数 x を作るだけ
    # モジュールの x は変わらない！

def change_global():
    global x
    x = 99        # ← モジュールの x が変わる
```

`.clear()` や `.update()` は `global` なしでも動きます（変数自体を変えていないため）。
`CONF = {}` のような「再代入」には `global` が必要です。

---

### 16. 再帰関数

自分自身を呼び出す関数です。

**登場箇所**：`config.py` の `_deep_merge()`

```python
def _deep_merge(base_dict, update_dict):
    for key, value in update_dict.items():
        if isinstance(value, dict) and isinstance(base_dict.get(key), dict):
            _deep_merge(base_dict[key], value)  # ← 自分自身を呼ぶ（再帰）
        else:
            base_dict[key] = value
```

**再帰で何が解決されるか**：

```python
# ネストが何階層あっても対応できる
main = {"a": {"b": {"c": 1}}}
update = {"a": {"b": {"c": 99, "d": 2}}}
_deep_merge(main, update)
# → {"a": {"b": {"c": 99, "d": 2}}}
```

`for` ループでは「何階層深いか分からないとき」は書けません。
再帰なら「辞書でなくなるまで掘り進む」と書けます。

---

## 上級者向け：設計に関わる構文

### 17. 型ヒント（Type Hints）

引数と戻り値の型を注釈として書く構文です。実行には影響しませんが、
IDE の補完やエラー検出を助けます。

**登場箇所**：`browser_utils.py`, `config_manager.py`

```python
# 基本的な型ヒント
def input_text(driver: webdriver.Remote, attribute: str, element: str, input_value: str):
#              ↑ 型: Remote             ↑ 型: str          ...
    ...

# 戻り値の型ヒント（-> の後）
def create_driver(width: int = 1000) -> webdriver.Chrome:
    ...

def is_element_present(driver, attribute: str, element: str) -> bool:
    ...

def find_elements(driver, attribute: str, element: str) -> list:
    ...

# None を返すことを明示
def execute(self) -> None:
    ...
```

**型ヒントのメリット**：

```python
def add_pattern(self, key: str, label: str, requires_environment: bool, fields: dict):
    # key に int を渡すと IDE が警告してくれる
    # → 実行前にバグに気づける
```

型ヒントは Python 3.5 以降の機能で、`mypy` などのツールで静的検査できます。

---

### 18. 抽象クラス（ABC と @abstractmethod）

「このメソッドは必ず実装してください」を強制する仕組みです。

**登場箇所**：`base_handler.py`

```python
from abc import ABC, abstractmethod

class BaseHandler(ABC):              # ABC を継承 → 抽象クラスになる
    def __init__(self, driver, context):
        self.driver = driver
        self.context = context

    @abstractmethod                  # このデコレータをつけると「実装必須」
    def execute(self):
        pass
```

```python
# サブクラスで execute() を実装しないとエラーになる
class BrokenHandler(BaseHandler):
    pass  # execute() を書いていない！

handler = BrokenHandler(driver, context)
# → TypeError: Can't instantiate abstract class BrokenHandler
#              with abstract method execute
```

**インタフェースとしての役割**：

`BaseHandler` を見れば「全ての Handler は `execute()` を持つ」とわかります。
`main.py` は Handler の種類を気にせず `handler.execute()` を呼べます。

---

### 19. デコレータ

関数やメソッドに「追加の機能」を付け加える構文です。

**登場箇所**：`base_handler.py`（`@abstractmethod`）、テストファイル（`@pytest.fixture()`）

```python
# デコレータの基本形
@abstractmethod
def execute(self):
    pass

# これは以下と同じ意味
def execute(self):
    pass
execute = abstractmethod(execute)  # execute 関数を abstractmethod に渡して再代入
```

**pytest.fixture の例**：

```python
# conftest.py
@pytest.fixture()
def project_root(tmp_path, monkeypatch):
    # テスト用フォルダを作る処理
    ...
    return tmp_path

# テスト側で引数名に書くだけで自動的に呼ばれる
def test_何か(project_root):  # ← fixture が自動で注入される
    assert (project_root / "config").exists()
```

デコレータは「関数を受け取り、機能を追加した新しい関数を返す」高階関数です。

---

### 20. sys.path 操作（モジュール検索パス）

Python がモジュールを探す場所を追加する操作です。

**登場箇所**：`tests/conftest.py`

```python
import sys
import os

# src/ を Python のモジュール検索パスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# これにより tests/ から以下が import できるようになる
from config import config
from config.config_manager import ConfigManager
```

**なぜ必要か**：

```
プロジェクトルート/
├── src/
│   └── config/config.py  ← ここにある
└── tests/
    └── test_config.py    ← ここから import したい
```

`tests/` から `from config import config` しようとすると、
Python は `tests/config/` を探してしまいます（見つからない）。
`sys.path` に `src/` を追加することで正しく見つかります。

---

### 21. `__name__` と `__file__`（マジック変数）

Python が自動で設定する特殊な変数です。

**登場箇所**：`config.py`

```python
# config.py
def setup_logger(log_file_path, logger_name=__name__):
    #                                        ↑ モジュール名が自動で入る
    logger = getLogger(logger_name)
    ...
```

```python
# __name__ の値
# config.py を直接実行したとき：  __name__ == "__main__"
# config.py を import したとき：  __name__ == "config.config"（パッケージ名.モジュール名）

# __file__ の値
# このスクリプト自身のファイルパス
os.path.dirname(__file__)  # そのファイルが置かれているフォルダ
```

`conftest.py` で `os.path.dirname(__file__)` を使って `src/` の場所を特定しているのはこのためです。

---

## まとめ：構文の出現マップ

| 構文 | 難易度 | 主な登場ファイル |
|---|---|---|
| f-string | 初級 | config_manager.py, gui_add_pattern_dialog.py |
| with文 | 初級 | config.py, config_manager.py |
| try/except | 初級 | config.py, gui_add_pattern_dialog.py |
| 複数の戻り値 | 初級 | config_manager.py |
| デフォルト引数 | 初級 | browser_utils.py, config.py |
| .get() / .items() | 初級 | config.py, gui.py |
| pass文 | 初級 | base_handler.py |
| _prefix（プライベート） | 初級 | config.py, gui.py |
| リスト内包表記 | 中級 | config_manager.py, gui_add_pattern_dialog.py |
| next() + ジェネレータ式 | 中級 | gui.py |
| 三項演算子 | 中級 | gui_add_pattern_dialog.py |
| lambda | 中級 | browser_utils.py |
| クロージャ | 中級 | gui_add_pattern_dialog.py |
| isinstance() | 中級 | config.py |
| global宣言 | 中級 | config.py |
| 再帰 | 中級 | config.py |
| 型ヒント | 上級 | browser_utils.py, config_manager.py |
| 抽象クラス（ABC） | 上級 | base_handler.py |
| デコレータ | 上級 | base_handler.py, conftest.py |
| sys.path操作 | 上級 | conftest.py |
| \_\_name\_\_ / \_\_file\_\_ | 上級 | config.py, conftest.py |
