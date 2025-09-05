import datetime
import random

now = datetime.datetime.now()
random_number = random.randint(10000, 99999)

# ユーザー定義
input_tr_csv ='./input/bugs.csv'
input_timesheet_csv = './input/timesheet.csv'
target_project = '島村楽器' # 島村楽器
sheet_name_detail = 'Detailed Data_' + target_project
sheet_name_processed = 'Detailed Processed Data_' + target_project
sheet_name_monthly_summary = 'Monthly Summary_' + target_project

# temp_file01 = f'output_summary_{now:%Y%m%d_%H%M%S}_{random_number}.xlsx'
# temp_file02 = 'temp_file1.xlsx' 
# final_output = 'output_'+target_project+'_aggregate_results.xlsx'  

temp_file01 = f'./output/output_summary_{now:%Y%m%d_%H%M%S}_{random_number}.xlsx'
temp_file02 = './output/temp_file1.xlsx'
final_output = f'./output/output_{target_project}_aggregate_results.xlsx'