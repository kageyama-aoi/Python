# ナレッジ集 - 上級者編
> 「なぜその設計にしたか」を理解し、自分で判断できるようになるための知識

---

## 1. 単一責任原則（SRP）とリファクタリングの判断基準

「1つのクラス・関数は1つの理由でのみ変更される」という原則です。

**Before（リファクタリング前の main.py）:**
```python
def main():
    # 設定読み込み
    # GUI入力
    # ブラウザ初期化
    # 検索フロー（80行）
    # フォーム入力フロー
    # ファイル移動
    # 完了通知
```

これは「検索フローを変えたい」「GUI表示を変えたい」「ブラウザ設定を変えたい」など
複数の理由で `main.py` を変更しなければならない状態です。

**After（リファクタリング後）:**
- 検索フロー → `ShimamuraSearchHandler.execute()`
- ブラウザ初期化 → `browser_utils.create_driver()`
- 完了通知 → `gui.show_completion_message()`
- `main.py` はオーケストレーション（呼び出しの順番）だけを担当

「変更理由が1つ」であれば、その変更の影響範囲がそのファイルだけで済みます。

---

## 2. 依存の方向を意識した設計

このプロジェクトの依存関係：

```
main.py
  ├── gui.py
  ├── config.py
  ├── browser_utils.py
  ├── handler_factory.py
  │     ├── handlers/crowdlog_handler.py
  │     └── handlers/task_report_handler.py
  └── handlers/shimamura_search_handler.py
        └── browser_utils.py
```

**重要な原則:** 依存は「上位 → 下位」の一方向にする。
`browser_utils.py` が `main.py` を知っていたら、`browser_utils.py` だけを
テストしたり別プロジェクトで再利用したりができなくなります。

`config_manager.py` は `config.py` をインポートしています（`config.load_config()` 呼び出し）。
これは「設定保存後に設定を再読み込みする」という要件があるためで、意図した依存です。

---

## 3. グローバル変数 CONF の設計判断

`config.py` の `CONF = {}` はグローバル変数です。
グローバル変数は一般に避けるべきとされますが、このプロジェクトでは合理的な選択です。

**グローバル変数が適切な理由:**
- 設定は「起動時に1回読む、以降は読み取りのみ」というパターン
- 全モジュールから参照できる必要がある
- `config.load_config()` で初期化し、`config.CONF.get(...)` でアクセスする形が明確

**代替設計（より厳密にしたい場合）:**
```python
# Singleton パターン
class Config:
    _instance = None
    _conf = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

ただしPythonでは「モジュール自体がSingleton」として機能するため、
`config.CONF` のアプローチで十分です。

---

## 4. StaleElementReferenceException を防ぐ先読み設計

Seleniumで「要素を取得 → ページ遷移 → 取得済みの要素を操作」すると
`StaleElementReferenceException` が起きます（要素への参照が切れるため）。

このプロジェクトの解決策：**ループの前にURLを全件取り出す。**

```python
# shimamura_search_handler.py より
# NG: ループ内でrowを直接操作するとページ遷移後に参照切れ
for row in rows:
    row.click()   # 詳細ページへ遷移した後、次のrowはもう存在しない

# OK: 先に必要な情報を全部抽出してから処理する
results = []
for row in rows:
    results.append({
        "url": ...,
        "task_id": ...,
        "status": ...,
    })

for r in results:      # WebElement ではなく dict を使う
    browser_utils.navigate(self.driver, r['url'])
```

**原則:** WebElementへの参照はページ遷移で無効になる。
URLや文字列など「プリミティブな値」に変換してからループに渡す。

---

## 5. JavaScriptのchangeイベントとブラウザの内部状態

Seleniumの `Select.select_by_visible_text()` は標準的なDOM操作として動作します。
しかし一部のWebフレームワーク（Vue.js、React等）は `change` イベントを
ベースに状態管理をしており、Seleniumのデフォルト操作でイベントが発火しないことがあります。

```python
# 単なるDOM変更（フレームワークが検知しないことがある）
Select(elem).select_by_visible_text(visible_text)

# イベントを明示的に発火させる（フレームワークの状態も更新される）
driver.execute_script(
    "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", elem
)
```

`{bubbles: true}` は「イベントをDOMツリーの上位に伝播させる」オプションです。
フォーム要素の `change` イベントはバブリングが必要な場合が多いため指定します。

**デバッグ方法:** ブラウザのDeveloper Tools > Console で
`document.querySelector("select[name='status_edit']").value` を実行し、
期待する値が設定されているか確認する。

---

## 6. `ruamel.yaml` vs `yaml.safe_load` の使い分け

このプロジェクトでは2種類のYAMLライブラリを使っています。

| | `yaml.safe_load`（config.py） | `ruamel.yaml`（config_manager.py） |
|--|--|--|
| 用途 | 起動時の設定読み込み | GUI上での設定編集・保存 |
| コメント保持 | しない | する |
| 速度 | 速い | やや遅い |
| 書き込み | しない | する |

YAMLファイルを書き戻すとき `yaml.safe_load` → `yaml.dump` を使うと
コメント（`# この値は変更しないこと` 等）がすべて消えます。
`ruamel.yaml` はコメントとインデントを保持したまま書き戻せます。

---

## 7. git mv によるリネームと履歴の保持

`form_handler.py` → `handler_factory.py` のリネームに `git mv` を使いました。

```bash
git mv src/form_handler.py src/handler_factory.py
```

単純にファイルを削除・作成すると git は「削除 + 新規追加」と認識し、
`git log src/handler_factory.py` で過去のコミット履歴が追えなくなります。

`git mv` を使うと `rename` として記録されるため、履歴が引き継がれます：

```bash
git log --follow src/handler_factory.py   # リネーム前の履歴も表示される
```

**注意:** ファイルの中身を大幅に書き換えながらリネームすると、
gitが「同じファイル」と判断しなくなることがあります（類似度が低くなるため）。
リネームと内容変更は別コミットに分けるのが安全です。

---

## 8. コミットメッセージの設計（Conventional Commits）

このプロジェクトで使っているコミット規約です。

```
<type>(<scope>): <summary> #<issue番号>
```

| type | 意味 |
|------|------|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `refactor` | 動作を変えないコード整理 |
| `chore` | ビルド設定・ツール変更 |
| `docs` | ドキュメントのみの変更 |

`refactor` と `fix` を混同しないことが重要です。
`refactor` は「外から見た動作が変わらない」ことが前提です。
動作を変えながら「refactorしました」とコミットすると、
バグが起きたときに「この変更は安全なはずなのに...」と混乱します。
