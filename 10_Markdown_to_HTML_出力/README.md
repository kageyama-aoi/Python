# Markdown to HTML ビルドツール

`md/` 配下の Markdown を `html/` に変換し、一覧ページ `html/index.html` を生成するツールです。

## 構成

- `build.py`: Markdown -> HTML 変換本体
- `md/`: 入力 Markdown（`*.md`）
- `html/`: 出力先（各HTML、`index.html`、`style.css`）
- `run_build.ps1` / `run_build.bat`: ビルド実行ラッパー
- `app.py`: Front Matter（`category` / `tags`）編集用のローカルWebツール
- `support_tool/`: Markdown作成補助ツール（ブラウザで使う単体HTML）
- `PROMPT.md`: 文章を装飾前提Markdownに整えるためのテンプレート

## 基本の使い方（ビルド）

1. `md/` に Markdown（`*.md`）を配置
2. 以下のいずれかで実行

```powershell
python build.py
```

```powershell
.\run_build.ps1
```

```bat
run_build.bat
```

`run_build.bat` は成功時に `html/index.html` を自動で開きます。

## 出力

- `html/` に各 Markdown の HTML を生成
- `html/index.html` に一覧を生成
- 画像タグ（`<img>`）は `width` 未指定時のみ `width="1000"` を自動付与

## サポートツール

ビルド本体とは別に、補助的に使えるツールがあります。

1. メタ情報編集ツール（`app.py`）
```powershell
python app.py
```
- `http://127.0.0.1:5000/` で `md/*.md` の `category` / `tags` を一括編集
- 保存後は静的HTMLへ反映するため、`python build.py` を再実行

2. Markdown保存補助（`support_tool/`）
- `support_tool/md_saver_min.html`
- `support_tool/md_saver_min_v2.html`
- ブラウザで開いて入力したMarkdownを `YYYYMMDD_名前.md` 形式で保存可能

3. Markdownリンク/画像記法補助（`md_helper.ps1`）
```powershell
.\md_helper.ps1 -Mode link -TargetPath ".\picture\sample.png" -FromPath ".\md\guide.md"
```
- 相対パスを自動計算して Markdown 記法を生成
- `-Mode image` で画像記法も生成可能
- `-Copy` で生成結果をクリップボードへコピー

`md_helper.ps1` の実行例:

```powershell
# リンク記法を生成
.\md_helper.ps1 -Mode link -TargetPath ".\README.md"

# 画像記法を生成（md/guide.md から見た相対パスで計算）
.\md_helper.ps1 -Mode image -TargetPath ".\picture\dummy.png" -FromPath ".\md\guide.md"

# 表示名を指定して生成
.\md_helper.ps1 -Mode link -TargetPath ".\docs\template.md" -Label "テンプレート"

# 生成結果をクリップボードへコピー
.\md_helper.ps1 -Mode link -TargetPath ".\README.md" -Copy
```

主な引数:
- `-Mode`: `link` または `image`
- `-TargetPath`: リンク先/画像ファイルのパス
- `-FromPath`: 相対パス計算の基準（省略時はカレントディレクトリ）
- `-Label`: リンク表示名/画像alt（省略時はファイル名）
- `-Copy`: 生成文字列をクリップボードへコピー

## 依存関係

- Python
- `markdown`
- `pymdown-extensions`（タスクリスト `- [ ]` のHTML化で使用）
- `flask`（`app.py` を使う場合のみ）

インストール例:

```powershell
pip install markdown pymdown-extensions flask
```

## Markdown 記法（推奨）

### Front Matter

Markdown先頭にFront Matterを付けると、一覧で分類・検索しやすくなります。

```yaml
---
category: 運用手順
tags: [手順, 申請, 社内]
---
```

- `category`: 一覧でのグループ名（未指定時は `未分類`）
- `tags`: タグフィルタ用。`[a, b]` または複数行リストに対応

### 強調用CSSクラス（本文内）

`html/style.css` で以下クラスを使用できます。

- `alert`
- `danger`
- `warn`
- `note`

例:

```html
<p class="warn">期限が近い項目です。</p>
```

## 注意点

- `md` / `html` ディレクトリ名は変更しない（`build.py` で固定参照）
- `html/` は書き込み権限が必要
- `build.py` は書き込み確認のため一時ファイル `.write_test` を作成

## メンテナンス

1. Front Matter運用を変更する場合  
`build.py` の `parse_front_matter` と `index.html` 生成ロジックを合わせて更新する。

2. 強調クラスを追加・変更する場合  
`html/style.css` と、このREADMEの「強調用CSSクラス」を同時に更新する。

3. 画像表示ルールを変更する場合  
`build.py` の `add_default_img_width_attr` を更新する。

4. 動作確認  
`python build.py` 実行後、`html/index.html` と対象ページをブラウザで確認する。

## 参考

- 装飾前提Markdownへ書き換えるためのプロンプト: `PROMPT.md`
- コミットメッセージ提案時に読み込む指示文: `COMMIT_MESSAGE_INSTRUCTIONS.md`
- Markdown作成テンプレート: `docs/template.md`

`docs/template.md` の使い方:
- 新規ドキュメント作成時に `docs/template.md` をコピーして開始する
- `## Quick Links` を実ファイルに差し替える
- リンク/画像の記法は `md_helper.ps1` で生成した文字列を貼り付ける
