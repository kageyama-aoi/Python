# 02 YAML設定管理

## IT新人向け

### YAML って何？

YAML は設定を書くためのファイル形式です。
プログラムコードではなく、**人間が読み書きしやすい形式**で値を管理できます。

```yaml
# これが YAML ファイルの例（config/main.yaml）
app:
  download_dir: "data/downloads/"   # ダウンロード先フォルダ

menus:
  tr_options:
    - key: "h"
      label: "標準"
    - key: "y"
      label: "Yamaha"
```

ポイント：
- **インデント（字下げ）** で親子関係を表す
- `- ` で始まる行はリスト（複数の項目）
- `#` 以降はコメント（プログラムには影響しない）

### なぜ設定をYAMLに書くの？

**設定をコードに直接書いた場合：**
```python
project_name = "SMMs001PH"  # 変えるたびにプログラムを修正が必要
```

**YAMLに書いた場合：**
```yaml
Project: "SMMs001PH"  # YAMLだけ変えればOK。プログラムは変えなくていい
```

プログラムを触らなくても、YAMLファイルを修正するだけで動きを変えられます。

### `.env` ファイルとの違い

| ファイル | 用途 | 例 |
|---|---|---|
| `.yaml` | 機能設定・定型文 | プロジェクト名、コメント文 |
| `.env` | 秘密情報 | メールアドレス、パスワード |

パスワードを YAML に書いてしまうと、うっかり Git に上げたときに漏れます。
秘密情報は必ず `.env` に書き、`.gitignore` で除外します。

---

## 中級者向け

### PyYAML と ruamel.yaml の違い

このプロジェクトでは **2つの YAML ライブラリ** を使い分けています。

| ライブラリ | 用途 | 特徴 |
|---|---|---|
| `PyYAML` (`yaml.safe_load`) | 読み込み専用（`config.py`） | 高速・シンプル |
| `ruamel.yaml` | 読み書き両用（`config_manager.py`） | コメント・空行を保持して書き戻せる |

**なぜ 2 つ必要か？**

PyYAML でファイルを読み書きすると、**コメントが消えます**。

```python
# PyYAML で書き戻した場合（コメントが消える）
import yaml
data = yaml.safe_load(f.read())
data['key'] = 'new_value'
yaml.dump(data, f)  # # コメント行が全部消える！
```

```python
# ruamel.yaml で書き戻した場合（コメントが保持される）
from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True
data = yaml.load(f)
data['key'] = 'new_value'
yaml.dump(data, f)  # コメントがそのまま残る
```

### ディープマージの仕組み

`config.py` の `_deep_merge()` は、複数のYAMLファイルを1つの辞書に統合します。

```python
def _deep_merge(base_dict, update_dict):
    for key, value in update_dict.items():
        if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
            _deep_merge(base_dict[key], value)  # 再帰的にマージ
        else:
            base_dict[key] = value  # 上書き
```

**マージの優先順位（後勝ち）：**

```
main.yaml      → common.yaml   → shimamura.yaml
（共通設定）      （TR共通）        （Shimamura固有）
低い優先度                          高い優先度
```

`shimamura.yaml` の値が `main.yaml` の値より優先されます。

### `_meta` の役割

```python
CONF['_meta'] = {'files': {'h': 'config/modes/task_report/shimamura.yaml'}}
```

`_meta.files` は「キー → ファイルパス」の対応表です。
`config_manager.py` の `save_setting('h', ...)` が呼ばれたとき、
このマップを使って「`h` キーは shimamura.yaml に書かれている」と判断して書き戻します。

---

## 上級者向け

### 設定管理の設計判断

#### グローバル変数 `CONF` の選択理由

`config.py` は `CONF` というモジュールレベルのグローバル辞書を使っています。

```python
# config.py
CONF = {}

def load_config():
    global CONF
    CONF.clear()
    ...
```

**メリット：**
- アプリのどこからでも `from config import config; config.CONF` でアクセスできる
- シングルトン的な使い方で、設定が1つに集約される

**デメリット・注意点：**
- グローバル状態はテストの独立性を壊しやすい（今回は `monkeypatch.chdir()` で回避）
- マルチスレッド環境では競合のリスクがある（本ツールはシングルスレッドなので問題なし）

代替案として、`Config` クラスをシングルトンパターンで実装する方法があります：

```python
class Config:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load()
        return cls._instance
```

ただし今の規模ではオーバーエンジニアリングになるため、グローバル変数の方が適切な選択です。

#### ruamel.yaml のインデント設定

```python
self.yaml.indent(mapping=2, sequence=4, offset=2)
```

これは既存のYAMLファイルのフォーマットに合わせた設定です。
`sequence=4, offset=2` にすることで、リストが以下のように出力されます：

```yaml
tr_options:      # mapping=2 でキーは2スペース
  - key: "h"     # sequence=4, offset=2 でハイフンは4スペース位置
    label: "標準"
```

この設定を間違えると、Git diff が「実質的な変更なし」なのに全行変更扱いになります。

#### add_pattern の原子性問題

現在の `add_pattern()` は 2 つのファイルを別々に書き込みます：

```python
# 1. main.yaml に追記
with open(main_yaml_path, 'w') as f:
    self.yaml.dump(main_data, f)

# 2. {key}.yaml を新規作成
with open(new_yaml_path, 'w') as f:
    self.yaml.dump(new_data, f)
```

1 の後、2 の前にクラッシュすると、`main.yaml` にはキーがあるのに `.yaml` ファイルがない **不整合状態** になります。

本番システムなら以下のように対処します：
- 書き込み前にバックアップを作成
- 両方成功した場合のみ `load_config()` を呼ぶ
- 失敗時はバックアップから復元

現状の規模・用途（個人ツール）では許容できるリスクです。
