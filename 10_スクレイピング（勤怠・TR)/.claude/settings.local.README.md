# settings.local.json 設定メモ

## ファイル参照系（読み取りのみ）
- `Bash(ls:*)` … ディレクトリ一覧
- `Bash(cat:*)` … ファイル内容表示
- `Bash(head:*)` … ファイル先頭表示
- `Bash(tail:*)` … ファイル末尾表示
- `Bash(wc:*)` … 行数・文字数カウント
- `Bash(sort -k2)` … ソート

## Git：状態確認・履歴（読み取り系のみ）
- `Bash(git status:*)` … 変更状態確認
- `Bash(git log:*)` … コミット履歴確認
- `Bash(git diff:*)` … 差分確認
- `Bash(git show:*)` … コミット内容確認
- `Bash(git branch:*)` … ブランチ一覧確認
- `Bash(git remote:*)` … リモート確認

> git add / commit / push などの書き込み系は都度確認が入ります。

## gh CLI：issue管理
- `Bash(gh issue:*)` … list / view / create / close / edit / comment すべて対応

## スキル実行
- `Skill(update-config)` … 設定ファイル更新スキル
