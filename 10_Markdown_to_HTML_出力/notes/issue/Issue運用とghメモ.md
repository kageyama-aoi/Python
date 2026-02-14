# Issue運用とghメモ

## 目的
このメモは、GitHub Issueを使って改善タスクを管理するための実務手順と、`gh`（GitHub CLI）の基礎知識をまとめたものです。

## 今回の運用方針（要約）
- Issueで課題を可視化する
- 課題は「機能追加」だけでなく「情報設計」も対象にする
- Issue本文に受け入れ条件とチェックリストを入れて進捗管理する

## Issueを作る手順（Web）
1. 対象リポジトリの `Issues` を開く
2. `New issue` を押す
3. タイトルと本文を貼り付ける
4. 必要なら `Labels` / `Assignees` / `Projects` を設定する
5. `Create` で作成する

## Issue本文に入れると良い項目
- 背景
- 現在の課題
- 目的
- 受け入れ条件（Doneの定義）
- タスクチェックリスト
- 関連ファイル

## コードやPRとの紐づけ方
1. ファイル参照を書く  
例: `README.md`, `build.py`

2. 行番号リンクを貼る  
例: `https://github.com/<owner>/<repo>/blob/<branch>/README.md#L1`

3. PRからIssueを閉じる  
PR本文に `Closes #123` または `Fixes #123` を書く

4. チェックリストで作業を見える化  
`- [ ] タスク名` をIssue本文に書く

## `gh` とは何か
`gh` は GitHub公式のCLI（コマンドラインツール）です。  
ブラウザを開かなくても、Issue/PR/リポジトリ操作をターミナルから実行できます。

### 主な利点
- Issue作成・閲覧・編集をCLIで完結できる
- PR作成やレビュー確認を高速化できる
- スクリプト化しやすく、運用を自動化しやすい

### よく使う例
```powershell
# インストール確認
gh --version

# ログイン状態確認
gh auth status

# Issue作成（対話）
gh issue create

# Issue一覧
gh issue list

# 特定Issueを表示
gh issue view 123
```

### この環境での注意
- `gh` が未インストールだとCLIからIssue作成はできない
- その場合はWebでIssueを作成する
- 後で `gh` を導入すれば、同じ運用をCLI化できる

## 推奨の次アクション
1. まずWebでIssueを1件作成して運用開始
2. 次に `gh` を導入してCLI運用に移行
3. Issueテンプレート化（`.github/ISSUE_TEMPLATE/`）で記述を標準化
