"""従来どおりのバッチ実行エントリ（プレビューなしで即振り分け）。

config.ini の TargetDirectory を対象に build_plan -> execute_plan を実行し、
結果を対象フォルダ内の logs/sort_log_*.txt に記録する。
"""
from __future__ import annotations

import configparser
import logging

from .config_io import load_config
from .organizer import build_plan, execute_plan, setup_file_logging


def _to_logging(message: str, level: str) -> None:
    logging.getLogger().log(logging.ERROR if level == "error" else logging.INFO, message)


def main() -> int:
    try:
        cfg = load_config()
    except (FileNotFoundError, configparser.Error) as e:
        print(f"設定ファイルの読み込みに失敗しました: {e}")
        return 1

    target_dir = cfg.target_dir
    log_dir = target_dir / cfg.log_dir_name
    setup_file_logging(log_dir)

    logging.info(f"処理を開始します。対象フォルダ: {target_dir}")
    if not target_dir.is_dir():
        logging.error(f"指定されたフォルダが見つかりません: {target_dir}")
        return 1

    plan = build_plan(target_dir, cfg)
    result = execute_plan(plan, on_log=_to_logging)

    logging.info(
        "完了: 移動 %d / 改名 %d / スキップ %d / 失敗 %d",
        result.moved,
        result.renamed,
        result.skipped,
        result.failed,
    )
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
