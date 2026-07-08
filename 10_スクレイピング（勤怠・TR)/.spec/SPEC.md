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

---

## 機能③：crowdlog工数入力補助UI（HTML）の統合

### 目的
`crowdlog_dur_input.html` で工数を入力し、その内容をGoogleカレンダーに登録する。
登録後は既存のcrowdlog同期フロー（Googleカレンダー → crowdlog）に乗せる。

### 全体フロー

```
① ユーザーがTkinterGUI上のWebViewでHTMLを操作して工数を入力
② 「登録して同期 ↗」ボタン押下 → JSONをPythonに渡す
③ PythonがGoogleカレンダーに工数エントリを登録
④ （手動 or 既存処理で）crowdlogのカレンダー同期ボタンを押す
```

### UI仕様（HTML側）

| 項目 | 仕様 |
|---|---|
| 表示方法 | Tkinterウィンドウ内にWebViewとして埋め込み |
| 日付 | 起動時に今日の日付を自動セット |
| 日付ナビ | `‹` `›` ボタンで前後1日移動可能 |
| 下書き保存 | `data/drafts/{date}.json` に保存 |
| 起動時の復元 | 対象日付の下書きJSONが存在すれば自動ロード |

### HTMLとPythonの通信方法（技術選定：要確認）

**候補A: `pywebview`**
- Windows11のEdge(WebView2)を利用 → JSフル対応
- `window.pywebview.api.xxx()` でPythonメソッドを直接呼び出せる
- Tkinterと共存させる場合は別ウィンドウになる可能性あり（要検証）

**候補B: `tkinterweb`**
- Tkinterウィンドウ内に完全埋め込み可能
- JSサポートが限定的 → 現HTMLの複雑なJSが動作しない可能性あり

→ **方針**: まず `pywebview` で動作検証。Tkinterとの共存が難しければ独立ウィンドウとして起動する形に切り替える。

### Pythonが受け取るJSONフォーマット

```json
{
  "date": "2025-04-07",
  "entries": [
    {
      "start": "09:00",
      "end": "10:30",
      "duration_min": 90,
      "project": "ProjectA",
      "task": "設計"
    }
  ]
}
```

### GoogleカレンダーへのAPI登録方法（技術選定：要確認）

**候補A: Selenium（ブラウザ操作）**
- 認証不要（ブラウザのログインセッションを利用）
- 実装コスト高め・動作が遅い

**候補B: GAS（Google Apps Script）Webアプリ**
- GAS側でカレンダー書き込みAPIを実装し、PythonからHTTP POSTで呼ぶ
- 軽量でシンプル・認証はGAS側で吸収できる
- GASデプロイが必要（初回のみ）

→ **方針**: GASアプローチを優先検討。GAS Webアプリを `https://script.google.com/...` にデプロイし、PythonからJSONをPOSTする。

### 下書き保存仕様

- 保存先: `data/drafts/{YYYY-MM-DD}.json`
- 保存タイミング: 「下書き保存」ボタン押下時
- 復元タイミング: WebView起動時に対象日付のJSONを読み込んでHTMLに渡す

### 対象ファイル（想定）

| ファイル | 変更内容 |
|---|---|
| `src/crowdlog_dur_input.html` | 日付動的セット・JS↔Python通信の追加 |
| `src/gui/gui.py` | WebView起動処理の追加 |
| `src/scraping/handlers/crowdlog_input_handler.py` | 新規作成：GAS POST / Selenium操作 |
| `data/drafts/` | 下書きJSON保存フォルダ（新規作成） |

### 非機能要件
- 既存のTRパターン・CrowdLog操作に影響を与えないこと
- HTMLのプロジェクト・タスク一覧は当面JSハードコードで可（将来的にYAML化の余地あり）
- GASのURLは `config/main.yaml` の `crowdlog_settings` セクションで管理する
