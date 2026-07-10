# 21_セレクタ抽出_Playwright

Webページ上の要素をAlt+クリックで自動キャプチャし、Playwright自動化スクリプト向けのセレクタコード（`getByRole`/`getByLabel`など）を生成・保存するツール「pw-inspector」を格納しています。

> **技術スタック**: Node.js/Express + **Playwrightベース**。現時点でPython直下にPlaywrightを使った現役プロジェクトはありませんが、将来Playwrightで自動化する際の準備として保持しています。Seleniumベースのプロジェクト（`10_スクレイピング（勤怠・TR)`など）向けには代わりに [`20_セレクタ抽出_Selenium`](../20_セレクタ抽出_Selenium/README.md) を使ってください。

## 中身

| フォルダ | 説明 |
| --- | --- |
| `pw-inspector/` | ツール本体（Node.js/Express + Playwright）。詳細は [`pw-inspector/README.md`](./pw-inspector/README.md) を参照 |

## クイックスタート

```bash
cd pw-inspector
npm install
npx playwright install chromium
npm start
# → http://localhost:3737 をブラウザで開く
```

ページ上でAlt+クリックした要素のセレクタが優先度順に生成され、`.js`/`.json`として保存できます。保存したセレクタは他のPlaywrightスクリプトから`require`して使い回せます。
