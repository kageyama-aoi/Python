# 30_データ変換ツール（JSON⇔CSV⇔TSV）

JSON・CSV・TSV間の変換を行う4つの小さなツールを、1つのGUIランチャーから使えるようにしたツール集です。
もともと別々のフォルダ（`JSON⇒TSV`・`tframe_api`）に分かれていた、役割の重なるスクリプトを1つにまとめたものです。

## 準備するもの

`data/input/` フォルダに変換したいJSON/CSVを置いてください。

```
30_データ変換ツール(JSON⇔CSV⇔TSV)/
    src/
        launcher_gui.py
        json_to_tsv_columns.py
        json_to_tsv_rows.py
        csv_to_tsv.py
        request_to_json.py
    config/
        leaf_like_keys.json
    data/            ← 実データ・生成物・ログ。丸ごとGit管理外
        input/
        output/
        logs/
    run.bat
```

## 出力されるもの

`data/output/` にツールごとの形式で出力されます（詳細は下記「ツール一覧」）。

## 起動方法

```
run.bat をダブルクリック（または 00_ランチャーから起動）
```

GUIランチャー（`src/launcher_gui.py`）が起動します。Python標準ライブラリ（Tkinter）のみで動作します。

### 画面構成

```
┌────────────────────────────────────────────────────────────┐
│ このツールについて（準備するもの／出力されるもの）             │
├────────────────────────┬───────────────────────────────────┤
│ [左ペイン]               │ [右ペイン]                        │
│  ツール一覧                │  Command（参照用・読み取り専用）│
│  実行パラメータ（ツール別）  │  Log（色付きリアルタイム表示） │
│  [▶ Run] [■ Stop]       │  出力ファイルパネル             │
│  [入力フォルダ] [出力フォルダ]│  （サイズ・件数）             │
└────────────────────────┴───────────────────────────────────┘
```

左のツール一覧から使いたいツールを選ぶと、そのツール専用のパラメータ欄に切り替わります。
「▶ Run」でサブプロセスとして実行し、ログをリアルタイムに色分け表示します。完了後、出力サマリーに
「入力ファイル名 / 出力◯ファイル・合計サイズ」を表示し、「詳細...」で各出力ファイルのサイズ・行数を確認できます。

## ツール一覧

| ツール | 変換 | 説明 |
| --- | --- | --- |
| JSON→TSV（横方向Level列） | JSON → TSV | `data/input/` からJSONファイルを選択（未選択時は最新のものを提案）。階層パスを**横方向のLevel列**に展開し、同じ値が連続する場合は`→`で省略表示。出力は`data/output/output_{タイムスタンプ}.tsv` |
| JSON→TSV（縦方向Level/Key/Value） | JSON → TSV | 階層を**縦方向のLevel/Key/Value行**に展開。ネストの深さが不揃いなデータや、行単位で見比べたい場合向け。出力は`data/output/output_levels_{タイムスタンプ}.tsv` |
| CSV→TSV 一括変換 | CSV → TSV | `data/input/` 内の全CSVファイルを一括でTSVに変換（UTF-8/Shift-JIS自動判定）。出力は`data/output/` |
| クエリ文字列→JSON | クエリ文字列 → JSON | `loginId=xxx&pwd=yyy`のようなURLクエリ文字列をテキスト入力し、JSON形式に変換・保存する。出力は`data/output/{loginId}_{タイムスタンプ}.json` |

### 使い分け（JSON→TSVの2種類）

同じJSONでも、見たい形式に応じて2種類のJSON→TSV変換を選べます。

- **横方向Level列**: 配列を含む複雑な階層データを、パスの共通部分を省略しながら俯瞰したい場合
- **縦方向Level/Key/Value**: ネストが浅いデータを、キーと値の対応がひと目で分かる行形式で見たい場合

### 矢印(→)省略の設定

「JSON→TSV（横方向Level列）」パネルの「矢印省略の設定を編集...」から、同じ値が連続しても矢印に
省略しないキー名（`config/leaf_like_keys.json`の`leaf_like_keys`）を編集できます。既定では
`value` `input_month` `has_target` `updated_records` `created_records` が対象です
（これらは実際の値を表すキー名なので、たまたま前後の行と同じ値でも省略しない）。

## GUIを使わずCLIで実行する場合

```bash
python src/json_to_tsv_columns.py [JSONファイルパス]   # 省略時はdata/input/内の最新JSON
python src/json_to_tsv_rows.py [JSONファイルパス]
python src/csv_to_tsv.py                              # data/input/内の全CSVを一括変換
python src/request_to_json.py ["loginId=xxx&pwd=yyy"]  # 省略時は対話入力
```

## 注意

- `data/`配下は実データが入るためGit管理外（`.gitignore`対象）。
- `data/logs/`・`data/output/`は起動時にバックグラウンドで、30日以上前のファイルを自動でzipアーカイブする。
- CSVの文字コードはUTF-8またはShift-JISを想定しています（両方とも判別できない場合はエラーメッセージで案内されます）。

## 経緯

- `json_to_tsv_columns.py`は旧`JSON⇒TSV/pg1.py`、`json_to_tsv_rows.py`は旧`tframe_api/②reaponse_json_to_tsv.py`を統合したものです（後者は元々JSONがハードコードされていたため、前者と同様にファイル自動検出方式に修正しています）。
- 各フォルダに残っていた作業データ（会員大会JSON、Tframe APIのサンプルCSV/TSV等）は`_archive/72_73_旧データ/`に退避しています。
- 2026-08: 4つの個別スクリプト＋4つの`.bat`がフラットに並んでいて分かりにくいという指摘を受け、33番と同様の統一GUIランチャー＋`src`/`data`/`config`構成に刷新（#147）。この際、`json_to_tsv_columns.py`の`split_path()`にあった「`courses[0]`のようにキー名の直後に配列インデックスが続くと、キー名が無言で欠落する」バグを発見・修正した。
