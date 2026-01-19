# Config Refactoring Plan

## 1. 目的
`config.yaml` の肥大化を防ぎ、モード（勤怠、TR）やプロジェクトごとの設定を独立して管理できるようにする。
`src/handlers/` のクラス構造と設定ファイルの構造を一致させることで、新機能追加時の作業範囲を明確にする。

## 2. 現状の課題
- `config.yaml` 1ファイルに全ての定義（URL, セレクタ, 各プロジェクトの定型文など）が混在している。
- 「Yamahaの設定を変えたいだけなのに、全体のConfigを開く」というリスクがある。
- Handlerは分割されたが、設定は密結合のまま。

## 3. 改善案: ファイル分割と階層化

### ディレクトリ構造案
```text
config/
├── main.yaml          # アプリ全体の共通設定（URL, ログイン情報, ログ設定）
└── modes/             # モードごとの設定
    ├── crowdlog.yaml  # 勤怠関連の設定 (selectors, fields...)
    └── task_report/   # TR関連
        ├── common.yaml    # TR共通設定 (fields mappings...)
        ├── shimamura.yaml # Shimamuraプロジェクトの定型文
        ├── yamaha.yaml
        ├── tframe.yaml
        └── ...
```

### Configファイルの構成イメージ

**config/main.yaml**
```yaml
app:
  url: "..."
  download_dir: "..."
menus:
  # モード定義など、起動に必要な情報はここに残す
  modes: ...
```

**config/modes/crowdlog.yaml**
```yaml
selectors:
  login_email: "email"
  # CrowdLog固有のセレクタのみ記述
fields:
  # CrowdLog固有のフィールド設定
```

**config/modes/task_report/shimamura.yaml**
```yaml
# キー名でマッチングさせる (例: 's', 'up' など)
s:
  Project: "SMMs001PH"
  Title: "(UATxxx)..."
up:
  Category: "[KANKYOUMEI]環境_更新依頼"
  # ...
```

## 4. 実装ステップ

### Step 1: `config.py` の改修 (Loaderの強化)
現在の `load_config()` 関数を拡張し、`main.yaml` を読み込んだ後、`config/modes/` 配下のYAMLファイルを再帰的に読み込んで、一つの巨大な辞書（`CONF`）にマージするロジックを実装する。

### Step 2: ファイルの分割作業
1.  現在の `config.yaml` を `main.yaml` にリネーム。
2.  `school_specific_defaults` や `fields` などの部分を切り出して、新しいファイルに移設する。

## 5. メリット
- **可読性向上**: 1ファイルあたりの行数が減り、目的の設定が見つけやすくなる。
- **拡張性**: 新しいプロジェクト（例: `hoge_project`）が増えたら、`modes/task_report/hoge.yaml` を置くだけで済むようにできる。
- **安全性**: 関係ない設定を誤って書き換えるリスクが減る。
