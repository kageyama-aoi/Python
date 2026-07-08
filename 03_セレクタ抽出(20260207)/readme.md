# 03_セレクタ抽出(20260207)

Webページ上の要素をAlt+クリックで自動キャプチャし、Playwright自動化スクリプト向けのセレクタコード（`getByRole`/`getByLabel`など）を生成・保存するツール「pw-inspector」を格納しています。

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
