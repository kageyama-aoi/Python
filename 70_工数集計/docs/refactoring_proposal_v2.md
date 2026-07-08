# リファクタリング提案書 (v2) - CSV項目名の定義とコードの安全性向上

## 1. 現状の課題
現在のコードベースでは、CSVの項目名（例: `'社員名'`, `'分'`, `'プロジェクト名'`）や、加工後の列名（例: `'PJコード'`, `'メモ_区分'`）が、`processor.py` や `excel_writer.py` の各所に**ハードコーディング（直接記述）**されています。

これにより、以下の問題が発生しています：
1.  **変更への脆弱性**: 入力CSVのヘッダー名が変わった場合、修正箇所が多数に及びます。
2.  **可読性の低下**: 日本語の文字列がコード内に散在し、変数なのか列名なのか直感的に分かりにくい状態です。
3.  **バグの温床**: `'PJコード'` と `'プロジェクトコード'` のような似た名称の混同や、タイプミス（`'工程1'` vs `'工程１'`）が発生しやすくなっています。

## 2. 改善案：定数管理クラスの導入

これらの文字列を `src/constants.py` という新しいモジュールで一元管理することを提案します。

### 2.1 新しいファイル構成案
```text
src/
├── ...
└── constants.py  <-- 新規作成
```

### 2.2 `src/constants.py` のイメージ
項目名を「入力（CrowdLog由来）」と「出力（集計用）」に分けて定義します。

```python
class InputCols:
    """入力CSV (timesheet.csv) の列名定義"""
    YEAR = "年"
    MONTH = "月"
    DAY = "日"
    EMPLOYEE_CODE = "社員コード"
    EMPLOYEE_NAME = "社員名"
    PROJECT_CODE = "プロジェクトコード"
    PROJECT_NAME = "プロジェクト名"
    MINUTES = "分"
    START_TIME = "開始時間"
    END_TIME = "終了時間"
    MEMO = "メモ"
    CLIENT_NAME = "取引先名"
    # ... 他

class InternalCols:
    """内部処理および出力Excelで使用する列名定義"""
    # 加工後の列名
    PJ_CODE = "PJコード"      # プロジェクトコード + 名称
    WORK_HOURS = "作業時間"   # 分 / 60
    MEMO_TYPE = "メモ_区分"
    MEMO_DETAIL = "メモ_詳細"
    PROCESS_1_NAME = "工程１:名称"
    PROCESS_1_CODE = "工程１:管理コード"
    
    # 集計用（数式で使用）
    SUM_EMPLOYEE = "集計_社員名"
    SUM_PJ = "集計_PJコード"
    SUM_HOURS = "集計_工数(h)"
    SUM_BLOCK = "集計_ブロック"
    SUM_HOURS_EXTRA = "集計_工数(h)_番外"
```

### 2.3 変更後のコードイメージ (`src/processor.py`)

```python
# Before
df['PJコード'] = df['プロジェクトコード'] + ':' + df['プロジェクト名']

# After
from .constants import InputCols as IC, InternalCols as RC

df[RC.PJ_CODE] = df[IC.PROJECT_CODE] + ':' + df[IC.PROJECT_NAME]
```

## 3. 実施手順

1.  **`src/constants.py` の作成**: 上記のクラス定義を実装します。
2.  **`src/processor.py` の修正**: 文字列リテラルをすべて定数参照に置き換えます。
3.  **`src/excel_writer.py` の修正**: 列の探索や数式生成ロジックで定数を使用するように変更します。
4.  **`src/data_loader.py` の修正**: 必要に応じて参照を更新します。

## 4. 期待される効果

- **一括管理**: 項目名を変更したい場合、`constants.py` の1箇所を修正するだけで済みます。
- **IDE支援**: 入力補完が効くようになり、タイプミスがなくなります。
- **明確な意図**: どの列が「外部入力」で、どの列が「内部生成」なのかが明確になります。
