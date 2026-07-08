# Pythonコード リファクタリング計画

## 1. 現状の課題分析

`main.py` を中心とした現在のコードベースには、以下の課題が見受けられます。

### 1.1 構造・設計面
- **手続き型スクリプト**: 全体の処理が `main.py` にベタ書きされており、再利用性やテスト容易性が低いです。
- **責務の混在**: データ読み込み、加工、Excel操作（書き込み・書式設定）、ファイル削除などが混在しています。
- **グローバル汚染**: 定数や変数がグローバルスコープに定義されており、インポートしただけで副作用（ファイル削除など）が発生する構造になっています。

### 1.2 パフォーマンス・効率面
- **過剰なI/O操作**: 処理の過程で一時ファイル（`output_summary_...`, `temp_file1`, `temp2_...`）を何度も保存・読み込み・再保存しており、処理速度とディスクI/Oの無駄が発生しています。
- **ループ処理**: `iterrows` を使用した行ごとの処理があり、Pandasの高速なベクトル処理の恩恵を受けられていません。

### 1.3 保守性・可読性
- **マジックナンバー/文字列**: 列番号（`column=15`など）やファイル名がコード中に散在しており、レイアウト変更時の修正が困難です。
- **Excel数式の埋め込み**: Pythonコード内で文字列としてExcel数式（`=SUMIFS(...)`）を組み立てており、非常に読みづらくバグの温床となりやすいです。
- **未使用・冗長なコード**: 空のファイル（`config.py`等）や未使用のインポート（`math.nan`等）が存在します。

## 2. リファクタリング方針

### 2.1 モジュール分割（構成案）

機能を明確に分離するため、以下の構成への変更を推奨します。

```text
src/
├── config.py          # 定数、設定読み込み
├── data_loader.py     # CSV/JSONの読み込み
├── processor.py       # Pandasによるデータ加工・集計
├── excel_writer.py    # OpenPyXLを用いたExcel出力・装飾
└── utils.py           # 汎用関数（ファイル削除など）
main.py                # エントリーポイント（全体の制御）
```

### 2.2 具体的な改善点

1.  **PandasとOpenPyXLの役割分担**
    -   **Pandas**: データのフィルタリング、並べ替え、値の計算に集中させます。
    -   **OpenPyXL**: 最終的なExcelへの書き込み、数式の埋め込み、書式設定（色、罫線、列幅）を担当します。一時ファイルを介さず、メモリ上で完結させるか、一度の保存で済むようにします。

2.  **設定の外部化と型ヒント**
    -   `config.json` の読み込みを専用関数化し、型ヒント（Type Hints）を導入してコードの意図を明確にします。
    -   `pathlib` モジュールを使用して、OSに依存しない堅牢なパス操作を行います。

3.  **Excel数式生成のロジック改善**
    -   Python側で計算できるものはPythonで計算し（値として出力）、ユーザーが「数式であること」を必須とする場合のみ数式を出力します。
    -   数式生成ロジックをヘルパー関数に切り出し、可読性を高めます。

## 3. リファクタリング詳細ステップ

### Step 1: 定数と設定の整理 (`config.py`)
パス、色コード、列名などの定数を一元管理します。

```python
# src/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / 'output'
INPUT_DIR = BASE_DIR / 'input'
CONFIG_FILE = BASE_DIR / 'config.json'

# Excel Styles
COLOR_HEADER = '009999'
COLOR_SUB_HEADER = 'B8CCE4'
```

### Step 2: データ処理の分離 (`processor.py`)
`process_timesheet` 関数内のロジックを整理し、DataFrameを返す純粋な関数にします。

```python
# src/processor.py
import pandas as pd

def filter_timesheet(df: pd.DataFrame, target_project: str, target_employee: str) -> pd.DataFrame:
    if target_project:
        df = df[df['取引先名'] == target_project]
    if target_employee:
        df = df[df['社員名'] == target_employee]
    return df

def aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    # 月次集計ロジック
    ...
    return summary_df
```

### Step 3: Excel出力の効率化 (`excel_writer.py`)
一時ファイルの作成をやめ、単一のWorkbookオブジェクトに対して操作を行います。

```python
# src/excel_writer.py
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def create_report_workbook(processed_df: pd.DataFrame, summary_df: pd.DataFrame) -> Workbook:
    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = "Monthly Summary"
    
    # DataFrameを直接書き込み
    for r in dataframe_to_rows(summary_df, index=False, header=True):
        ws_summary.append(r)
        
    # 書式設定や数式挿入もここで行う
    ...
    return wb
```

### Step 4: エントリーポイントの作成 (`main.py`)

```python
# main.py
from src import config, data_loader, processor, excel_writer

def main():
    # 設定読み込み
    settings = data_loader.load_config()
    
    # データ読み込み
    df = data_loader.load_csv(config.INPUT_DIR / 'timesheet.csv')
    
    # 加工
    df_filtered = processor.filter_timesheet(df, settings['target_project'], ...)
    
    # 出力
    wb = excel_writer.create_report_workbook(df_filtered)
    wb.save(config.OUTPUT_DIR / 'result.xlsx')

if __name__ == "__main__":
    main()
```

## 5. 運用バッチファイルの修正 (`03_click_this_kensho.bat`)

スクリプトの構成変更に合わせて、実行用のバッチファイルも以下のように改善することを推奨します。

```batch
@echo off
setlocal
cd /d %~dp0

REM --- ログディレクトリの作成 ---
if not exist "error_log" mkdir error_log

REM --- 日時取得 ---
set "DATETIME=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "DATETIME=%DATETIME: =0%"
set "LOG_FILE=./error_log/log_%DATETIME%.txt"

echo [%DATE% %TIME%] Execution started. > "%LOG_FILE%"

REM --- Python実行 (標準出力とエラー出力の両方を記録) ---
REM 実行するスクリプトが src/main.py に移動した場合は、以下を src/main.py に書き換えます
python ./main.py >> "%LOG_FILE%" 2>&1

if %ERRORLEVEL% equ 0 (
    echo [%DATE% %TIME%] Success! >> "%LOG_FILE%"
) else (
    echo [%DATE% %TIME%] Error occurred. Level: %ERRORLEVEL% >> "%LOG_FILE%"
    echo エラーが発生しました。詳細は %LOG_FILE% を確認してください。
)

pause
endlocal
exit
```

### 改善のポイント
-   **一元的なログ管理**: `2>` (エラーのみ) ではなく `>> "%LOG_FILE%" 2>&1` とすることで、通常の出力とエラーの両方を一つのファイルに時系列で記録します。
-   **エラーレベルのチェック**: `if %ERRORLEVEL%` を使うことで、失敗したときにコンソールで即座に気づけるようになります。
-   **環境変数の局所化**: `setlocal` を使用して、他のプロセスに影響を与えないようにします。

## 6. 構成案への移行手順

現在のルートディレクトリにあるスクリプト群は、`src` ディレクトリ配下へ適切に移動・分割することを推奨します。

- `main.py` (ルート): アプリケーション実行用
- `src/`: ロジック格納用
- `input/`: 入力データ
- `output/`: 出力データ（`.gitignore` で無視設定推奨）
- `tests/`: ユニットテスト（将来的な品質担保のため）

この計画に基づき、段階的にコードの移行を行うことで、安全かつ確実なリファクタリングが可能になります。
