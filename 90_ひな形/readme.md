# 90_ひな形

今後作成するPythonプロジェクトの標準ディレクトリ構成（雛形）と、その生成スクリプトを置いています。

## 中身

| ファイル/フォルダ | 説明 |
| --- | --- |
| `00_project_standard.md` | 標準構成の定義書。ディレクトリ構成・各フォルダの役割・設計3原則を説明 |
| `scripts/create_project.py` | 標準構成の新規プロジェクトを自動生成するスクリプト |

詳細は [`00_project_standard.md`](./00_project_standard.md) を参照してください。

## 使い方

```bash
python scripts/create_project.py <新規プロジェクト名>
```

カレントディレクトリ配下に `<新規プロジェクト名>/` が作成され、`src/` `config/` `docs/` `data/` `logs/` `scripts/` `tests/` などの標準構成一式と、`.gitignore` / `README.md` / `requirements.txt` の雛形ファイルが生成されます。
