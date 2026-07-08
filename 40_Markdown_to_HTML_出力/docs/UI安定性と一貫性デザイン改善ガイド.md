# UI安定性と一貫性デザイン改善ガイド

## 背景

画面遷移時に「横幅・余白・見た目の微妙なズレ」があり、ちらつき感やストレスが発生している。

現行コードでは、主要画面ごとにコンテナ幅が不一致になっている。

- メタ編集画面: `--max: 1280px`（`app.py`）
- 取込画面: `max-width: 960px`（`app.py`）
- 一覧画面: `--max: 1200px`（`build.py` / `html/index.html`）

## 問題の本質

1. 見た目の一貫性不足  
画面ごとに幅・余白・背景・コンポーネント密度が異なるため、遷移時に「別システム感」が出る。

2. レイアウト安定性不足  
表示後の要素追加やサイズ揺れで、視線の再探索コストが上がる（体感ちらつき）。

## 改善原則（調査ベース）

1. レイアウトシフト（CLS）を抑える  
- 目安: CLS 0.1 以下  
- 遅延表示される領域は先に高さを確保  
- 表示後に押し下げるUI更新を避ける

2. Design Tokensで共通骨格を持つ  
- `--container-max`, `--space-*`, `--radius-*`, `--font-size-*` を共通化  
- 画面単位の「場当たりCSS」を減らし、基準値を1か所管理

3. ブレークポイントを統一  
- `sm / md / lg` の3段階で、全画面同じルールを適用  
- 同じ幅で同じ崩れ方にする

4. モーションを制御する  
- 不要アニメーションを削減  
- 使う場合は `transform` / `opacity` を中心に  
- `prefers-reduced-motion` に対応

5. 導線パターンを固定する  
- ヘッダー、ナビ、フォーム、ボタンの配置を全画面で共通化  
- 「毎回探す」負荷をなくす

## このリポジトリ向け実装方針

1. 共通CSS導入  
- `html/shared_ui.css`（または `html/style.css` 拡張）にトークンと共通レイアウトを集約  
- `app.py` のインラインCSSを段階的に移行

2. コンテナ幅を単一化  
- 例: `--container-max: 1120px`  
- `/`（メタ編集）, `/import`（取込）, `/kb`（一覧）を同値へ統一

3. 共通ヘッダー化  
- ナビリンク群を同じDOM構造・同じ高さに統一  
- 見出し・操作エリアの間隔も統一

4. メッセージ領域の高さ確保  
- 保存結果・エラー表示の領域に `min-height` を設ける  
- 表示有無でレイアウトが上下しないようにする

5. フォーム部品の寸法統一  
- `input/select/button/textarea` の高さ・フォントサイズ・余白を共通化  
- 「画面ごとに違う密度感」を解消

## 実装ステップ（推奨）

1. `shared_ui.css` を新設してトークン定義  
2. `/` → `/import` → `/kb` の順に共通スタイルへ移行  
3. `build.py` 側の生成HTMLにも同じクラス体系を適用  
4. 3画面の横幅・余白・ヘッダー位置をスクリーン比較  
5. 仕上げにアクセシビリティと性能観点を確認

## 検証チェックリスト

- 画面幅 `360 / 768 / 1280` で見た目の整合が取れている
- ブラウザズーム `200% / 400%` で破綻しない（Reflow）
- 保存前後で操作位置が大きくズレない
- LighthouseでCLS悪化がない
- `prefers-reduced-motion` で過剰演出が抑制される

## 参考リンク

- CLS最適化（web.dev）  
  https://web.dev/articles/optimize-cls
- Motionとアクセシビリティ（web.dev）  
  https://web.dev/learn/accessibility/motion/
- USWDS Design Tokens  
  https://designsystem.digital.gov/design-tokens/
- USWDS Spacing Units  
  https://designsystem.digital.gov/design-tokens/spacing-units/
- Material Responsive UI  
  https://m1.material.io/layout/responsive-ui.html
- WCAG 2.2 Reflow  
  https://www.w3.org/WAI/WCAG22/Understanding/reflow
- GOV.UK Design System Patterns  
  https://design-system.service.gov.uk/patterns/
- GOV.UK Design System Styles  
  https://design-system.service.gov.uk/styles/

## 補足

本ガイドは「見た目を派手にする」ためではなく、利用者の認知負荷を下げるための実務基準として作成した。  
優先順位は「一貫性 > 安定性 > 装飾性」とする。
