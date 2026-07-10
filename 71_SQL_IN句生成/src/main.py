import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logger
from src.config_manager import ConfigManager
from src.handlers.in_clause_generator import generate, load_table
from src.handlers.input_resolver import (
    InputCancelled,
    resolve_input_csv,
    resolve_user_column,
)


def main():
    logger = setup_logger()
    logger.info("Application started.")

    config = ConfigManager().load_config()
    logger.info(f"Loaded config for: {config.get('app_name', 'Unknown')}")

    try:
        path = resolve_input_csv(sys.argv, config["input"], logger)
        df = load_table(path, config["input"].get("encoding", "utf-8"))
        logger.info(f"読込: {path} ({len(df)}行 x {len(df.columns)}列)")
        user_column = resolve_user_column(sys.argv, list(df.columns),
                                          config["filter"], logger)
    except InputCancelled as e:
        logger.info(str(e))
        print(str(e))
        return

    result = generate(config, logger, df, user_column)
    print(f"抽出件数: {result['count']}")
    print(f"-> '{result['txt_path']}' に書き出しました（SQLツールにコピペ用）")
    print(f"-> '{result['csv_path']}' に書き出しました（Excel確認用）")


if __name__ == "__main__":
    main()
