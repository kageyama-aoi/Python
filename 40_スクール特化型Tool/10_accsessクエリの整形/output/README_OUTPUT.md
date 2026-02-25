# output 整理ガイド

## まず見る場所
- `output/00_latest/`  
  現時点の採用版を集約したフォルダです。まずここだけ見ればOKです。

## フォルダ構成
- `output/00_latest/`  
  最終採用版（参照起点）
- `output/10_core/`  
  主要テーブルに絞ったERと差分
- `output/20_full/`  
  全体版ERと差分
- `output/30_docs/`  
  推察メモ・コンテキスト定義などの補助資料
- `output/90_work/`  
  変換パイプラインの中間成果物（CSV/SQL）
- `output/archive/`  
  退避ファイル
- `output/split_sql/`  
  SQL分割結果

## 主要ファイル
- `output/00_latest/er_core_with_samples.mmd`  
  主要テーブルER（代表列付き）
- `output/00_latest/diff_core_variants.md`  
  主要テーブル版の受講生/講師/一般研修の差分
- `output/00_latest/diff_full_variants.md`  
  全体版の受講生/講師/一般研修の差分
- `output/00_latest/コンテキスト定義.md`  
  運用前提ルール（初版）
- `output/00_latest/core_table_inference.md`  
  coreテーブルの役割推察

## 運用ルール（推奨）
- 新しい成果物を採用したら、必ず `output/00_latest/` へコピーして更新する
- 試作ファイルは `output/10_core` または `output/20_full` に置く
- 変換途中の素材は `output/90_work` に集約する
