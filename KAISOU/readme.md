# ディレクトリ構造Excel出力スクリプト (KAISOU)

指定されたディレクトリの構造（フォルダとファイル）をスキャンし、Excelファイルに出力するPythonスクリプトです。
指定されたルートディレクトリ以下のフォルダ・ファイル構造をスキャンし、Excelファイルに出力するPythonスクリプトです。
Excelでは、アイテムのタイプ（フォルダ/ファイル）に応じた書式設定や、フォルダパスへのハイパーリンクが設定されます。

## 機能
Unchanged lines-   指定したルートディレクトリ以下のフォルダ・ファイル構造を再帰的にスキャン
-   スキャン結果をExcelファイルに出力
    -   アイテムのフルパス（フォルダの場合、クリックで開けるハイパーリンク）
    -   アイテムのタイプ（フォルダ/ファイル）
    -   アイテムのタイプ（フォルダ/ファイル、Excelの左端に表示）
    -   階層構造をLevel1, Level2... の列で表示
    -   アイテム名
-   Excel出力時の書式設定
Unchanged lines    -   ファイル行: 薄い水色背景
    -   各列の幅を内容に合わせて自動調整
-   設定ファイル (`config.json`) による柔軟なカスタマイズ
    -   スキャン対象のルートディレクトリ (`root_dir`)
    -   Excelファイルの出力先ディレクトリ (`output_base_dir`) とファイル名 (`output_filename`)
    -   スキャン対象から除外するファイル拡張子（例: `.log`, `.tmp`） (`excluded_extensions`)
    -   スキャン対象から除外するフォルダ名（例: `OLD`, `backup`、大文字・小文字区別なし） (`excluded_folder_names`)
-   タイムスタンプ付きのExcelファイル名生成
-   出力ファイル名にタイムスタンプを自動付加
-   古い出力ファイル（同じベース名でタイムスタンプが異なるもの）の削除確認機能
-   実行ログの記録（コンソールとログファイルの両方）
-   エラー発生時の詳細なログ記録と制御された終了

## 必要なもの

## インストール

Unchanged lines
スクリプトと同じディレクトリにある `config.json` ファイルを編集して、動作をカスタマイズします。

```json
```jsonc
{
  "past_root_dir": "G:\\マイドライブ\\作業フォルダ\\WORK",
  "root_dir": "G:\\.shortcut-targets-by-id\\1zn8aWqqs4R3t1zaPqJ-EbyXnDecmJKAZ\\001.Customers(AN)\\1477_島村楽器",
  // スキャン対象のルートディレクトリ (必須)
  "root_dir": "G:\\.shortcut-targets-by-id\\1zn8aWqqs4R3t1zaPqJ-EbyXnDecmJKAZ\\001.Customers(AN)\\1477_島村楽器\\08_詳細設計",
  "output_base_dir": "C:\\Users\\kageyama\\Tools\\KAISOU",
  "output_filename": "drive_structure.xlsx",
}