# Scalability Refactoring Plan

## 1. 目的
将来的な機能追加（モード追加）に備え、コードの拡張性と保守性を向上させる。
現在は `form_handler.py` や `main.py` に条件分岐 (`if type == 'cl'`) が散在しており、新機能追加のたびに既存コードを修正する必要がある。これを解消し、**「新しいファイルを追加するだけで機能拡張できる」** 構造を目指す。

## 2. 方針 (Step-by-Step)
一気に書き換えるのではなく、以下のフェーズに分けて段階的に実施する。

### Phase 1: Handlerの構造化 (Polymorphism)
現在の巨大な `FormAutomationHandler` クラスを、役割ごとに分割する。

1.  **基底クラス (`BaseHandler`) の作成**:
    - 全モード共通の処理（ドライバ保持、設定読み込みなど）を定義。
    - `run()` や `fill_form()` などの抽象メソッドを定義。
2.  **具象クラスの作成**:
    - `CrowdLogHandler`: 勤怠ダウンロード特有の処理（ログイン、日付入力、ダウンロード待機）を実装。
    - `TaskReportHandler`: バグ票起票などの処理を実装。
3.  **`form_handler.py` の修正**:
    - 既存のロジックを上記クラスに移動し、`main.py` からはクラスを切り替えてインスタンス化するように変更。

### Phase 2: Factoryパターンの導入
`main.py` 内の条件分岐を排除する。

1.  **HandlerFactory の作成**:
    - `school_type` (モード) を受け取り、適切な Handler クラスのインスタンスを返す単純なファクトリ関数を作成。
    - 例: `get_handler(driver, context) -> BaseHandler`
2.  **`main.py` の簡素化**:
    - `if user_select_school == 'cl': ... else: ...` という分岐を削除。
    - `handler = factory.get_handler(...)` -> `handler.run()` のように統一的な呼び出しに変更。

### Phase 3: Configの構造化と分割
設定ファイルが肥大化するのを防ぐ。

1.  **セクションの明確化**:
    - 現在の `school_specific_defaults` を、`modes` 定義の中に統合するなど、設定の構造を Handler クラスと対になるように整理する。
2.  **ファイル分割 (Optional)**:
    - 将来的に `config/modes/crowdlog.yaml`, `config/modes/task_report.yaml` のように分割し、読み込み時にマージする仕組みを導入。

## 3. 実装イメージ

### 現状 (`form_handler.py`)
```python
class FormAutomationHandler:
    def fill_form(self):
        if self.schools_type == 'cl':
            # CrowdLogの処理
        else:
            # TRの処理
```

### Phase 1 & 2 完了後
```python
# src/handlers/base_handler.py
class BaseHandler(ABC):
    @abstractmethod
    def run(self):
        pass

# src/handlers/crowdlog_handler.py
class CrowdLogHandler(BaseHandler):
    def run(self):
        self._login()
        self._input_dates()
        self._download()

# src/handler_factory.py
def create_handler(driver, context):
    mode = context['mode']
    if mode == 'cl':
        return CrowdLogHandler(driver, context)
    elif mode == 'tr':
        return TaskReportHandler(driver, context)
    ...
```

## 4. 次のアクション
まずは **Phase 1: Handlerの構造化** から着手することを推奨します。
これにより、ロジックが分離され、それぞれのコードが見通し良くなります。
