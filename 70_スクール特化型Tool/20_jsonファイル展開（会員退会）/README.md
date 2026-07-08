# 業務ロジック タイムラインビューアー

会員退会系の JSON 実行結果を、**業務ロジック理解**のために可視化する軽量ビューアーです。  
単なる JSON ビューではなく、実行順・分岐・更新有無・入力値を追えることを目的にしています。

## 主な機能
- タイムライン表示: `conditions` と `child_logic` を時系列に近い見た目で表示
- 判定ステータス: `EXECUTED / TARGET / UPDATED` をバッジで表示
- 入力スナップショット: `precondition` の入力値・意味・ラベルを一覧表示
- 業務ノート表示: `update.meta.note` / `create.meta.note` などをチップ表示
- 折りたたみ: 判定スコープと子ロジック分岐を個別・一括で展開/折りたたみ

## ディレクトリ構成
```text
.
├─ json_logic_viewer_mock.html   # エントリHTML
├─ assets/
│  ├─ css/styles.css             # スタイル
│  └─ js/app.js                  # 描画ロジック
└─ json/                         # サンプル JSON
```

## 使い方
1. ローカルサーバーを起動
```powershell
python -m http.server 8000
```
2. ブラウザで `http://localhost:8000` を開く
3. `JSONを選択` から対象ファイルを読み込む

## 想定する JSON の主要項目
- 共通: `student`, `context`
- コース: `courses[].event_name`, `courses[].precondition`
- ロジック: `courses[].conditions[]`
  - `logic_no`, `logic_name`, `executed`, `result.has_target`
  - `update.updated_records`, `update.meta.note`
  - `create.created_records`, `create.meta.note`
  - `child_logic`（再帰構造）

## 開発メモ
- フレームワーク不使用（Vanilla JS）
- 文字コードは UTF-8
- UI 変更時は以下を目視確認
  - タブ切り替え
  - 全展開/全折りたたみ
  - `child_logic` の再帰表示
  - 入力スナップショットと業務ノートの表示
