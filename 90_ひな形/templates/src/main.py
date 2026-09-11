import os
import sys

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.logger import setup_logger
from src.config_manager import ConfigManager


def main():
    logger = setup_logger()
    logger.info("Application started.")

    # 設定の読み込み例
    config = ConfigManager().load_config()
    logger.info(f"Loaded config for: {config.get('app_name', 'Unknown')}")

    print(f"Hello, {config.get('app_name')}!")


if __name__ == "__main__":
    main()
