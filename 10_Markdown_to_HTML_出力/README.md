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

## 依存関係

- Python
- `markdown` パッケージ
- チェックボックス（タスクリスト）を HTML 化したい場合は `pymdown-extensions`

インストール例:

```powershell
pip install markdown pymdown-extensions
```

## 注意点

- `md` / `html` ディレクトリ名は変更しないでください（`build.py` で固定参照）
- `html/` は書き込み権限が必要です

## 参考

- 装飾前提のMarkdownに書き換えるためのプロンプト: `PROMPT.md`
