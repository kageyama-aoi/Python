## 仮のテストコード例（pytest）

```python
# test_failing.py
def test_this_will_always_fail():
    assert False, "This test is intentionally designed to fail for pre-push hook demonstration."
```

## pre-push スクリプト全文

`C:\Users\kageyama\Tools\Python\07_(掃除)Fileを拡張子ごと振り分け\.git\hooks\pre-push` に以下の内容でファイルを作成してください。

```bash
#!/bin/sh
#
# A pre-push hook to run pytest before pushing.
# If tests fail, the push is aborted.

echo "Running pytest tests before pushing..."

# Run pytest. Use 'python -m pytest' for better compatibility if pytest is not directly on PATH.
# The '--quiet' flag reduces pytest output, making the hook less verbose on success.
# The '--durations=0' flag shows slowest tests (optional).
if python -m pytest --quiet; then
  echo "Pytest tests passed. Pushing..."
  exit 0
else
  echo "Pytest tests failed! Aborting push."
  exit 1
fi
```

## 実行手順（コマンド付き）

1.  **テストファイルの作成:**
    プロジェクトのルートディレクトリに `test_failing.py` ファイルを以下の内容で作成します。

    ```python
    # test_failing.py
    def test_this_will_always_fail():
        assert False, "This test is intentionally designed to fail for pre-push hook demonstration."
    ```
    (※これは既に私が行いました。)

2.  **pre-pushフックファイルの作成:**
    `.git/hooks/pre-push` ファイルを上記「pre-push スクリプト全文」の内容で作成します。

    ```powershell
    # Windows PowerShell の場合
    Set-Content -Path ".git/hooks/pre-push" -Value '#!/bin/sh`n#`n# A pre-push hook to run pytest before pushing.`n# If tests fail, the push is aborted.`n`necho "Running pytest tests before pushing..."`n`n# Run pytest. Use '\'python -m pytest\'' for better compatibility if pytest is not directly on PATH.`n# The '\'--quiet\'' flag reduces pytest output, making the hook less verbose on success.`n# The '--durations=0' flag shows slowest tests (optional).`nif python -m pytest --quiet; then`n  echo "Pytest tests passed. Pushing..."`n  exit 0`nelse`n  echo "Pytest tests failed! Aborting push."`n  exit 1`nfi'
    ```
    (※Git BashやWSLを使用している場合は、通常の`touch .git/hooks/pre-push`でファイルを作成後、エディタで内容をペーストしても構いません。)

3.  **フックファイルに実行権限を付与:**
    Linux/macOS環境、またはGit Bash/WSLを使用している場合は、`chmod`コマンドで実行権限を付与します。

    ```bash
    chmod +x .git/hooks/pre-push
    ```
    (※PowerShellの場合はこの手順は不要なことが多いですが、問題が発生した場合はGit Bashなどで試してください。)

4.  **変更をコミット:**
    `test_failing.py` をステージングし、コミットします。

    ```bash
    git add test_failing.py
    git commit -m "Add a failing test for pre-push hook demo"
    ```

5.  **push を試行:**
    リモートリポジトリに push しようとします。

    ```bash
    git push origin main # または対象のブランチ名
    ```

## push 失敗時の出力例

上記の`pre-push`スクリプトと`test_failing.py`が存在する状態で `git push` を実行すると、以下のような出力が表示され、pushは中断されます。

```
Running pytest tests before pushing...
============================= test session starts ==============================
platform win32 -- Python 3.x.x, pytest-x.x.x, pluggy-x.x.x
rootdir: C:\Users\kageyama\Tools\Python\07_(掃除)Fileを拡張子ごと振り分け
collected 1 item

test_failing.py F                                                        [100%]

=================================== FAILURES ===================================
___________________________ test_this_will_always_fail ___________________________

    def test_this_will_always_fail():
>       assert False, "This test is intentionally designed to fail for pre-push hook demonstration."
E       AssertionError: This test is intentionally designed to fail for pre-push hook demonstration.

test_failing.py:3: AssertionError
=========================== short test summary info ============================
FAILED test_failing.py::test_this_will_always_fail - AssertionError: This test is intentionally designed to fail for pre-push hook demonstration.
============================== 1 failed in x.xxs ===============================
Pytest tests failed! Aborting push.
To <リモートリポジトリのURL>
 ! [remote rejected] main -> main (pre-push hook declined)
error: failed to push some refs to '<リモートリポジトリのURL>'
```

## 仕組みの解説（短く）

Git の `pre-push` フックは、`git push` コマンドがリモートリポジトリに変更を送信する直前に実行されるスクリプトです。このスクリプトは、終了コードが `0` の場合は push を続行し、`0` 以外（通常 `1`）の場合は push を中断します。今回の設定では、`pre-push` スクリプトが `pytest` を実行し、`pytest` のテスト結果がフックの終了コードを決定します。テストが失敗すると `pytest` は `0` 以外の終了コードを返すため、`pre-push` フックが中断され、結果として `git push` も失敗します。これにより、テストが通らないコードが誤ってリモートにプッシュされるのを防ぎます。
