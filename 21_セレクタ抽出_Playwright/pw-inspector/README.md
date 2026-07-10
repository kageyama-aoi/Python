# PW Inspector - Playwright Element Inspector

Alt+クリックでセレクタを自動生成し、スクリプトから require できる JS/JSON として保存するツール。

## セットアップ

```bash
cd pw-inspector
npm install
npx playwright install chromium
npm start
# → http://localhost:3737
```

## ワークフロー

```
1. URL 入力 → 「起動」
2. ページで Alt+クリック で要素キャプチャ
3. GUI でキー名・メモを編集
4. 「保存」ボタンで .js / .json を出力
5. 自動化スクリプトから require
```

## スクリプトでの使い方

```javascript
const { getLocator, loginSelectors } = require('./selectors/login-selectors.js')

// getByRole/getByLabel などを自動判定して呼び分け
await getLocator(page, 'emailInput').fill('test@example.com')
await getLocator(page, 'submitButton').click()

// 直接参照も可
console.log(loginSelectors.emailInput.code)
// → "page.getByLabel('メールアドレス')"
```

## セレクタ優先度

1. getByRole ★★★★★  
2. getByLabel ★★★★☆  
3. getByPlaceholder ★★★★☆  
4. getByText ★★★☆☆  
5. data-testid ★★★★★  
6. #id ★★☆☆☆  
7. aria-label ★★★☆☆  
8. name属性 ★★★☆☆  
9. .class ★★☆☆☆  
10. XPath ★☆☆☆☆ (最終手段)

## IT初心者向け

「ウェブページの部品を自動で名前付けしてくれるツール」

ボタンやテキストボックスなど、ページ上の部品をクリックするだけで「この部品をプログラムで操作するにはこう書けばいい」という答えを自動で探してくれます。今まで手作業で調べていた作業が数秒で終わります。

---

## 技術者向け

「Playwright 自動化スクリプト向けのセレクタ収集・エクスポートツール」

対象ページ上で Alt+クリックするだけで、`getByRole` / `getByLabel` などを優先した耐変化性の高いセレクタ候補を優先度順に生成し、重複チェック（ページ内ヒット件数）まで自動で行います。収集した要素はキー名・メモを付けて `require` 可能な JS ファイルとして出力でき、`getLocator(page, 'key')` ヘルパー経由でスクリプトから直接呼び出せます。
