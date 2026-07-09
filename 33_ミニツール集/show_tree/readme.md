# show_tree

指定フォルダのディレクトリ構成をツリー表示するスクリプト。
構成を Claude などに貼り付けて共有する用途を想定。

## 使い方

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
