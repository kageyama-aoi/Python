以下の手順を順番に実行してください。

## 注意事項（最初に確認）
- `config.py` は読まない・内容を出力しない（TOKEN等が含まれるため）
- エラーが出たら止まって報告する（勝手に修正しない）

---

### 0. 既存ファイルをバックアップ

`sql_knowledge.md` が存在する場合、上書き前に `old/` フォルダへ退避する。

```bash
# sql_knowledge.md が存在すれば old/ に日時付きでコピー
if [ -f sql_knowledge.md ]; then
  mkdir -p old
  TIMESTAMP=$(powershell -Command "Get-Date -Format 'yyyyMMdd_HHmm'")
  cp sql_knowledge.md "old/sql_knowledge_${TIMESTAMP}.md"
  echo "バックアップ完了: old/sql_knowledge_${TIMESTAMP}.md"
fi
```

バックアップを確認してからステップ1に進む。

---

### 1. SQL集を取得

```bash
python src/notion_sql_export.py
```

`sql_knowledge.md` が生成されることを確認する。
エラーが出た場合は内容を報告して止まること。

---

### 2. テーブル関係を分析して冒頭に追記

`sql_knowledge.md` の全内容を読み込み、以下の観点で分析する：

- 登場するテーブル名とその役割
- テーブル間のJOINキー（どのカラムで繋がっているか）
- よく使う絞り込み条件（deleted='0' など）
- SET @変数 のパターンと用途

分析結果を以下のMarkdown形式でまとめ、`sql_knowledge.md` の
`## テーブル関係サマリー` セクションを丸ごと差し替える。

#### 出力フォーマット

```markdown
## テーブル関係サマリー
> ⚡ このセクションはClaude Codeが自動生成しました（{実行日時}）

### テーブル一覧
- `テーブル名` : 役割の説明（何を管理するテーブルか）

### テーブル間のJOIN関係
- `テーブルA`.`カラム` = `テーブルB`.`カラム` : 説明

### よく使う絞り込み条件
- `条件式` : 意味・用途

### SET @変数 パターン
- `@変数名` : 何を格納するか・典型的な使われ方
```

---

### 3. 完了報告

以下を報告する：
- 取得したSQL集のページ数
- 検出したテーブル数
- 生成した sql_knowledge.md のサイズ（文字数）
