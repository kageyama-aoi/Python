# SPEC - 技術仕様・要件定義

## 機能要件

### リファクタリング：src/ ディレクトリ構造の再編成

#### 目的
- メニュー（GUI）と画面自動操作（スクレイピング）を明確に分離する
- 設定系・ユーティリティ系もサブディレクトリで管理し、責務を明確にする

#### 変更前後の構造

**変更前**
```
src/
├── main.py
├── config.py
├── config_manager.py
├── browser_utils.py
├── file_utils.py
├── gui.py
├── gui_config_dialog.py
├── handler_factory.py
└── handlers/
    ├── __init__.py
    ├── base_handler.py
    ├── crowdlog_handler.py
    ├── task_report_handler.py
    └── shimamura_search_handler.py
```

**変更後**
```
src/
├── main.py
├── config/
│   ├── __init__.py
│   ├── config.py
│   └── config_manager.py
├── gui/
│   ├── __init__.py
│   ├── gui.py
│   └── gui_config_dialog.py
├── scraping/
│   ├── __init__.py
│   ├── browser_utils.py
│   ├── handler_factory.py
│   └── handlers/
│       ├── __init__.py
│       ├── base_handler.py
│       ├── crowdlog_handler.py
│       ├── task_report_handler.py
│       └── shimamura_search_handler.py
└── utils/
    ├── __init__.py
    └── file_utils.py
```

#### 対応範囲
- ファイルの移動（物理的な配置変更）
- 移動に伴う全 import パスの修正
- 各サブディレクトリへの `__init__.py` 新設
- ロジック変更は行わない（純粋な構造整理のみ）

## 非機能要件
- 既存の動作を一切変えないこと（ロジック・設定ファイルパス等に影響を与えない）
- 移動前のファイルは削除する（残骸を残さない）

## 技術構成
- Python パッケージ構成（`__init__.py` によるパッケージ化）
- import は相対パスではなく絶対パス（`from src.config.config import ...`）で統一
