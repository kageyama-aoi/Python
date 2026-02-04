# Repository Guidelines

## Project Structure & Module Organization
このリポジトリは、テキストの一覧を基に複数の PDF を結合する小さな Python CLI です。エントリーポイントはルート直下の `merge_pdfs_from_list.py` です。入力リスト（例: `inputs.txt`）はスクリプトと同じ場所に置きます。出力 PDF はコマンドラインで指定したパスに書き出され、必要な親ディレクトリは自動作成されます。現時点で `src/` や `tests/` はありません。

## Build, Test, and Development Commands
- `python -m venv .venv`: 仮想環境を作成します。
- `.venv\Scripts\Activate.ps1`: Windows PowerShell で仮想環境を有効化します。
- `pip install pypdf`: 依存ライブラリ（`pypdf`）をインストールします。
- `python merge_pdfs_from_list.py -l inputs.txt -o output\merged.pdf`: 一覧から PDF を結合して指定パスへ出力します。

## Coding Style & Naming Conventions
Python 3 と型ヒントを使用します。インデントは 4 スペース。関数・変数は `snake_case` を推奨し、モジュール名は短く説明的にします。公開関数とモジュール先頭の docstring は必須です。エラーメッセージは既存の方針に合わせ、利用者向けの日本語で記述します。

## Testing Guidelines
現在テストはありません。追加する場合は `tests/` ディレクトリを作成し、`pytest` と `test_merge_pdfs.py` のような命名規則を使ってください。少なくとも「存在しないファイル」と「暗号化 PDF」のケースを含め、実行方法（例: `pytest -q`）を文書化してください。

## Commit & Pull Request Guidelines
直近のコミットメッセージは「ツール完成」「フォルダ名修正」のように短く日本語で記載されています。同じスタイルで 1 行・簡潔・変更内容中心にまとめてください。プルリクエストには概要、実行したコマンド、使用した入力リストを記載します。出力 PDF が大きい場合は添付せず、出力パスと簡単な検証結果のみを書いてください。

## Security & Configuration Tips
入力リストには絶対パス・相対パスの両方が使えます。機密ファイルを指すリストはコミットしないでください。共有用の例ではローカルのサンプル PDF を使い、必要に応じてファイル名を伏せてください。
