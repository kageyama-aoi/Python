# Tools / Python

業務・個人利用の小さなPythonツールを集めたリポジトリ。
各ツールは連番プレフィックス付きのフォルダとして独立しており、共通のGUIランチャーから起動できる。

> **公開リポジトリの注意**: 実名・顧客名・業務データを含むファイルはコミットしない。
> 実データが必要な設定は gitignore し、`*.example.json` 等のテンプレートを代わりにコミットする。

## 使い方（エントリポイント）

```bash
cd 00_ランチャー
python app.py
```

`00_ランチャー` が各フォルダの `launcher.json`（ツールの自己申告マニフェスト）を再帰探索し、
一覧・起動ボタンを自動生成する。個別ツールを直接使う場合は各フォルダの README を参照。

## ツール一覧

| フォルダ | ツール | 概要 |
|---|---|---|
| `00_ランチャー` | GUIランチャー | `launcher.json` を探索して全ツールを一覧・起動する Tkinter GUI |
| `10_スクレイピング（勤怠・TR)` | 勤怠・TR自動化 | Web上のタスクレポート入力と勤怠システムの工数実績ダウンロードを自動化する |
| `11_工数集計` | 工数集計 | タイムシートCSVから工数集計Excelレポートを生成する |
| `20_セレクタ抽出_Selenium` | セレクタ抽出（Selenium） | Webページの要素をクリックしてID/Class/XPathなどのセレクタ情報を取得する |
| `21_セレクタ抽出_Playwright` | セレクタ抽出（Playwright） | Playwright版のセレクタ検査ツール（pw-inspector） |
| `30_データ変換ツール(JSON⇔CSV⇔TSV)` | データ変換 | JSON・CSV・TSV間の変換を行う小さなスクリプト集 |
| `31_csv-excel-viewer(phpMyadmin)` | CSV Table Viewer | フォルダ内の全CSVを読み込み、見やすく整形されたExcelを生成する |
| `32_フォルダ構造Excel出力` | フォルダ構造Excel出力 | ディレクトリ構造をスキャンして階層付きExcelに出力する（ツリー表示の show_tree 同梱） |
| `33_CSV検証サポート` | CSV検証サポート | 巨大な区切りテキスト（CSV/TSV/TXT/DAT）の分割（text_splitter）と2ファイル差分比較（diff_csv）。専用ランチャー付き |
| `40_Markdown_to_HTML_出力` | Markdown to HTML | MarkdownをHTMLに変換して閲覧・管理する。一括ビルドとポータルサーバーの2モード |
| `41_PDFファイルを1つに統合` | PDF結合CLI | inputs.txt に記載されたPDFを順番どおりに1つへ結合する |
| `50_ナレッジ抽出整理（Notion）` | ナレッジ抽出（Notion） | Notion上のSQL集ページを検索し、Markdownとしてエクスポートする |
| `60_Data_Flow_Portal(データフロー書き出し)` | Data Flow Portal | イベント単位のデータフロー（DB更新の前後比較）CSVを静的HTMLで可視化する |
| `70_スクール特化型Tool` | 特化型ツール群 | 案件特化・一時利用のツール置き場（クエリ整形、JSON展開、宿泊タイムライン など） |
| `71_SQL_IN句生成` | SQL IN句生成 | CSV/テキストから値を抽出・フィルタし、SQLのIN句テキストを生成する |
| `80_(掃除)Fileを拡張子ごと振り分け` | ファイル整理 | ディレクトリ内のファイルを拡張子ごとのサブディレクトリへ振り分ける |
| `81_open_shortcut` | open_shortcut | 設定に基づいてディレクトリやURLを開くボタンを動的生成する Tkinter GUI |
| `82_日付付きファイル世代整理` | 世代整理 | 日付サフィックス付きファイルをベース名ごとに最新N件だけ残して退避する |
| `90_ひな形` | プロジェクトひな形 | 新規ツールの標準構成テンプレートと生成スクリプト（`scripts/create_project.py`） |

## リポジトリの規約

- **連番フォルダ**: `NN_ツール名` 形式。番号帯はおおまかな分類（00=基盤、10-11=勤怠系、20-21=セレクタ、
  30-33=データ変換・可視化・検証、40-41=ドキュメント/ファイル加工、50-60=ナレッジ・ポータル、
  70-71=特化型・SQL補助、80-82=ファイル整理、90=ひな形）
- **launcher.json**: ランチャーに載せるツールはフォルダ直下に置く（`name` / `description` / 起動方法を自己申告）
- **標準構成**: 新規ツールは `90_ひな形/00_project_standard.md` の構成に従う。
  `python 90_ひな形/scripts/create_project.py` でひな形から生成できる
- **実データの扱い**: `input/` `output/` `logs/` や実データ入り設定は gitignore し、
  `config.example.json` / `presets.example.json` 等のテンプレートをコミットする
- **Issue駆動**: 修正・機能追加は GitHub Issue を立ててから作業し、コミットメッセージは
  Conventional Commits（`type(scope): summary #issue`）に従う

## 必要環境

- Python 3.10+（ツールにより異なる。基本は標準ライブラリ、必要な追加ライブラリは各ツールの README を参照）
- Windows を主対象（Tkinter GUI・bat 起動・cp932 対応などWindows前提の作りが多い）
