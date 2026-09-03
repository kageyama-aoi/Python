import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app_context import create_context
from src.utils.logger import setup_logger
from src.handlers import setup_handler, mapping_handler, fixed_to_excel, diff_checker

MENU = """
=== 34_Fixed2Excel ===
1: 環境初期化（フォルダ作成 + サンプルConfig/固定長テキスト生成）
2: mapping.csv 更新（inputの新規ファイルを追記）
3: 固定長テキスト -> Excel 変換
4: Excel -> 固定長テキスト 復元（続けて差分チェックも実行）
5: 差分チェック（入力 vs 復元後）のみ
0: 終了
"""


def main():
    logger = setup_logger()
    ctx = create_context(logger)
    logger.info(f"{ctx.app_name} 起動")

    while True:
        print(MENU)
        choice = input("番号を選択してください: ").strip()

        try:
            if choice == "1":
                setup_handler.init_environment(ctx)
            elif choice == "2":
                mapping_handler.build_or_update_mapping(ctx)
            elif choice == "3":
                fixed_to_excel.convert_all(ctx)
            elif choice == "4":
                diff_checker.restore_and_check(ctx)
            elif choice == "5":
                diff_checker.check_all(ctx)
            elif choice == "0":
                logger.info("終了")
                break
            else:
                print("無効な選択です。もう一度入力してください。")
        except Exception:
            logger.exception("処理中にエラーが発生しました。")


if __name__ == "__main__":
    main()
