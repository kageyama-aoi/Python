# scripts/ — リポジトリ横断の補助スクリプト

個々のツールではなく、リポジトリ全体を対象にするスクリプトを置く。

| ファイル | 用途 |
|---|---|
| `check_doc_refs.py` | ドキュメント/スキルの参照ドリフト検知（下記） |
| `check_doc_refs.ignore` | 「実在しないが意図的」な参照の除外リスト |
| `run_all_tests.py` | 全ツールの pytest をツールごとに独立プロセスで実行・集計（下記） |
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
- `pre-push`: `check_doc_refs.py`（警告）＋ `pytest scripts/`（失敗時のみ push 中止）
  ＋ `run_all_tests.py --warn-only`（全ツール pytest・警告のみ）。

**方針**: 当面ずっと警告モードで運用する。誤検知ゼロを十分な期間確認できてから、
`--check`（exit 1）への昇格を別途検討する。いきなり fail にすると誤検知で作業が止まる。

---

## run_all_tests.py — 全ツールの pytest 集約

各ツールは独立しており（`src/` を `sys.path` に足す各ツールの `conftest.py`、`config` 等の
同名モジュール、`test_main.py` の重複、`11_` を外すと数字始まりで壊れるフォルダ名）、
リポジトリルートで `python -m pytest` を一発実行すると collection 段階で衝突する。
このスクリプトは各ツールの流儀（`cd <tool> && python -m pytest tests/`）を
**ツールごとに独立したサブプロセス**で回し、結果だけを集約する。

```bash
python scripts/run_all_tests.py             # 全ツール実行。1つでも失敗で exit 1
python scripts/run_all_tests.py --warn-only # 失敗があっても exit 0（フック用）
python scripts/run_all_tests.py --list      # 対象ユニットを列挙
python scripts/run_all_tests.py -k 34       # tests/ の親フォルダ名で絞り込み
```

- 対象は「`test_*.py` を含む `tests/` を持つフォルダ」を自動探索（`_archive` 等は除外）。
- pytest 終了コード 5（テスト0件）は skip 扱い。
- GUI（tkinter）テストは**ローカルの Tcl/Tk 環境が壊れていると落ちる**。これは
  コードのバグではないため pre-push では `--warn-only`。詳細と昇格条件は #179。
