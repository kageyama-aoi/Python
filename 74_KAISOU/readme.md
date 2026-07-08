# ディレクトリ構造Excel出力スクリプト (KAISOU)

指定したディレクトリ以下のフォルダ・ファイル構造を再帰的にスキャンし、階層構造付きのExcelファイルに出力するツールです。
フォルダパスにはハイパーリンクが設定され、クリックでそのフォルダをエクスプローラーで開けます。

## 機能

- 指定したルートディレクトリ以下を再帰的にスキャン
- Excel出力
  - アイテムのフルパス（フォルダはクリックで開けるハイパーリンク）
  - タイプ（フォルダ/ファイル、行の色分けで判別しやすく）
  - 階層構造をLevel1, Level2... の列で表示
  - 各列幅は内容に合わせて自動調整
- `config.json` によるカスタマイズ
  - スキャン対象のルートディレクトリ (`root_dir`)
  - 出力先ディレクトリ (`output_base_dir`) とファイル名 (`output_filename`)
  - 除外する拡張子 (`excluded_extensions`)
  - 除外するフォルダ名 (`excluded_folder_names`、大文字小文字区別なし）
- 出力ファイル名にタイムスタンプを自動付加し、同名の古い出力は確認の上で削除
- 実行ログを `logs/` にコンソール出力と合わせて記録

## 必要なもの

- Python 3.x
- `pandas`, `xlsxwriter`

```bash
pip install pandas xlsxwriter
```

## 使い方

1. `config.json` の `root_dir` に、スキャンしたいフォルダの絶対パスを指定する。
   - 未編集のデフォルト値 `"."` はこのツール自身のフォルダをスキャンする動作確認用。
2. `run_drive_structure.bat` をダブルクリックして実行する。
   - `output_base_dir` が相対パスの場合、このツールのフォルダ基準（`config.json`と同じ場所）で解決される。デフォルトは `output/`。
3. `output/` フォルダに `drive_structure_<タイムスタンプ>.xlsx` が生成される。

## config.json の設定例

```json
{
  "root_dir": "G:\\マイドライブ\\作業フォルダ\\WORK\\1234_案件名",
  "output_base_dir": "output",
  "output_filename": "drive_structure.xlsx",
  "excluded_extensions": [".log", ".tmp", ".bak", ".DS_Store", "desktop.ini"],
  "excluded_folder_names": ["OLD", "old", "backup", "アーカイブ", "不要", "output", "logs", "__pycache__"]
}
```

## ファイル構成

| ファイル/フォルダ | 説明 |
| --- | --- |
| `run_drive_structure.bat` | 実行用バッチファイル（内部で `generate_drive_structure.py` を呼び出す） |
| `generate_drive_structure.py` | スキャンとExcel出力を行うスクリプト本体 |
| `config.json` | スキャン対象・出力先・除外条件を指定する設定ファイル |
| `output/` | 出力Excelファイルの格納先（初回実行時に自動生成） |
| `logs/` | 実行ログの格納先（初回実行時に自動生成） |

## 案件ごとに使う場合

複数案件で使い回す際は、案件ごとに `config.json` の `root_dir` を書き換えて実行する。
過去の出力（案件名入りのファイル名にリネームして保管する運用を推奨）と混ざらないよう、`output/` の中身は都度整理する。
