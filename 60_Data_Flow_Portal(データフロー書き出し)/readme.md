# 60_Data Flow Portal（データフロー書き出し）

CSVで管理している「イベント単位のデータフロー（DB更新の前後比較）」を、静的HTMLの横表として可視化するツールです。

## 中身

| フォルダ/ファイル | 説明 |
| --- | --- |
| `P01/` | ツール本体。詳しい仕様・使い方は [`P01/README.md`](./P01/README.md) を参照 |
| `01_prompt.md` | ツールの初期実装を依頼した際の設計プロンプト（役割・要件定義） |
| `02_prompt.md` | 画面のUI/UX改善を依頼した際のプロンプト |
| `scripts/create_project.py` | プロジェクト標準構成（`99_ひな形`）の生成スクリプトのコピー |
| `.claude/` | Claude Code のローカル設定 |

## クイックスタート

実際の実行手順・CSV仕様・設定方法は `P01` 側のREADMEにまとまっています。

```bash
cd P01
pip install -r requirements.txt
python src/main.py --config config/main.yaml --open
```
