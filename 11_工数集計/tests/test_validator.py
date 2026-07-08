import pytest
import pandas as pd
from src.validator import validate_timesheet_columns
from src.constants import InputCols as IC


REQUIRED_COLS = [
    IC.EMPLOYEE_CODE, IC.EMPLOYEE_NAME, IC.PROJECT_CODE, IC.PROJECT_NAME,
    IC.MINUTES, IC.START_DATE, IC.MEMO, IC.CLIENT_NAME,
    IC.START_TIME, IC.END_TIME, IC.PROCESS_1_CODE, IC.PROCESS_1_NAME,
]


class TestValidateTimesheetColumns:

    def test_valid_df_no_error(self):
        """必要な列が全て揃っていればエラーなし"""
        df = pd.DataFrame(columns=REQUIRED_COLS)
        validate_timesheet_columns(df)  # 例外が出なければOK

    def test_missing_single_column_exits(self, capsys):
        """1列欠損で SystemExit し、列名がメッセージに含まれる"""
        cols = [c for c in REQUIRED_COLS if c != IC.EMPLOYEE_NAME]
        df = pd.DataFrame(columns=cols)
        with pytest.raises(SystemExit):
            validate_timesheet_columns(df)
        captured = capsys.readouterr()
        assert IC.EMPLOYEE_NAME in captured.out

    def test_missing_multiple_columns_lists_all(self, capsys):
        """複数列欠損で全ての列名がメッセージに含まれる"""
        cols = [c for c in REQUIRED_COLS if c not in (IC.EMPLOYEE_NAME, IC.PROJECT_CODE)]
        df = pd.DataFrame(columns=cols)
        with pytest.raises(SystemExit):
            validate_timesheet_columns(df)
        captured = capsys.readouterr()
        assert IC.EMPLOYEE_NAME in captured.out
        assert IC.PROJECT_CODE in captured.out

    def test_extra_columns_are_ignored(self):
        """余分な列があってもエラーにならない"""
        df = pd.DataFrame(columns=REQUIRED_COLS + ["余分な列"])
        validate_timesheet_columns(df)  # 例外が出なければOK
