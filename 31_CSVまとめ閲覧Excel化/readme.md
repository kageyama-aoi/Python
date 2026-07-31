# CSV Table Viewer

CSVファイルを読み込み、見やすく整形されたExcelファイル（`view.xlsx`）を自動生成するツールです。phpMyAdminなどからエクスポートしたCSVをそのままExcelで開くと発生する問題（先頭ゼロ消失、列幅崩れなど）を回避し、閲覧に最適な形式で出力します。

## 主な機能

1. `csv/` フォルダ内の全CSVを読み込み
2. 1CSV = 1Excelシートとして出力
3. INDEXシート（表紙）を自動生成し、各シートへのハイパーリンク・行数・作成日時を表示
4. ヘッダの黒背景＋白文字、オートフィルタ、ヘッダ行固定、列幅自動調整、長文列の折り返し表示を自動適用

## フォルダ構成

```
31_csv-excel-viewer(phpMyadmin)/
    csv_table_viewer.py
    csv/
        table1.csv
        table2.csv
```

## 使い方

1. 変換したいCSVファイルを `csv/` フォルダに配置する
2. 実行する

```bash
pip install -r requirements.txt
python csv_table_viewer.py
```

3. `view.xlsx` が生成される

## 必要ライブラリ

`requirements.txt` を参照（`pandas`, `openpyxl`, `tqdm`）。

## 注意事項

- CSVの文字コードはUTF-8を想定しています。
- Excelのシート名は31文字制限があるため自動で切り詰められます。
- Excelで使用できない文字は自動で除外されます。
