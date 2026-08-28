# ファイル振り分けツール

指定フォルダ内のファイルを拡張子ごとのサブフォルダに振り分けて整理するツールです。
Tkinter GUI で **対象フォルダ選択 → プレビュー（ドライラン）→ 実行** の流れで使えます。

## 機能

- 対象フォルダ内のファイルを、拡張子（またはグループ名）と同じ名前のフォルダへ移動します。
- 拡張子のないファイルは `no_extension` フォルダへ移動します。
- `config.ini` の `ExtensionGroups` で複数の拡張子を1つのフォルダにまとめられます（例: `images = jpg, png`）。
- `Exclude` で整理対象から外すファイル名・拡張子を指定できます。
- 移動先に同名ファイルがある場合、末尾に連番を付けてリネームします（`foo.txt` → `foo_2.txt`）。
- **プレビュー**：実行前に「どのファイルがどこへ動くか／なぜスキップされるか」を一覧表示します（ファイルは移動しません）。
- **実行ログ**：処理内容を画面にライブ表示し、CLI 実行時は対象フォルダ内の `logs` フォルダにも保存します。

## 使い方（GUI）

1. `run.bat` をダブルクリックして起動します。
2. 「対象フォルダ」を確認・変更します（［参照…］でフォルダ選択）。
3. ［プレビュー］を押して、移動内容を確認します。
4. 問題なければ ［この内容で実行］ を押します（確認ダイアログが出ます）。

拡張子グループや除外リストは ［設定…］ から編集できます。
※ 設定を保存すると `config.ini` は `configparser` で書き直されるため、**既存のコメント行（`;` 始まり）は失われます**。
　`config.ini` は git 追跡対象なので、変更内容は `git status` / コミット履歴に現れます。

## 使い方（CLI・従来互換）

`run_cli.bat` は GUI を開かず、`config.ini` の `TargetDirectory` を対象にプレビューなしで即振り分けます。
実行前に対象パスを必ず確認してください。

## ファイル構成

```
src/
  config_io.py       config.ini の読み書き
  organizer.py       振り分けの計画（build_plan）と実行（execute_plan）
  gui.py             Tkinter GUI 本体
  settings_editor.py 設定編集サブウィンドウ
  theme.py           任意のダークテーマ適用（sv-ttk / pywinstyles、未導入でも動作）
  cli.py             CLI エントリ（run_cli.bat）
  main.py            GUI エントリ（run.bat）
tests/               unittest（python -m unittest discover -v tests / run_tests.bat）
config.ini           設定ファイル
```

## テスト

```
run_tests.bat
```
