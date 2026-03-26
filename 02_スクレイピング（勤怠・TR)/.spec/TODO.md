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

## 優先度：低

## 完了済み
- [x] 初期セットアップ
- [x] リファクタリング：src/ ディレクトリ構造の再編成（T01〜T12）
