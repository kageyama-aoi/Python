import pytest
import pandas as pd
import json
import os
from pathlib import Path


@pytest.fixture
def sample_timesheet_df():
    """タイムシートのサンプルDataFrame"""
    return pd.DataFrame({
        "社員コード": ["E001", "E001", "E002"],
        "社員名": ["山田太郎", "山田太郎", "鈴木花子"],
        "プロジェクトコード": ["PJ001", "PJ001", "PJ002"],
        "プロジェクト名": ["テストPJ", "テストPJ", "別PJ"],
        "分": [60, 90, 120],
        "開始時間": ["09:00", "10:00", "09:00"],
        "終了時間": ["10:00", "11:30", "11:00"],
        "メモ": ["設計,詳細設計", "実装,コーディング", "テスト,単体テスト"],
        "取引先名": ["顧客A", "顧客A", "顧客B"],
        "開始日": ["2024-01-10", "2024-01-11", "2024-01-10"],
        "工程１:管理コード": ["D", "I", "T"],
        "工程１:名称": ["設計", "実装", "テスト"],
    })


@pytest.fixture
def sample_timesheet_csv(tmp_path, sample_timesheet_df):
    """タイムシートCSVファイル（一時ファイル）"""
    csv_path = tmp_path / "timesheet.csv"
    sample_timesheet_df.to_csv(csv_path, index=False, encoding='cp932')
    return csv_path


@pytest.fixture
def sample_bugs_df():
    """TRリストのサンプルDataFrame"""
    return pd.DataFrame({
        "ID": ["BUG-001", "BUG-002"],
        "タイトル": ["ログインエラー", "集計ズレ"],
        "状態": ["Open", "Closed"],
    })


@pytest.fixture
def sample_bugs_csv(tmp_path, sample_bugs_df):
    """バグCSVファイル（一時ファイル）"""
    csv_path = tmp_path / "bugs.csv"
    sample_bugs_df.to_csv(csv_path, index=False, encoding='utf-8')
    return csv_path


@pytest.fixture
def sample_config_json(tmp_path):
    """設定ファイル（一時ファイル）"""
    config = {"target_project": "顧客A", "target_employee": "山田太郎"}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding='utf-8')
    return config_path
