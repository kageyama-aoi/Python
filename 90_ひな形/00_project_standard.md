# Pythonプロジェクト標準構成定義 (Standard Project Structure)

このドキュメントでは、本プロジェクトおよび今後作成されるPythonプロジェクトの標準的なディレクトリ構成とその設計思想について定義します。

## 1. ディレクトリ構成図

```text
Project_Root/
├── .gitignore               # バージョン管理除外設定
├── .env                     # 環境変数 (APIキー、パスワード等) ※Git管理外
├── README.md                # プロジェクト概要・セットアップ手順
├── requirements.txt         # 依存ライブラリ一覧
├── src/                     # ソースコード (Source)
│   ├── __init__.py
│   ├── main.py              # エントリーポイント
│   ├── gui.py               # UI層 (GUI/CUI)
│   ├── config_manager.py    # 設定管理ロジック
│   ├── utils/               # 汎用ユーティリティ
│   └── handlers/            # ビジネスロジック (機能ごとの具体的処理)
├── config/                  # 設定ファイル (Configuration)
│   ├── main.yaml            # 全体設定
│   └── modes/               # カテゴリ別詳細設定
├── docs/                    # ドキュメント (Documentation)
├── data/                    # データ領域 (Data) ※実データが入るため丸ごとGit管理外
│   ├── input/               # 入力データ
│   ├── output/              # 出力データ・ダウンロードファイル
│   ├── temp/                # 一時ファイル
│   └── logs/                # 実行ログ
└── scripts/                 # 補助スクリプト (構築・運用)
```

## 2. 各ディレクトリの役割

| ディレクトリ | 役割 |
| :--- | :--- |
| `src/handlers/` | **このツールの心臓部。** 具体的な自動化処理や計算ロジックをここに集約する。 |
| `src/utils/` | ログ出力やブラウザ操作など、他のプロジェクトでも再利用可能な汎用関数を置く。 |
| `config/` | プログラムを書き換えずに挙動を変更するための設定値を置く。YAML形式を推奨。 |
| `docs/` | 設計計画、仕様書、ユーザーマニュアルなどを管理する。 |
| `data/` | 実行時に生成されるファイル・読み込むCSV・実行ログなどを整理して格納する。**実データが入るため丸ごと gitignore 対象。** |
| `scripts/` | 開発環境の構築や、本番実行用のバッチファイルなどを置く。 |

## 3. 設計の4原則

保守性と拡張性を維持するために、以下の原則を遵守します。

1.  **ハードコードの禁止 (External Config)**
    *   URL、ファイルパス、セレクタ、定型文などはコード内に直接書かず、必ず `config/` 内のYAMLファイルに定義する。
2.  **ロジックと設定の完全分離 (Separation of Logic & Config)**
    *   `src/` には「どう動くか」を書き、`config/` には「何に対して動くか」を書く。
3.  **ドキュメント駆動開発 (Documentation First)**
    *   複雑な変更を行う際は、まず `docs/` に計画（Plan）を記述し、思考を整理してから実装に入る。
    *   計画・提案・レビュー系の doc（`docs/*plan*.md` `*_proposal*.md` `*review*.md` 等）は、
        先頭に状態行を置く：`> 状態: 進行中` / `> 状態: 完了(YYYY-MM)` / `> 状態: 廃止`。
        古い計画を「今の話」と誤読させない。完了・廃止の doc は凍結された記録として扱う。
4.  **実データはコミット禁止 (No Real Data in Repo)**
    *   実行データ（入力・出力・ログ）は `data/` に集約し、丸ごと gitignore する。公開リポジトリのため、
        実名・業務データがリポジトリに載る経路を構造的に断つ。
    *   設定ファイルに実案件名が入り得る場合は、そのファイルを gitignore し、
        形式サンプルを `*.example.*`（例: `presets.example.json`）としてコミットする。

## 4. 新規プロジェクトの作成

本プロジェクトに含まれる `scripts/create_project.py` を使用することで、この標準構成を自動的に生成できます。

```bash
python scripts/create_project.py <New_Project_Name>
```

## 5. 共通実装の索引（自作する前にここを見る）

各ツールは独立しているため共通コードは「共有」ではなく**コピー**する。以下は
「コピー元にしてよい既知の正実装」。同じものを自前で書き直さない（実装の重複が
リポジトリ全体の保守性を下げる。ロガーは過去に7か所重複した）。

| 用途 | 正実装 | 公開シンボル |
| :--- | :--- | :--- |
| ロギング | `90_ひな形/scripts/create_project.py` が生成する `src/utils/logger.py` | `setup_logger()` |
| 設定読み込み | 同上が生成する `src/config_manager.py` | `ConfigManager` |
| Tkinter テーマ/フォント/タイトルバー | `00_ランチャー/theme.py`（`32_` `34_` `81_` に同型あり） | `apply_theme(root)` / `style_titlebar(window)` |
| ログのライフサイクル色分け（START/END） | `34_Fixed2Excel/src/utils/log_tags.py` | `log_start()` / `log_end()` / `TAG_START` |
| GUI ログハンドラ（queue 経由） | `34_Fixed2Excel/src/gui.py` | `QueueLogHandler` |
| 人が見る Excel 出力の書式 | `34_Fixed2Excel/src/utils/excel_style.py` | （スキル `excel-output-conventions` 参照） |
| 固定長フィールドの列名一意化 | `34_Fixed2Excel/src/utils/fixed_format.py` | `build_field_columns()` |
| ランチャー登録（`launcher.json` / `run.bat`） | スキル `launcher-manifest` | — |

- テーマ/ログ色/Excel 書式など、判断基準はグローバルスキル（`launcher-gui-design`
  `log-conventions` `excel-output-conventions`）側にある。この表は「現物の場所」の索引。
- この表を更新したときは §6 の連動ルールに従い、関連スキル・README も同じコミットで直す。

## 6. ドキュメント連動ルール

共通パターン・構成・命名を変えたら、それを教える doc も同じコミットで直す。
対応表は [`DOC_SYNC.md`](./DOC_SYNC.md)。参照ずれは
`python scripts/check_doc_refs.py` で検知できる（`scripts/README.md`）。

---
**作成日:** 2025年12月26日
**作成経緯:** 勤怠自動化ツールのリファクタリング過程で、拡張性と保守性を両立した「最強のPythonプロジェクト構成」として定義。
**2026-09 追記:** §3 に計画 doc の状態行、§5 共通実装の索引、§6 連動ルールを追加（ドリフト防止 #177）。
