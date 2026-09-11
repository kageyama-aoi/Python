# ドキュメント連動ルール（DOC_SYNC）

> 状態: 進行中

コードを整理したのに、それを教える doc（スキル・ガイド・README）が古いまま残ると、
次の開発で古いパターンが再生産される。**「X を変えたら Y も同じコミットで直す」** の対応表。

リファクタや構成変更の**仕上げ**でこの表を上から確認する。
参照ずれの機械チェックは `python scripts/check_doc_refs.py`（`scripts/README.md`）。

---

## 対応表

| 変えたもの（X） | 同じコミットで直すもの（Y） |
|---|---|
| ツールのフォルダ名を変更・移動した | ルート `README.md` のツール一覧表 ／ そのツールの `launcher.json` ／ `~/.claude/skills/` 内でそのパスを名指ししている箇所（`check_doc_refs.py --skills` で確認）／ 自動メモリ（`~/.claude/projects/.../memory/`） |
| `src/utils/logger.py` / `src/config_manager.py` の正実装を変えた | `90_ひな形/templates/` 配下の同名テンプレファイル（`create_project.py` が生成時にコピーする実体） ／ `00_project_standard.md` §5 の索引 ／ スキル `python-review` checklist A-4 |
| `theme.py` の公開 API（`apply_theme` / `style_titlebar`）を変えた | スキル `launcher-gui-design`（`templates/theme.py` と本文）／ `00_project_standard.md` §5 |
| ログの文言規約・色（START/END 等）を変えた | スキル `log-conventions` ／ `34_Fixed2Excel/src/utils/log_tags.py` |
| 人が見る Excel 出力の書式パターンを変えた | スキル `excel-output-conventions`（参照実装の表・コード抜粋） |
| `launcher.json` の形式・`kind` の種類を変えた | `00_ランチャー/readme.md` の仕様表 ／ スキル `launcher-manifest` |
| 標準ディレクトリ構成・設計原則を変えた | `00_project_standard.md` ／ スキル `python-new`・`python-review`（どちらも「正はこの doc」と誘導しているだけなので本文転記は無い前提を維持） |
| あるモジュール／関数を、`docs/` や `html(kaisetu)/` の解説が名指ししている状態でリネーム・分割した | その解説 doc（`docs/CODE_ROADMAP.md` `docs/TECHNOLOGIES.md` `docs/diagrams/*` `html(kaisetu)/*.html` 等）を同じコミットで更新 |
| 再利用してよい共通実装を新たに作った／場所を移した | `00_project_standard.md` §5 の索引に追記 ／ 関連スキルがあればそこにも |
| Python レビュー中に新しい落とし穴を見つけた | スキル `python-review` の `references/checklist.md` に実例付きで追記 |

## スキルはリポジトリ外にある

`~/.claude/skills/` はこのリポジトリの管理外で、複数リポジトリで共有されている。
commit フックからスキル本体は直接検査できないため、`check_doc_refs.py --skills` を
**フォルダ名変更などの後に手動で**回す。GAS/JS 用スキルの参照は対象外
（`Tools\Python` を含む行だけを見る）。

## 運用の順序

新しい仕組み → 掃除（既存のずれを直す）→ コードの集約、の順で進める。
逆順（先に集約）だと、集約した瞬間に doc が再びずれて掃除をやり直すことになる。
