# launcher_gui.py — CSV検証サポート ランチャー GUI

`csv_splitter` / `diff_csv` を1つのウィンドウから起動・監視できる内蔵型ランチャー。
Python 標準ライブラリ（Tkinter）のみで動作する。
`e2e/run/run_gui.py`（テストランナーGUI）の設計を踏襲している。

## 起動方法

```
run.bat をダブルクリック（または 00_ランチャーから起動）
```

## 動作要件

| 項目 | 条件 |
|---|---|
| Python | 3.8 以上（Tkinter 付属、標準配布で OK） |
| sv-ttk | **任意**。`pip install sv-ttk` で Windows 11 スタイルのダークテーマが有効になる。未インストールでも標準 ttk テーマで正常動作する |

## 画面構成

```
┌────────────────────────────────────────────────────────────┐
│ [左ペイン]                  │ [右ペイン]                    │
│  ツール一覧                  │  Command（参照用・読み取り専用）│
│  実行パラメータ（ツール別）    │  Log（色付きリアルタイム表示） │
│  [▶ Run] [■ Stop]           │  出力ファイルパネル            │
│  [入力フォルダ] [出力フォルダ] │   （サイズ・件数・エンコード）  │
└────────────────────────────────────────────────────────────┘
```

### ツール別パラメータ

| ツール | パラメータ |
|---|---|
| **csv_splitter** | 入力ファイル選択（`data/input/` 自動スキャン + 参照ボタン）、設定ボタン（`config/config.json` を GUI 編集）、単体GUI起動ボタン |
| **diff_csv** | 新旧ファイルの存在チェック表示（ファイル名は `src/postcode_diff.py` に定義） |

### 実行まわり

- **Run** — 選択ツールをサブスレッドで実行し、ログをリアルタイムに色付き表示する
- **Stop** — 実行中プロセスを `terminate()` で停止する
- 実行終了後（正常・Stop・エラーとも）、ログを `logs/<tool>_<YYYYMMDD_HHMMSS>.log` に自動保存する
- 実行終了後、そのツールの出力フォルダ（csv_splitter は `data/output/`、diff_csv は `output/`）に
  新しく作成・更新されたファイルを一覧表示する
  （サブディレクトリ1階層下まで検知。csv_splitter の実行ごと出力フォルダ `data/output/<入力名>_<日時>/` に対応。
  ダブルクリックまたは「開く」で既定アプリ起動）

### ログの色分けルール

| 色 | 条件 |
|---|---|
| 青 | `===` で始まる行（ヘッダー） |
| グレー | `---` で始まる行 |
| 緑 | `✓` / `完了` / `passed` / exit code 0 |
| 赤（太字） | `FAIL` / `Traceback` / exit code ≠ 0 |
| ピンク | `Error` / `エラー` |
| オレンジ | `warn` / `警告` |

### ログ・出力ファイルの自動クリーンアップ

起動 0.3 秒後にバックグラウンドで、30 日以上古いものを zip 圧縮してから削除する。

- ログ: `logs/` 内のログ → `logs/archive/<name>.log.zip`
- 出力ファイル: 各ツールの出力フォルダ（`ToolPanelBase.output_subdir` で定義）直下の
  ファイル・実行ごとサブディレクトリ → `<出力フォルダ>/archive/<name>.zip`
  （サブディレクトリはフォルダ単位で 1 つの zip にまとめる。
  ディレクトリの新旧は配下ファイルの最新更新日時で判定し、`archive/` 自体と
  出力拡張子以外のファイル（`desktop.ini` 等）は対象外）

日数は `launcher_gui.py` の `LOG_CLEANUP_DAYS` / `OUTPUT_CLEANUP_DAYS` で変更できる。

## ツールを追加する

`launcher_gui.py` に `ToolPanelBase` のサブクラスを作り、`_PANEL_CLASSES` に登録する。

```python
class MyToolPanel(ToolPanelBase):
    name = "my_tool"          # BASE_DIR/my_tool がツールフォルダになる
    title = "my_tool — 説明"   # 一覧表示名
    description = "..."

    def build_command(self):
        return [sys.executable, "-u", str(self.tool_dir / "run.py")], self.tool_dir
```

## フォルダ構成

```
33_CSV検証サポート/
├── launcher_gui.py    # ランチャー本体
├── run.bat            # ダブルクリック起動用
├── launcher.json      # 00_ランチャー登録マニフェスト
├── logs/              # 実行ログ（gitignore対象、30日で自動アーカイブ）
├── csv_splitter/      # 巨大CSV分割ツール
└── diff_csv/          # 郵便番号差分比較ツール
```
