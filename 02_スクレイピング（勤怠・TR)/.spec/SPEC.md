# SPEC - 技術仕様・要件定義

---

## 機能①：GUIからTRパターンを新規追加する

### 目的
コードやYAMLを直接編集せず、GUIの操作だけで新しいTRパターンを追加できるようにする。

### 追加するUI

**TR詳細設定エリアに「＋ パターン追加」ボタンを設置**
- 既存の「設定編集」ボタンの隣に配置
- TRモード選択時のみ有効（CrowdLogモードでは無効）

**新規パターン作成ダイアログ**

| 項目 | 入力形式 | 制約 |
|---|---|---|
| キー（識別子） | テキスト入力 | 半角英数字、既存キーと重複不可 |
| 表示名（ラベル） | テキスト入力 | 必須 |
| 環境選択が必要か | チェックボックス | デフォルトOFF |
| Schools | ドロップダウン | マスターデータから選択（自由入力不可） |
| Project | ドロップダウン | Schoolsに連動してフィルタリング（自由入力不可） |
| Title | テキスト入力 | 任意 |
| Comments | テキストエリア（複数行） | 任意 |

### マスターデータ（main.yaml に追加）

```yaml
masters:
  schools_projects:
    shimamura:
      - "SMMs001PH"
      - "SMMN003PH"
      - "TCNz007PH"
    yamaha:
      - "YMHs001PH"
    tframe:
      - "TCNz004PH"
```

### 保存時の動作

1. `main.yaml` の `menus.tr_options` に新エントリを追記
2. `config/modes/task_report/{key}.yaml` を新規作成（school_specific_defaults 形式）
3. `config.load_config()` でリロード
4. GUIのラジオボタンを再描画して新パターンを即反映

### 保存後のYAMLイメージ（例：key=abc）

**main.yaml への追記**
```yaml
tr_options:
  - key: "abc"
    label: "ABC案件"
    requires_environment: false
```

**config/modes/task_report/abc.yaml（新規作成）**
```yaml
school_specific_defaults:
  abc:
    Schools: "shimamura"
    Project: "SMMs001PH"
    Title: "(UATxxx)-----"
    Comments: ""
```

### 対象ファイル

| ファイル | 変更内容 |
|---|---|
| `config/main.yaml` | `masters` セクションを追加 |
| `src/gui/gui.py` | 「＋ パターン追加」ボタンの追加、ダイアログ呼び出し、GUI再描画ロジック |
| `src/gui/gui_add_pattern_dialog.py` | 新規作成：パターン追加ダイアログ |
| `src/config/config_manager.py` | `add_pattern()` メソッドを追加 |

## 非機能要件
- 既存パターンの動作に影響を与えないこと
- キー重複時はエラーダイアログを表示し保存しないこと
- 追加後、GUIを再起動せず即反映されること

---

## 機能②：リファクタリング：src/ ディレクトリ構造の再編成（完了済み）

- src/config/ : 設定管理
- src/gui/    : メニュー・UI
- src/scraping/ : 画面自動操作
- src/utils/  : 汎用ユーティリティ
