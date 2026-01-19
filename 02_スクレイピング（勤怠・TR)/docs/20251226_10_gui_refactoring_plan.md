# GUI Refactoring Plan (Tkinter) - Revised

## 1. 目的
現在のコマンドライン入力（CLI）による操作対象の選択を、Python標準ライブラリの `Tkinter` を用いたGUI画面に置き換えることで、ユーザービリティを向上させる。
特に、**「勤怠入力」と「タスクレポート(TR)作成」という大きく異なる2つの操作**を明確に分離し、ユーザーが迷わずに選択できるUIを提供する。

## 2. 現状の課題
- 選択肢（`cl`, `h`, `y`...）がフラットに並んでおり、目的（勤怠管理 vs バグ票起票）の区別が一目でつきにくい。
- 不要な選択肢が常に表示されており、認知負荷が高い。
- 特定の選択肢（`up`）のみに追加パラメータ（環境名）が必要など、依存関係が複雑で見通しが悪い。

## 3. 改善案 (GUI設計)

### 画面イメージ
**2段階選択**を採用し、選択内容に応じて必要な項目のみをアクティブにする。

- **ウィンドウタイトル**: 自動化ツール実行設定
- **エリア1: メインモード選択** (ラジオボタン)
    1. **CrowdLog工数実績ダウンロード (勤怠)**
       - これを選択した場合、以下の詳細選択エリアは無効化（グレーアウト）または非表示。
    2. **タスクレポート作成 (TR)**
       - これを選択した場合、以下の詳細選択エリアが有効化される。

- **エリア2: TR詳細設定** (モードで「TR」選択時のみ有効)
    - **プロジェクト種別**: (コンボボックス または ラジオボタンリスト)
        - 標準, Yamaha, Tframe, Shimamura(本番), etc.
    - **対象環境**: (コンボボックス)
        - プロジェクト種別で「更新依頼 (UP依頼)」が選択された場合のみ有効化。
        - (UAT2, trainingGCP, etc.)

- **下部エリア**:
    - **[実行] ボタン**
    - **[終了] ボタン**

## 4. 実装計画

### 4.1 設定ファイル (`config/config.yaml`) の構造変更
フラットなリストではなく、モードとそれに紐づく詳細オプションという階層構造に変更する。

**変更後案:**
```yaml
menus:
  # メインモード定義
  modes:
    crowdlog:
      label: "CrowdLog工数実績ダウンロード"
      value: "cl" # 内部的な識別子
    task_report:
      label: "タスクレポート作成 (TR)"
      value: "tr" # 内部的な識別子。これを指定してさらに詳細分岐へ

  # TRモード選択時の詳細オプション
  tr_options:
    - key: "h"
      label: "標準"
    - key: "y"
      label: "Yamaha"
    - key: "tf"
      label: "Tframe"
    - key: "s"
      label: "Shimamura(本番サポート)"
    - key: "t"
      label: "Shimamura_SMBCPOS追加開発"
    - key: "up"
      label: "Shimamura_UAT_UP依頼"
      requires_environment: true # 環境選択を必須とするフラグ
    - key: "sm"
      label: "Shimamura_mysql対応"
  
  # 環境選択肢 (UP依頼などで使用)
  environment_options:
    t: "trainigGCP"
    u: "UAT2"
    st: "smbcpos_training"
    su: "smbcpos_uat"
```

### 4.2 ソースコードの変更

1.  **新規モジュール作成: `src/gui.py`**
    - `SelectionApp` クラスの実装。
    - **状態管理**:
        - `selected_mode`: 勤怠(`cl`) か TR(`tr`) か。
        - `selected_tr_type`: TRの場合の種別(`h`, `y`...)。
        - `selected_env`: 環境名。
    - **イベントハンドラ**:
        - モード切替時に「TR詳細エリア」の `state` を `normal` / `disabled` に切り替える。
        - TR種別切替時に「環境選択プルダウン」の `state` を切り替える。
    
2.  **`src/main.py` の修正**
    - GUIから返される戻り値の形式を変更。
    - 戻り値例: `('cl', None)` または `('up', 'UAT2')` のように、既存のロジック (`form_handler`) がそのまま解釈できる形式に変換して渡すアダプター処理を入れる。

## 5. ステップ
1.  `config.yaml` の構造を変更（バックアップ必須）。
2.  `src/gui.py` を作成し、新しいConfig構造を読み込んで動的に画面を生成するロジックを実装。
3.  `src/main.py` を繋ぎ込み、動作確認。