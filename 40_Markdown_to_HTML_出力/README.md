# Markdown to HTML ビルドツール

このツールは、生成AIで増えやすい Markdown ナレッジと図版（画像）を、閲覧しやすい1つの知識ベースとして再編するためのものです。  
分散した `.md` ファイルを `html/index.html` 起点で一覧・検索しやすくし、運用時の「見つけにくい」「追いにくい」を減らすことを目的としています。

`md/` 配下の Markdown を `html/` に変換し、一覧ページ `html/index.html` を生成するツールです。

## 最初にこれ（迷ったら）

`start_here.bat` を実行してください。番号で選べます。

1. ビルドする（`build.py`）
2. ポータルを起動する（`app.py`）
3. ツールキットを別ディレクトリへ配布する
9. 終了

起動しない・画面が開かないなど動作がおかしいときは、`health_check.bat` を実行してください。
Python・依存モジュール・ディレクトリ構成・主要ルート疎通を1コマンドで診断します（詳細は「自己診断」参照）。

## 構成

- `build.py`: Markdown -> HTML 変換本体
- `start_here.bat` / `scripts/start_here.ps1`: 番号メニュー付きの実行入口
- `deploy_toolkit.bat` / `scripts/deploy_toolkit.ps1`: 本体ツールを別ディレクトリへコピー配布
- `health_check.bat` / `scripts/health_check.ps1`: 環境の自己診断（Python・依存・ディレクトリ・ルート疎通）
- `templates/`: 画面・生成HTMLのテンプレート（Jinja2）。`meta_editor.html` / `import.html` は `app.py` の画面、`kb_index.html` / `kb_article.html` は `build.py` の生成物
- `md/`: 入力 Markdown（`*.md`）。サンプル以外はgit管理外（誤コミット防止）
- `html/`: 出力先（各HTML、`index.html`、`style.css`）。生成HTMLもサンプル以外はgit管理外
- `tests/`: スモークテスト（`python -m pytest tests` で主要ルートの200確認）
- `scripts/`: 実行ラッパー・補助スクリプト群（`*.ps1`）
- `scripts/run_build.ps1` / `run_build.bat`: ビルド実行ラッパー
- `scripts/run_portal.ps1` / `run_portal.bat`: ローカル運用ポータル起動（`app.py` を起動しブラウザで開く）
- `app.py`: Front Matter（`category` / `tags`）編集用のローカルWebツール（候補選択 + 自由入力）
- `support_tool/`: Markdown作成補助ツール（ブラウザで使う単体HTML）
- `docs/`: 正式ドキュメント（恒久運用）
- `notes/`: 途中経過・運用メモ（`issue/`, `operations/`, `archive/`）
- `PROMPT.md`: 文章を装飾前提Markdownに整えるためのテンプレート
- `docs/COMMIT_MESSAGE_INSTRUCTIONS.md`: コミットメッセージ提案時の指示文
- `scripts/commit_suggest.ps1`: ステージ差分をもとに `codex` へ提案依頼を渡す補助スクリプト（任意）
- `scripts/toolkit_manifest.json`: 配布対象ファイル一覧（本命データを除外）

## 他案件への展開（本命MDを含めない）

`md/` の本命データをこの共通基盤に置かず、案件ごとにツールだけ展開したい場合は以下を使ってください。

```bat
deploy_toolkit.bat "..\案件A\kb_toolkit"
```

または:

```powershell
.\scripts\deploy_toolkit.ps1 -TargetDir "..\案件A\kb_toolkit"
```

オプション:
- `-IncludeDocs`: `docs/` のテンプレート類もコピー
- `-IncludeSupportTool`: `support_tool/` の補助HTMLもコピー
- `-DryRun`: 実コピーせず予定だけ表示
- `-Force`: 既存ファイルも上書き

この配布スクリプトは `scripts/toolkit_manifest.json` に書かれたファイルだけをコピーするため、`md/*.md` 本命ファイルや `notes/` は配布対象に入りません。
`md/` `html/` `picture/` の空ディレクトリは `.gitkeep` ごと配置されるため、初回起動時のディレクトリ欠落は起きません。

配布後は、配布先で `health_check.bat` を実行して環境（Python・依存モジュール）を確認してから `start_here.bat` を使ってください。

## 基本の使い方（ビルド）

1. `md/` に Markdown（`*.md`）を配置
2. 以下のいずれかで実行

```powershell
python build.py
```

```powershell
.\scripts\run_build.ps1
```

```bat
run_build.bat
```

`run_build.bat` は成功時に `html/index.html` を自動で開きます。

## 出力

- `html/` に各 Markdown の HTML を生成
- `html/index.html` に一覧を生成
- 画像タグ（`<img>`）は `width` 未指定時のみ `width="1000"` を自動付与
- 一覧はカテゴリ単位で表示し、`未分類` は常に最後に配置
- 一覧はカテゴリ3件ずつページ切り替え（`前へ` / `次へ`）

## サポートツール

ビルド本体とは別に、補助的に使えるツールがあります。

1. メタ情報編集ツール（`app.py`）
```powershell
python app.py
```
- `http://127.0.0.1:5000/` で `md/*.md` の `category` / `tags` を一括編集
  - ポートは環境変数 `PORT` で変更可能（未指定時は `5000`）
- 同画面上のリンクから以下へ遷移可能
  - `http://127.0.0.1:5000/kb/`（`html/index.html` の閲覧。未ビルド時は案内ページを表示）
  - `http://127.0.0.1:5000/import`（プレーンテキスト取込）
- 更新系API（保存・一括適用）の実行結果は、起動したコンソールに運用ログとして出力される（件数・失敗ファイルなど）
- `category` は既存値から候補選択でき、自由入力も可能
- `tags` はチップ形式で編集（クリック削除）
- `tags` は既存タグ候補のプルダウン追加 + 自由入力追加（Enter対応）
- 未設定精査用フィルタ
  - `category未設定のみ`
  - `tags未設定のみ`
  - `どちらか未設定`
- 一括編集モード
  - 表示中を全選択
  - 複数ファイルへカテゴリ一括適用
  - タグの `既存へ追加` / `置換` を選択して一括適用
- 保存後は静的HTMLへ反映するため、`python build.py` を再実行

2. プレーンテキスト取込（`/import`）
- タイトル・カテゴリ・タグ・本文を入力して `md/*.md` を作成
- `保存` / `保存してビルド` を選択可能
- ファイル名は `YYYYMMDD_タイトル.md` 形式で自動採番

3. ポータル起動（おすすめ）
```powershell
.\scripts\run_portal.ps1
```
または
```bat
run_portal.bat
```
- `app.py` を起動し、`http://127.0.0.1:5000/` を自動で開く
- `5000` が使用中の場合は `5001`〜`5010` の空きポートを自動選択して開く（実際のURLは起動時のコンソール表示を確認）

4. Markdown保存補助（`support_tool/`）
- `support_tool/md_saver_min.html`
- `support_tool/md_saver_min_v2.html`
- ブラウザで開いて入力したMarkdownを `YYYYMMDD_名前.md` 形式で保存可能

5. Markdownリンク/画像記法補助（`scripts/md_helper.ps1`）
```powershell
.\scripts\md_helper.ps1 -Mode link -TargetPath ".\picture\sample.png" -FromPath ".\md\guide.md"
```
- 相対パスを自動計算して Markdown 記法を生成
- `-Mode image` で画像記法も生成可能
- `-Copy` で生成結果をクリップボードへコピー

`scripts/md_helper.ps1` の実行例:

```powershell
# リンク記法を生成
.\scripts\md_helper.ps1 -Mode link -TargetPath ".\README.md"

# 画像記法を生成（md/guide.md から見た相対パスで計算）
.\scripts\md_helper.ps1 -Mode image -TargetPath ".\picture\dummy.png" -FromPath ".\md\guide.md"

# 表示名を指定して生成
.\scripts\md_helper.ps1 -Mode link -TargetPath ".\docs\template.md" -Label "テンプレート"

# 生成結果をクリップボードへコピー
.\scripts\md_helper.ps1 -Mode link -TargetPath ".\README.md" -Copy
```

主な引数:
- `-Mode`: `link` または `image`
- `-TargetPath`: リンク先/画像ファイルのパス
- `-FromPath`: 相対パス計算の基準（省略時はカレントディレクトリ）
- `-Label`: リンク表示名/画像alt（省略時はファイル名）
- `-Copy`: 生成文字列をクリップボードへコピー

6. コミットメッセージ提案補助（`scripts/commit_suggest.ps1`）
```powershell
.\scripts\commit_suggest.ps1
```
- ステージ済み差分（`git diff --staged`）を取得し、`codex exec -` に渡す補助スクリプト
- 実行には `codex` コマンドが必要
- プロンプトは `scripts/commit_prompt.md` -> `commit_prompt.md` -> `docs/COMMIT_MESSAGE_INSTRUCTIONS.md` の順で自動検出

## 自己診断（health_check）

環境トラブル（起動しない・モジュール不足・ディレクトリ欠落）の切り分けは、以下の1コマンドで行えます。

```bat
health_check.bat
```

または:

```powershell
.\scripts\health_check.ps1
```

診断項目:
- Python が PATH にあるか
- `markdown` / `flask` が import できるか
- `md/` `html/` `picture/` ディレクトリが存在するか
- `app.py` の主要ルート（`/`, `/import`, `/kb/`）が応答するか（サーバー起動不要のインプロセス検査）

結果は `[OK]` / `[WARN]` / `[NG]` で表示され、`[NG]` には対処方法（`->` 行）が併記されます。

## テスト

主要ルートの破壊を検知するスモークテストがあります。改修後は以下で確認してください。

```powershell
python -m pytest tests
```

## 依存関係

- Python
- `markdown`
- `pymdown-extensions`（タスクリスト `- [ ]` のHTML化で使用）
- `flask`（`app.py` を使う場合のみ）

インストール例:

```powershell
pip install markdown pymdown-extensions flask
```

## Markdown 記法（推奨）

### Front Matter

Markdown先頭にFront Matterを付けると、一覧で分類・検索しやすくなります。

```yaml
---
category: 運用手順
tags: [手順, 申請, 社内]
---
```

- `category`: 一覧でのグループ名（未指定時は `未分類`）
- `tags`: タグフィルタ用。`[a, b]` または複数行リストに対応

### 強調用CSSクラス（本文内）

`html/style.css` で以下クラスを使用できます。

- `alert`
- `danger`
- `warn`
- `note`

例:

```html
<p class="warn">期限が近い項目です。</p>
```

## 注意点

- `md` / `html` ディレクトリ名は変更しない（`md_store.py` で固定参照）
- `html/` は書き込み権限が必要
- `build.py` は書き込み確認のため一時ファイル `.write_test` を作成
- `app.py` は `md` 直下の `*.md` を対象（サブディレクトリは対象外）
- `md/*.md` と `html/*.html` は `.gitignore` で除外済み（本命データの誤コミット防止）。
  サンプルとして追跡したいファイルは `.gitignore` に `!md/ファイル名.md` 形式の例外行を追記する

## メンテナンス

1. Front Matter運用を変更する場合  
`frontmatter.py` の `parse_front_matter`（app.py / build.py 共通）と `index.html` 生成ロジックを合わせて更新する。

2. 強調クラスを追加・変更する場合  
`html/style.css` と、このREADMEの「強調用CSSクラス」を同時に更新する。

3. 画像表示ルールを変更する場合  
`build.py` の `add_default_img_width_attr` を更新する。

4. 動作確認  
`python build.py` 実行後、`html/index.html` と対象ページをブラウザで確認する。

## 参考

- 装飾前提Markdownへ書き換えるためのプロンプト: `PROMPT.md`
- コミットメッセージ提案時に読み込む指示文: `docs/COMMIT_MESSAGE_INSTRUCTIONS.md`
- Markdown作成テンプレート: `docs/template.md`
- Issue関連メモ: `notes/issue/`
- 運用検討・実装メモ: `notes/operations/`

`docs/template.md` の使い方:
- 新規ドキュメント作成時に `docs/template.md` をコピーして開始する
- `## Quick Links` を実ファイルに差し替える
- リンク/画像の記法は `scripts/md_helper.ps1` で生成した文字列を貼り付ける
