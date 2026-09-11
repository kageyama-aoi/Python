# scripts/ — リポジトリ横断の補助スクリプト

個々のツールではなく、リポジトリ全体を対象にするスクリプトを置く。

| ファイル | 用途 |
|---|---|
| `check_doc_refs.py` | ドキュメント/スキルの参照ドリフト検知（下記） |
| `check_doc_refs.ignore` | 「実在しないが意図的」な参照の除外リスト |
| `tests/` | 上記スクリプトの特性テスト（`python -m pytest scripts/`） |

---

## check_doc_refs.py — 参照ドリフト検知

「コードを整理したのに、それを説明する README/ガイド/スキルが古い参照を抱えたまま
残る」ドリフトを、機械的に気付ける状態にするための**警告ツール**。

### 使い方

```bash
python scripts/check_doc_refs.py            # 警告のみ表示（exit 0）
python scripts/check_doc_refs.py --check    # 検出があれば exit 1（CI/フック昇格用）
python scripts/check_doc_refs.py --docs     # **/docs/** も対象に含める（広めの掃除用）
python scripts/check_doc_refs.py --skills   # ~/.claude/skills/ の Tools\Python 参照も検査（手動専用）
python scripts/check_doc_refs.py --symbols  # 識別子参照(②)も検査（Python前提・弱い警告）
```

### 何を見るか

- **既定の対象**: 「いま何がどうなっているか」を説明する doc
  （リポジトリ直下と各ツール直下の `README.md` / `readme.md`、すべての
  `AGENTS.md` / `CLAUDE.md`、`90_ひな形/` 配下の `*.md`）。
- `--docs` を付けると `**/docs/**` も対象。ただし先頭に
  `> 状態: 完了(...)` / `廃止` と書かれた plan・履歴 doc は凍結記録として自動スキップ。
- **① パス参照**: バッククォート内・Markdownリンク先の `src/...` `NN_フォルダ/...`
  `*.py` 等が、doc のツールフォルダ基準 → リポジトリルート基準のどちらでも
  解決できなければ報告。末尾 `:123` の行番号は無視。
- **② 識別子参照**（`--symbols`）: `name(` `Class.method(` `def name` `class Name` が
  リポジトリ内の `.py` に定義されているか。JS/GAS は対象外なので弱い警告扱い。

### 誤検知が出たら

意図的に「実在しない参照」を書いている場合は `scripts/check_doc_refs.ignore` に
1行1件で追記する（`#` 以降はコメント。glob 可）。**なぜ実在しないのが正しいのかを
コメントで残すこと。**

### git フック（`.githooks/`）

```bash
git config core.hooksPath .githooks   # 各クローンで1回
```

- `pre-commit`: `check_doc_refs.py` を警告モードで実行（**commit はブロックしない**）。
- `pre-push`: 同上（警告）＋ `pytest scripts/`（このスクリプト自体のテスト。失敗時のみ push 中止）。

**方針**: 当面ずっと警告モードで運用する。誤検知ゼロを十分な期間確認できてから、
`--check`（exit 1）への昇格を別途検討する。いきなり fail にすると誤検知で作業が止まる。

> 補足: `.git/hooks/_pre-push`（リポジトリ全体 pytest）は、ツール横断の収集エラーで
> 現状クリーンに通らないため無効のまま。リポジトリ全体 pytest の是正は別Issue。
