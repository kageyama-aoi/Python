# Full Separation Plan (Logic & Config) - Revised

## 1. 目的
`main.py` に残っている「モードごとの分岐処理（URL決定など）」を完全に排除し、設定ファイルとロジックの責務分離を徹底する。
また、`config/main.yaml` に混在している「特定モード専用のセレクタやフィールド定義」を各モードのファイルへ移設し、真のモジュール化を実現する。

## 2. 現状の課題
- **Configの混在**:
    - `config/main.yaml` に、CrowdLog専用の `selectors`（ログイン、ダウンロードボタン）や URL が残っている。
    - `fields` 定義も、CrowdLog用（StartDate等）とTR用（Project等）が混ざっている。
- **main.pyの密結合**:
    - `main.py` が `if school == 'cl'` でURLを切り替えるロジックを持ってしまっている。

## 3. 改善案

### 3.1 Configの完全分離と整理
`config/main.yaml` は「アプリ全体の基盤設定」のみとし、各モード固有の値は全て `modes/` 配下へ移動する。

#### A. `config/main.yaml` (アプリ基盤)
```yaml
app:
  download_dir: "data/downloads/"
  # ログ設定など
menus:
  # メニュー構造自体はアプリの入り口なのでここに残す
  modes: ...
```

#### B. `config/modes/crowdlog.yaml` (勤怠専用)
```yaml
crowdlog_settings:
  entry_url: "https://app.crowdlog.jp/download/?rm=timesheet"
  
  selectors:
    login_email: "email"
    login_password: "passwd"
    login_button: "#idLoginForm button[type='submit']"
    download_button: "#idDownloadForm button"
    
  fields:
    StartDate: { locator: "from", type: "text" }
    EndDate: { locator: "to", type: "text" }
```

#### C. `config/modes/task_report/common.yaml` (TR共通)
新規作成し、TR全般で使う設定をまとめる。
```yaml
task_report_settings:
  entry_url: "https://taskreport.e-school.jp/bugfix.php"
  
  # "new_bug_button" は直接URL遷移するなら不要になる可能性が高いが、
  # 残すならここに記述。
  selectors:
    new_bug_button: "goindex"

  fields:
    Schools: { locator: "who_edit", type: "select" }
    Project: { locator: "project", type: "text" }
    # ... 他のTR用フィールド
```

### 3.2 ロジックの移動 (Navigation Responsibility)
「ブラウザで初期URLを開く」という処理を、`main.py` から `Handler` クラスへ移動する。

**`BaseHandler` の変更:**
```python
class BaseHandler(ABC):
    def run(self):
        """テンプレートメソッド"""
        self.navigate()  # 各ハンドラが自分の責任でURLを開く
        self.execute()   # フォーム入力

    @abstractmethod
    def navigate(self):
        pass
```

**各ハンドラの実装:**
- `CrowdLogHandler`: `CONF['crowdlog_settings']['entry_url']` を開く。
- `TaskReportHandler`: `CONF['task_report_settings']['entry_url']` を開く。

### 3.3 main.py の単純化
`main.py` は具体的なURLやセレクタを知る必要がなくなる。

**変更後の `main.py`:**
```python
def main():
    # ...初期化...
    
    # ハンドラ生成 (Factory or Dispatcher)
    handler = FormAutomationHandler(driver, context)
    
    # 実行
    handler.run()
```

## 4. 実施ステップ
1.  **Config整理**:
    - `config/modes/task_report/common.yaml` を作成。
    - `main.yaml` から `selectors`, `fields`, `url` を切り出し、適切なYAMLへ移動。
    - 古い `tr_field_mappings` という名前をやめ、わかりやすい構造にする。
2.  **Handler改修**:
    - Configの参照先キーが変わるため（`CONF['selectors']` → `CONF['crowdlog_settings']['selectors']` 等）、コードを修正。
    - `navigate()` メソッドの実装。
3.  **main.py修正**:
    - `driver.get()` を削除し、`handler.run()` 呼び出しに変更。

この改修により、例えば「勤怠システムがCrowdLogから別のSaaSに変わった」場合でも、`config/modes/new_system.yaml` と `NewSystemHandler` を作るだけで済み、`main.yaml` や `main.py` を汚さずに移行できます。