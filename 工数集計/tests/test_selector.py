import pytest
import pandas as pd
from unittest.mock import patch
from src.selector import select_target
from src.constants import InputCols as IC


@pytest.fixture
def timesheet_csv(tmp_path):
    """複数の取引先・社員を持つCSVファイル"""
    df = pd.DataFrame({
        IC.CLIENT_NAME: ["顧客A", "顧客A", "顧客B"],
        IC.EMPLOYEE_NAME: ["山田太郎", "鈴木花子", "山田太郎"],
        IC.EMPLOYEE_CODE: ["E001", "E002", "E001"],
        IC.PROJECT_CODE: ["PJ001", "PJ001", "PJ002"],
        IC.PROJECT_NAME: ["テストPJ", "テストPJ", "別PJ"],
        IC.MINUTES: [60, 90, 120],
        IC.START_TIME: ["09:00", "10:00", "09:00"],
        IC.END_TIME: ["10:00", "11:30", "11:00"],
        IC.MEMO: ["設計,詳細設計", "実装,コーディング", "テスト,単体テスト"],
        IC.START_DATE: ["2024-01-10", "2024-01-11", "2024-01-10"],
        IC.PROCESS_1_CODE: ["D", "I", "T"],
        IC.PROCESS_1_NAME: ["設計", "実装", "テスト"],
    })
    path = tmp_path / "timesheet.csv"
    df.to_csv(path, index=False, encoding='cp932')
    return path


class TestSelectTarget:

    def test_returns_selected_project_and_employee(self, timesheet_csv):
        """番号を入力するとプロジェクト・社員名が返る"""
        with patch("builtins.input", side_effect=["1", "1"]):
            project, employee = select_target(timesheet_csv)
        assert project != ""
        assert employee != ""

    def test_zero_returns_all(self, timesheet_csv):
        """0を選ぶと空文字（全件）が返る"""
        with patch("builtins.input", side_effect=["0", "0"]):
            project, employee = select_target(timesheet_csv)
        assert project == ""
        assert employee == ""

    def test_default_used_when_provided(self, timesheet_csv):
        """デフォルト値が提供され Enter を押すとデフォルトが使われる"""
        with patch("builtins.input", side_effect=["", ""]):
            project, employee = select_target(
                timesheet_csv,
                default_project="顧客A",
                default_employee="山田太郎"
            )
        assert project == "顧客A"
        assert employee == "山田太郎"

    def test_invalid_input_reprompts(self, timesheet_csv):
        """範囲外の番号を入力すると再入力を促す"""
        with patch("builtins.input", side_effect=["99", "1", "1"]):
            project, employee = select_target(timesheet_csv)
        assert project != ""

    def test_project_list_shows_unique_values(self, timesheet_csv, capsys):
        """取引先の一覧が重複なく表示される"""
        with patch("builtins.input", side_effect=["0", "0"]):
            select_target(timesheet_csv)
        captured = capsys.readouterr()
        assert "顧客A" in captured.out
        assert "顧客B" in captured.out
        assert captured.out.count("顧客A") == 1  # 重複なし
