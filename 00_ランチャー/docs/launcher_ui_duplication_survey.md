# ランチャー系GUIコードの重複調査

- 調査日: 2026-07-31
- 調査範囲: `C:\Users\kageyama\Tools\Python` 配下全体
- ステータス: 調査完了。**2026-08-28 (#162)** に `00_ランチャー` 側を `theme.py` へ切り出し済み

## 2026-08-28 更新（#162）

- `00_ランチャー/app.py` からテーマ／フォント／ボタン3段階スタイル／`style_titlebar`
  （下表 #1〜#5 の 00 側）を `00_ランチャー/theme.py` に抽出した。`81_open_shortcut/src/theme.py`
  と同型で、関数 `apply_theme(root)` / `style_titlebar(window)` を公開する。
- 設定エディタ（`ConfigEditorWindow` / `IniConfigEditorWindow`）は `00_ランチャー/config_editors.py`
  に分離し、JSON型ラウンドトリップ・INI行置換を純関数化して `tests/test_config_editors.py` を追加。
- 以降の下表の行番号は分割前の app.py のもの。00 側の該当コードは `theme.py` / `config_editors.py`
  に移動している。
- **残タスク**: `00_ランチャー/theme.py` と `33_テキスト・CSV前処理サポート/launcher_gui.py` の
  テーマ部分がまだ二重管理。両者が対等に参照できる共通モジュール（第3の場所）への集約は未着手。

## 背景・目的

Python配下の各ツールはそれぞれ独立した起動用コード（`run.bat` や、ツール内蔵のTkinter GUI）を持っている。
「これらは共通化できないのでは」という認識について検証するため、実装を読んで重複の有無・範囲を洗い出した。

## 結論（3層に分けて評価）

| レイヤー | 判定 | 理由 |
|---|---|---|
| 各ツール直下の `run.bat` | 共通化**不要** | 4〜6行、差分は起動コマンド1行のみ。Explorerダブルクリックの入口として各フォルダに実体が要る制約があり、共通化しても間接層が増えるだけでメリットが薄い |
| GUIランチャー本体のテーマ/スタイル定型部分 | 共通化**候補あり** | 3ファイルで独立に再実装されている（詳細下記）。うち1件は自己申告コメントで重複を認識済み |
| 各ツール固有のビジネスロジック部分（設定エディタの中身、クリーンアップ処理等） | 対象外 | 中身がツールごとに異なり、無理に共通化する意味がない |

## 重複箇所の詳細

対象3ファイル:

- `00_ランチャー\app.py`（外付け・非侵襲型の親ランチャー。全ツールのlauncher.jsonを読んで起動する）
- `33_テキスト・CSV前処理サポート\launcher_gui.py`（内蔵型ランチャー。text_splitter/diff_csvを起動・監視する）
- `81_open_shortcut\src\theme.py`（+ 呼び出し元の `main.py` / `settings_editor.py` / `button_form.py`）

### 確実に一致（優先度高）

| # | 内容 | 00_ランチャー/app.py | 33/launcher_gui.py | 81_open_shortcut |
|---|---|---|---|---|
| 1 | タイトルバーのダークテーマ適用関数（`_style_titlebar`/`style_titlebar`） | :89-103 | :231-245 | `theme.py`:27-45 |
| 2 | `sv_ttk`/`pywinstyles` の optional import try/except一式 | :45-55 | :23-33 | `theme.py`:8-18 |
| 3 | フォント定数群（`UI_FONT_FAMILY`/`UI_FONT`/`UI_FONT_BOLD`/`HEADER_FONT`等） | :68-73 | :42-49 | ✗（未使用） |
| 4 | ボタン3段階スタイル（`BTN_PRIMARY/SECONDARY/TERTIARY` + `_BUTTON_SPECS`） | :79-86 | :55-62 | ✗（`Accent.TButton`を直接使用） |
| 5 | メインウィンドウ起動時の「テーマ適用→タイトルバー処理」呼び出し順 | :584-588 | :1165-1176 | `main.py`:50,58 |

- #1・#2・#5 は3ファイルで独立に再実装されている（Windows 11/10分岐、アルファ再描画ハックまで一致）。
- #3・#4 は00と33の2箇所のみの重複（81はボタン3段階スペックを採用していない）。
- `app.py` 側のコメント「フォント定義（ここで一元管理。33_テキスト・CSV前処理サポートのlauncher_gui.pyと揃える）」、`theme.py` 側のdocstring「00_ランチャー、33_テキスト・CSV前処理サポートと同じ任意依存パターン」から、**開発時点で重複を認識しながら手動同期している状態**であることが確認できる。
- `81_open_shortcut/theme.py` は既に関数として自フォルダ内に切り出し済みで、呼び出し側も `theme.apply_dark_theme()` / `theme.style_titlebar(self)` と関数呼び出しの形になっている。共通モジュール化する際のひな形として最も完成度が高い。

### 要注意（共通化ではなく整理対象）

| # | 内容 | 備考 |
|---|---|---|
| 6 | クラス名 `ConfigEditorWindow` が00と33の両方に存在 | 00は汎用config.jsonフォーム化、33はtext_splitter専用フォーム。中身は別物なので共通化するなら統合設計が要るが、同名で紛らわしい点は認識共有しておきたい |
| 7 | 「JSON読み込み→失敗時 `messagebox.showerror`」の定型イディオム | 00・33の随所（config読込、favorites読込等）で反復。厳密には同一コードでないためヘルパー関数化の余地がある程度 |

## 対象外と判断したファイル

`import tkinter` を含む全21ファイルを走査し、`sv_ttk`/`pywinstyles`/タイトルバー処理の有無で絞り込んだ。以下は該当パターンを持たないため対象外。

- `34_Fixed2Excel\src\gui.py`, `mapping_editor_window.py`
- `10_スクレイピング（勤怠・TR)\src\gui\*.py`（`gui.py`, `gui_config_dialog.py`, `gui_add_pattern_dialog.py`, `gui_date_range_dialog.py`）
- `10_スクレイピング（勤怠・TR)\src\gui\webview_launcher.py` — 名前に「ランチャー」とあるが、pywebview UIをsubprocessで起動するだけの4行モジュール。テーマ/スタイル要素はなく別の関心事
- `32_フォルダ構造Excel出力\generate_drive_structure.py`
- `20_セレクタ抽出_Selenium\src\gui.py`
- `33_テキスト・CSV前処理サポート\text_splitter\src\gui.py`（親の `launcher_gui.py` のみが対象）

`run.bat` については全ツール横断で内容を確認済み（差分は起動コマンド1行のみ）のため個別列挙はしない。

## 次のアクション（未着手・検討用メモ）

着手する場合は #1・#2・#5（テーマ適用＋タイトルバー処理）から着手するのが費用対効果が高い。
`81_open_shortcut/src/theme.py` をベースに共通モジュールを切り出し、`00_ランチャー` と `33_テキスト・CSV前処理サポート` からimportする形が候補。

ただし `00_ランチャー` は「ツール側コードに一切手を入れない外付けマニフェスト方式」を思想として掲げているため、
`33_テキスト・CSV前処理サポート` や `81_open_shortcut` が `00_ランチャー` に依存する形は思想と矛盾する。
共通モジュールは第3の場所（例: `90_ひな形` 配下）に置き、両者が対等に参照する形が筋が良さそう。

フォント定数・ボタン3段階スタイル（#3・#4）は00と33の2箇所のみの重複のため、優先度は#1・#2・#5より低い。
