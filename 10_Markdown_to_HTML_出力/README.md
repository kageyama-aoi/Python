# Markdown to HTML ビルドツール

`md/` 配下の Markdown を `html/` に変換し、一覧ページ `html/index.html` を生成する簡易ツールです。

## 使い方

1. `md/` に Markdown（`*.md`）を配置
2. 以下のいずれかでビルド

```powershell
python build.py
```

```powershell
.\run_build.ps1
```

```bat
run_build.bat
```

## 出力

- `html/` に各 Markdown の HTML を生成
- `html/index.html` に一覧を生成
- 画像タグ（`<img>`）は、`width` 未指定の場合のみ `width="1000"` を自動付与

## 依存関係

- Python
- `markdown` パッケージ
- チェックボックス（タスクリスト）を HTML 化したい場合は `pymdown-extensions`

インストール例:

```powershell
pip install markdown pymdown-extensions
```

## Markdown 記法（推奨）

### Front Matter

Markdown先頭に以下のFront Matterを付けると、一覧ページで分類・検索しやすくなります。

```yaml
---
category: 運用手順
tags: [手順, 申請, 社内]
---
```

- `category`: 一覧ページでのグループ名（未指定時は `未分類`）
- `tags`: タグフィルタ用。`[a, b]` 形式または複数行リストに対応

### 強調用CSSクラス（本文内）

以下のクラスをMarkdown本文中のHTMLで使用できます（`html/style.css` 定義）。

- `alert`
- `danger`
- `warn`
- `note`

例:

```html
<p class="warn">期限が近い項目です。</p>
```

## 注意点

- `md` / `html` ディレクトリ名は変更しないでください（`build.py` で固定参照）
- `html/` は書き込み権限が必要です

## メンテナンス方法（最新版）

1. タグ（Front Matter）運用を変更する場合  
`build.py` の `parse_front_matter` と `index.html` 生成部分（検索・タグボタン）を合わせて更新する。

2. 強調クラスを追加・変更する場合  
`html/style.css` にクラス定義を追加し、同時にこのREADMEの「強調用CSSクラス」を更新する。

3. 画像表示ルールを変更する場合  
`build.py` の `add_default_img_width_attr` を更新する（現在は未指定時 `width="1000"` を付与）。

4. 動作確認  
`python build.py` 実行後、`html/index.html` と対象ページをブラウザ確認する。

## 参考

- 装飾前提のMarkdownに書き換えるためのプロンプト: `PROMPT.md`
