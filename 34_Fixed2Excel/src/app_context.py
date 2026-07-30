import logging
from dataclasses import dataclass

from src.config_manager import ConfigManager


@dataclass
class AppContext:
    """config/main.yaml の設定一式と logger を束ね、handler 群へそのまま渡す実行コンテキスト"""

    app_name: str
    encoding: str
    dirs: dict
    mapping_csv: str
    mapping_columns: dict
    record_type_codes: dict
    logger: logging.Logger


def create_context(logger):
    """config/main.yaml を読み込んで AppContext を組み立てる（CUI/GUI 共通の入口）"""
    cfg = ConfigManager().load_config()
    return AppContext(
        app_name=cfg.get("app_name", "34_Fixed2Excel"),
        encoding=cfg["encoding"],
        dirs=cfg["dirs"],
        mapping_csv=cfg["mapping_csv"],
        mapping_columns=cfg["mapping_columns"],
        record_type_codes=cfg["record_type_codes"],
        logger=logger,
    )
