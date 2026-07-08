# PDF結合CLI

入力リスト（テキスト）に記載された PDF を、順番どおりに 1 つへ結合する小さな Python CLI です。  
出力先ディレクトリは自動作成されます。

## 使い方
1. （任意）仮想環境を用意
   - `python -m venv .venv`
   - `.venv\Scripts\Activate.ps1`
2. 依存関係をインストール
   - `pip install -r requirements.txt`
2. 入力リストを作成（例: `inputs.txt`）
   - 1 行に 1 つの PDF パス
   - 空行、`#` から始まる行は無視
3. 実行
   - `python merge_pdfs_from_list.py -l inputs.txt -o output\merged.pdf`

## 入力リストの例
```
# 見出し
docs\part1.pdf
docs\part2.pdf
```

## スクリプト構成
- `merge_pdfs_from_list.py`: メインの PDF 結合 CLI
- `inputs.txt`: サンプルの入力リスト
- `output\`: 出力 PDF の配置先（自動作成）
- `pickup_index.py`: docstring 付き Python を走査して CSV 化する補助スクリプト

## エラーハンドリング
- ファイルが存在しない場合は `FileNotFoundError` を送出します。
- 暗号化 PDF は空パスワードでの解除を試み、失敗時は `RuntimeError` で停止します。

## 開発メモ
- インデントは 4 スペース、型ヒントを使用します。
- 公開関数とモジュール先頭に docstring を付けてください。
 - 依存関係は `requirements.txt` で管理します。

## ライセンス
未設定です。必要に応じて追加してください。
