# 設定ファイルの外部化計画 (YAML化)

本ドキュメントは、現在の `src/config.py` にハードコーディングされている設定データを、外部のYAMLファイル (`config.yaml`) に切り出し、アプリケーションから読み込むようにするための計画書です。

## 1. 目的

*   **設定とロジックの分離**: プログラムの再コンパイルやコード修正なしに、設定（URL、セレクタ、テンプレート文言など）を変更可能にする。
*   **メンテナンス性の向上**: 非エンジニアでも設定ファイルを編集しやすくする。

## 2. 採用フォーマット: YAML

JSONと比較して、以下の理由からYAMLを採用します。
*   **可読性**: コメントが書けるため、設定の意味を記述できる。
*   **複数行文字列**: `|` を使うことで、メールのテンプレートなどの改行を含むテキストを自然に記述できる。

**※注意**: PythonでYAMLを扱うには `PyYAML` ライブラリが必要です。(`pip install pyyaml`)

## 3. 構成案

### A. `config.yaml` (新規作成)
現在の `src/config.py` の定数定義をYAML構造に変換します。

```yaml
app:
  url: "https://taskreport.e-school.jp/bugfix.php"

selectors:
  new_bug_button:
    name: "goindex"

fields:
  Schools:
    locator: "who_edit"
    type: "select"
  Project:
    locator: "project"
    type: "text"
  # ... 他のフィールド定義

menus:
  menu_1:
    prompt: |
      今回の対象は？次の選択肢の中から入力してください
      ------------------------------------------------------
      h:標準~
      ...
  # ...

defaults:
  common:
    user: "kageyama"
    priority: "Critical"
  
  templates:
    up_request:
      category: "[KANKYOUMEI]環境_更新依頼"
      comment: |
        下記のTRに紐づくschoolmngの資材を...
        (改行やインデントが維持されます)

  school_specific:
    s: 
      - "shimamura"
      - "SMMs001PH"
      # ... リスト形式、あるいはキー付き辞書形式に整理
```

### B. `src/config.py` (修正)
定数の羅列をやめ、YAMLローダーとして機能させます。

```python
import yaml
from pathlib import Path
# ... logging関連は維持 ...

def load_config(config_path="config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# グローバルな設定オブジェクトとして保持
# (main.pyの冒頭で load_config() を呼び出し、ここに格納する想定)
CONF = {} 
```

### C. `src/main.py` & `src/form_handler.py` (修正)
`config.CONSTANT_NAME` 形式のアクセスを、辞書アクセス `config.CONF['app']['url']` 形式に変更します。

## 4. 実施ステップ

1.  **ライブラリ導入**: `pip install pyyaml` を実行（または環境確認）。
2.  **YAMLファイル作成**: `config.yaml` をプロジェクトルートに作成し、データを移行。
3.  **Configローダー実装**: `src/config.py` を書き換え。
4.  **呼び出し元修正**: `src/main.py`, `src/form_handler.py` の定数参照箇所を修正。
5.  **動作確認**: 既存のロジックがYAMLの設定値で正しく動くか確認。
