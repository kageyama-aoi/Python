# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## アプリ概要

研修・講義の宿泊プランを管理する**タイムライン ジェネレーター**。ビルドツール・依存パッケージ一切なし。`timeline-builder.html` をブラウザで直接開くだけで動作する。

## 実行方法

```
# ブラウザで直接開く（ビルド不要）
start timeline-builder.html
```

テスト・Lint の仕組みは存在しない。動作確認はブラウザの開発者ツール（Console）で行う。外部JSファイルを `<script src>` で読み込んでいるため、`file://` 直接オープンで動作する（ローカルサーバー不要）。

## ディレクトリ構成

```
30_宿泊_(前泊延泊)/
├── timeline-builder.html   ← エントリーポイント（HTML骨格と読み込みのみ）
├── assets/
│   ├── css/
│   │   └── styles.css      ← CSS変数ベースのダークテーマ（--bg, --surface, --c0〜--c7 等）
│   └── js/
│       ├── date-utils.js   ← 'M/D'文字列の日付計算（YEAR, addDays, getAllDates, clamp）
│       ├── plan-logic.js   ← 標準プラン算出・computePlanDates()
│       ├── render.js       ← チャート描画（renderDateHeader/LectureRow/PlanRow/Legend + render）
│       ├── sidebar.js      ← プランリストUI・updatePlans()による再描画一元化
│       ├── csv.js          ← CSVエクスポート
│       └── app.js          ← 初期化・フォーム・イベント配線
├── CLAUDE.md
└── 指示文.txt
```

## アーキテクチャ

HTML/CSS/JS分離構成（Issue #12〜#17 のリファクタリングで移行済み）。`timeline-builder.html` は骨格のみで、ロジックは `assets/js/` の6ファイルに責務ごとに分かれる。`<script src>` は依存順（date-utils → plan-logic → render → sidebar → csv → app）に読み込まれ、モジュールシステムは使わずグローバル関数で連携する。

### 状態

```js
let config = {
  timeline: { start: 'M/D', end: 'M/D' },
  lectures: ['M/D', ...]       // 講義日リスト
};

let customPlans = [
  { id, name, early, late, daytrip }  // early/late は標準からの差分（泊数）
];
```

### 日付フォーマット

**`'M/D'` 形式のみ使用**（例: `'2/16'`）。`Date` オブジェクトは内部計算のみに使い、文字列として保持・描画する。年は `const YEAR = new Date().getFullYear()` で動的取得（`addDays`, `getAllDates`, `nightsBetween` が参照）。

### コアロジック（`getStandard` / `render`）

- `getStandard()` → 講義最初の日の前日をチェックイン、講義最終日をチェックアウトとする「標準プラン」を返す
- `render()` → チャートを毎回フルDOM再構築（差分更新なし）。呼ばれるたびに `#chart` を空にして再描画
- `renderSidebar()` → サイドバーのプランリストを同様にフル再構築

### 前泊・延泊ロジック

```
前泊 +N → 標準チェックインより N 日早い（期間が前に伸びる）
前泊 -N → 標準チェックインより N 日遅い（期間が前から縮む）
延泊 +N → 標準チェックアウトより N 日遅い（期間が後ろに伸びる）
延泊 -N → 標準チェックアウトより N 日早い（期間が後ろから縮む）
日帰り  → 宿泊なし、入り日のみダイヤモンドマーカーで表示
```

plan の `startDate` / `endDate` は `render()` 内で `getStandard()` を元に動的に計算される（`customPlans` オブジェクト自体には保存しない）。

### CSV出力

BOM付き UTF-8（`'\uFEFF'` プレフィックス）で Blob を生成し `<a>` タグ経由でダウンロード。Excel での文字化け防止のため。

## 開発上の注意

- **年の取得**: `YEAR` 定数（`new Date().getFullYear()`）を `addDays`・`getAllDates`・`nightsBetween` が参照。年をまたぐ研修（12月〜1月）には未対応。
- **`render()` は副作用あり**: DOM を破壊・再構築するため、呼び出し前に `chart.innerHTML = ''` が実行される。
- **プランの色**: `COLORS` 配列（8色）をインデックスでループ。標準プランは常に `--c0`（index 0）。カスタムプランは `(i+1) % 8`。
- **JSONパース**: `parseSchedule()` と `parsePlans()` はそれぞれ独立したエラーハンドリングを持つ。入力が不正な場合はトーストを表示して `config`/`customPlans` を変更しない。
