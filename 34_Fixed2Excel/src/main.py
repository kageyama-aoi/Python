import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app_context import create_context
from src.utils.logger import setup_logger
from src.handlers import setup_handler, mapping_handler, fixed_to_excel, excel_to_fixed

MENU = """
=== 34_Fixed2Excel ===
1: 環境初期化（フォルダ作成 + サンプルConfig/固定長テキスト生成）
2: mapping.csv 更新（inputの新規ファイルを追記）
3: 固定長テキスト -> Excel 変換
4: Excel -> 固定長テキスト 復元
0: 終了
"""


def main():
    logger = setup_logger()
    ctx = create_context(logger)
    logger.info(f"{ctx.app_name} を起動しました。")

    while True:
        print(MENU)
        choice = input("番号を選択してください: ").strip()

        if choice == "1":
            setup_handler.init_environment(ctx)
        elif choice == "2":
            mapping_handler.build_or_update_mapping(ctx)
        elif choice == "3":
            fixed_to_excel.convert_all(ctx)
        elif choice == "4":
            excel_to_fixed.restore_all(ctx)
        elif choice == "0":
            logger.info("終了します。")
            break
        else:
            print("無効な選択です。もう一度入力してください。")


if __name__ == "__main__":
    main()
