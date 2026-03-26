import pytest
import pandas as pd
from src.processor import load_and_filter_data, process_details, aggregate_monthly
from src.constants import InputCols as IC, InternalCols as RC


class TestLoadAndFilterData:

    def test_load_all(self, sample_timesheet_csv):
        """フィルタなしで全行読み込む"""
        df = load_and_filter_data(sample_timesheet_csv)
        assert len(df) == 3

    def test_filter_by_project(self, sample_timesheet_csv):
        """取引先名でフィルタリングする"""
        df = load_and_filter_data(sample_timesheet_csv, target_project="顧客A")
        assert len(df) == 2
        assert all(df[IC.CLIENT_NAME] == "顧客A")

    def test_filter_by_employee(self, sample_timesheet_csv):
        """社員名でフィルタリングする"""
        df = load_and_filter_data(sample_timesheet_csv, target_employee="鈴木花子")
        assert len(df) == 1
        assert df.iloc[0][IC.EMPLOYEE_NAME] == "鈴木花子"

    def test_filter_no_match_returns_empty(self, sample_timesheet_csv):
        """マッチしない条件で空DataFrameを返す"""
        df = load_and_filter_data(sample_timesheet_csv, target_project="存在しない案件")
        assert df.empty


class TestProcessDetails:

    def test_work_hours_calculated(self, sample_timesheet_df):
        """分から作業時間（時間）が計算される"""
        result = process_details(sample_timesheet_df)
        assert RC.WORK_HOURS in result.columns
        # ソート後の行順に依存しないよう全値で検証
        hours = set(result[RC.WORK_HOURS].tolist())
        assert 1.0 in hours
        assert 1.5 in hours
        assert 2.0 in hours

    def test_pj_code_combined(self, sample_timesheet_df):
        """PJコード列がコード:名称の形式で生成される"""
        result = process_details(sample_timesheet_df)
        assert RC.PJ_CODE in result.columns
        assert "PJ001:テストPJ" in result[RC.PJ_CODE].values

    def test_memo_columns_added(self, sample_timesheet_df):
        """メモ_区分・メモ_詳細の空列が追加される"""
        result = process_details(sample_timesheet_df)
        assert RC.MEMO_TYPE in result.columns
        assert RC.MEMO_DETAIL in result.columns

    def test_start_date_is_datetime(self, sample_timesheet_df):
        """開始日がdatetime型に変換される"""
        result = process_details(sample_timesheet_df)
        assert pd.api.types.is_datetime64_any_dtype(result[IC.START_DATE])

    def test_result_is_sorted(self, sample_timesheet_df):
        """社員名・PJコードでソートされている"""
        result = process_details(sample_timesheet_df)
        names = result[IC.EMPLOYEE_NAME].tolist()
        assert names == sorted(names)

    def test_original_df_not_modified(self, sample_timesheet_df):
        """元のDataFrameが変更されない（コピーで処理される）"""
        original_cols = list(sample_timesheet_df.columns)
        process_details(sample_timesheet_df)
        assert list(sample_timesheet_df.columns) == original_cols


class TestAggregateMonthly:

    def test_returns_empty_for_empty_df(self):
        """空DataFrameに対して空を返す"""
        result = aggregate_monthly(pd.DataFrame())
        assert result.empty

    def test_aggregates_by_month(self, sample_timesheet_df):
        """月単位で作業時間が集計される"""
        processed = process_details(sample_timesheet_df)
        result = aggregate_monthly(processed)
        assert not result.empty
        assert RC.WORK_HOURS in result.columns

    def test_work_hours_summed(self, sample_timesheet_df):
        """同月・同社員・同PJの作業時間が合算される"""
        processed = process_details(sample_timesheet_df)
        result = aggregate_monthly(processed)
        # 山田太郎 / PJ001:テストPJ の1月合計は 1.0 + 1.5 = 2.5h
        row = result[
            (result[IC.EMPLOYEE_NAME] == "山田太郎") &
            (result[RC.PJ_CODE] == "PJ001:テストPJ")
        ]
        assert len(row) == 1
        assert row.iloc[0][RC.WORK_HOURS] == pytest.approx(2.5)
