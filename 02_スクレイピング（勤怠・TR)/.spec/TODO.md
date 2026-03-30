# TODO - タスクリスト

## 優先度：高

### 機能①：GUIからTRパターンを新規追加する

- [ ] T01: `config/main.yaml` に `masters.schools_projects` セクションを追加
- [ ] T02: `src/config/config_manager.py` に `add_pattern()` メソッドを追加
- [ ] T03: `src/gui/gui_add_pattern_dialog.py` を新規作成（パターン追加ダイアログ）
          - キー・ラベル・requires_environment 入力
          - Schools ドロップダウン（マスターデータから）
          - Project ドロップダウン（Schools連動）
          - Title・Comments 入力
          - キー重複チェック
          - 保存処理（main.yaml追記 + {key}.yaml新規作成）
- [x] T04: `src/gui/gui.py` に「＋ パターン追加」ボタンを追加
- [x] T05: `src/gui/gui.py` に保存後のGUI再描画ロジックを追加

## 優先度：中

### 機能③：crowdlog工数入力補助UI（HTML）の統合

#### Phase 1: 技術検証
- [x] T10: `pywebview` のインストール・Tkinter共存の動作検証（サブプロセス方式で解決）
- [x] T11: `pywebview` から Python メソッドを呼び出す最小サンプルで疎通確認

#### Phase 2: HTML改修
- [x] T12: HTML の日付表示を動的化（起動時に今日の日付をPythonから渡す）
- [x] T13: 日付ナビ `‹` `›` の動作実装（前後1日移動）
- [x] T14: 「下書き保存」ボタン → `window.pywebview.api.save_draft(json)` 呼び出しに変更
- [x] T15: 「登録して同期 ↗」ボタン → `window.pywebview.api.submit(json)` 呼び出しに変更
- [ ] T16: 起動時に下書きJSONが存在すれば `allRows` を復元する処理を追加

#### Phase 3: Python バックエンド実装
- [ ] T17: `data/drafts/` フォルダ作成・`.gitkeep` 配置、`.gitignore` に `data/drafts/*.json` を追加
- [ ] T18: `src/gui/gui.py` に WebView 起動処理を追加（既存GUIから呼び出せる形で）
- [ ] T19: GAS Webアプリの実装・デプロイ（カレンダーへの工数エントリ書き込み）
- [ ] T20: `src/scraping/handlers/crowdlog_input_handler.py` を新規作成（GAS への HTTP POST処理）
- [ ] T21: `config/main.yaml` の `crowdlog_settings` に GAS URL を追加

#### Phase 4: 結合・動作確認
- [ ] T22: HTML → Python → GAS → Google Calendar の End-to-End 動作確認
- [ ] T23: 下書き保存・復元の動作確認

## 優先度：低

## 完了済み
- [x] 初期セットアップ
- [x] リファクタリング：src/ ディレクトリ構造の再編成（T01〜T12）
