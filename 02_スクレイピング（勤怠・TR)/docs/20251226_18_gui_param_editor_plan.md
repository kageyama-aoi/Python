# GUI Config Editor Plan - Revised (with ruamel.yaml)

## 1. 目的
ユーザーがYAMLファイルを直接操作することなく、GUI上から恒久的な設定変更（プロジェクトコードの更新、定型文の修正など）を行えるようにする。
編集内容は実際のYAMLファイルに保存され、即座にアプリケーションに反映される。
その際、**YAML内のコメントや空行などのスタイルは保持される**（`ruamel.yaml` を使用）。

## 2. 実現イメージ (UI/UX)

### メイン画面
- [実行] ボタンの横（またはメニューバー）に、**[設定編集] ボタン** を追加する。
- このボタンは、TR種別が選択されている状態でのみ有効になる。

### 設定編集ダイアログ (別ウィンドウ)
1.  **タイトル**: "設定編集: Shimamura(本番サポート)"
2.  **編集エリア**:
    - 対象のYAMLファイル（例: `config/modes/task_report/shimamura.yaml`）から読み込んだ値が表示される。
    - **Project**: `[ SMMs001PH ]`
    - **Title**: `[ (UATxxx)... ]`
    - **Comments**: `[ sc ]` (テキストエリア)
3.  **アクション**:
    - [保存]: 変更内容をYAMLファイルに書き込み、ウィンドウを閉じる。
    - [キャンセル]: 変更を破棄して閉じる。

## 3. 技術的アプローチ

### 3.1 ライブラリの導入 (`ruamel.yaml`)
標準の `PyYAML` ではコメントが消えてしまうため、Round-Trip（読み書きしても元の状態を保持する）機能を持つ `ruamel.yaml` を導入する。

- **インストール**: `pip install ruamel.yaml`
- **requirements.txt**: 追加が必要。

### 3.2 データの読み書き (`src/config_manager.py` 新規作成)
- `ConfigManager` クラスを作成し、以下の責務を持たせる。
  - **メタデータの管理**: Configロード時に、どの設定値がどのファイル由来か（File Path）を記録しておく。
    - 例: `CONF['_meta']['files']['s'] = 'config/modes/task_report/shimamura.yaml'`
  - **値の更新**:
    - 指定されたファイルを `ruamel.yaml` でロード。
    - オブジェクトとして値を更新（`data['school_specific_defaults']['s']['Project'] = new_val`）。
    - 同じファイルにダンプ（コメントは維持される）。

### 3.3 GUIの実装 (`src/gui.py`)
- `SelectionApp` に `_open_config_editor` メソッドを追加。
- 現在選択中のモード（例: `s`）に対応する設定値を `ConfigManager` 経由で取得し、入力フォームを表示。
- 保存時は `ConfigManager.save_setting(mode, key, value)` を呼び出す。
- 保存成功後、`config.load_config()` を再実行してメモリ上の設定を最新化する。

## 4. 実装ステップ

### Step 1: 依存関係の追加
- `requirements.txt` に `ruamel.yaml` を追加し、インストール。

### Step 2: `src/config.py` の改修 (メタデータ保存)
- `load_config` 内でファイルを読み込む際、どのモードキー（`s`, `y`...）がそのファイルに含まれているかを解析し、`CONF['_meta']` にパスを保存するロジックを追加。

### Step 3: `src/config_manager.py` の実装
- `ruamel.yaml` を使った `load_for_edit`, `save` メソッドの実装。

### Step 4: GUIへの組み込み
- [設定編集] ボタンの実装と、編集ダイアログの作成。

## 5. 期待される効果
- エンジニア以外のユーザーでも安全かつ簡単に設定を変更できる。
- YAMLのコメント（手順書や注意書き）が消えないため、ファイルの可読性が維持される。
