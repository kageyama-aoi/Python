# show_tree

指定フォルダのディレクトリ構成をツリー表示するツール。
構成を Claude などに貼り付けて共有する用途を想定。

## 使い方（GUI）

`run.bat` をダブルクリックすると GUI（`show_tree_gui.py`）が起動する。
フォルダを選び、深さ・隠しファイル表示・拡張子フィルタ・追加除外を指定して
「ツリー生成」。「コピー」でクリップボードへ、「保存...」でテキスト／Markdown 保存。
テーマ・フォントは親ツールの `../src/theme.py` を共用する（Tkinter 標準ライブラリのみで動作）。

## 使い方（CLI）

```bash
python show_tree.py [ルートパス] [オプション]
```

| オプション | 説明 |
| --- | --- |
| `--depth N` | 表示する階層の深さ（デフォルト: 4） |
| `--all` | 隠しファイル（`.`で始まるもの）も表示 |
| `--ext .py .md` | 指定拡張子のファイルだけ表示（複数指定可） |
| `--ignore node_modules .git` | 除外フォルダ名（複数指定可） |

例:

```bash
python show_tree.py C:/Users/me/projects --depth 3 --ignore node_modules .git __pycache__
```
