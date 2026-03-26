"""
pytest 共通設定。
src/ をパスに追加し、テスト用YAMLフィクスチャを提供する。
"""
import sys
import os
import textwrap
import pytest

# src/ をモジュール検索パスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ---------------------------------------------------------------------------
# フィクスチャ: テスト用ディレクトリ構造を生成
# ---------------------------------------------------------------------------

MAIN_YAML_CONTENT = textwrap.dedent("""\
    app:
      download_dir: "data/downloads/"
      login:
        email: "test@example.com"
        password: "testpass"

    menus:
      modes:
        crowdlog:
          label: "CrowdLog"
          value: "cl"
        task_report:
          label: "Task Report"
          value: "tr"
      tr_options:
        - key: "h"
          label: "標準"
        - key: "y"
          label: "Yamaha"
      environment_options:
        - "UAT2"
        - "smbcpos_uat"

    masters:
      schools_projects:
        shimamura:
          - "SMMs001PH"
          - "SMMN003PH"
        yamaha:
          - "YMHs001PH"
""")

SHIMAMURA_YAML_CONTENT = textwrap.dedent("""\
    school_specific_defaults:
      h:
        Schools: "shimamura"
        Project: "SMMs001PH"
        Title: "(UATxxx)-----"
        Comments: "hc"
      s:
        Schools: "shimamura"
        Project: "SMMs001PH"
        Title: "(UATxxx)-----"
        Comments: "sc"
""")


@pytest.fixture()
def project_root(tmp_path, monkeypatch):
    """
    テスト用プロジェクトルートを tmp_path に構築し、
    カレントディレクトリをそこに変更するフィクスチャ。
    config_manager.py が使う相対パスに対応するため。
    """
    # ディレクトリ構造を作成
    (tmp_path / "config" / "modes" / "task_report").mkdir(parents=True)
    (tmp_path / "data").mkdir()

    # YAML ファイルを配置
    (tmp_path / "config" / "main.yaml").write_text(MAIN_YAML_CONTENT, encoding="utf-8")
    (tmp_path / "config" / "modes" / "task_report" / "shimamura.yaml").write_text(
        SHIMAMURA_YAML_CONTENT, encoding="utf-8"
    )

    monkeypatch.chdir(tmp_path)
    return tmp_path
