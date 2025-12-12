import os
import shutil
import logging
import configparser
from pathlib import Path
from datetime import datetime

def load_config() -> configparser.ConfigParser:
    """設定ファイルを読み込む"""
    config = configparser.ConfigParser()
    # スクリプトと同じディレクトリにあるconfig.iniを読み込む
    config_path = Path(__file__).parent / "config.ini"
    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
    config.read(config_path, encoding='utf-8')
    return config

def setup_logging(log_dir: Path) -> None:
    """ロギングの設定を行う"""
    log_dir.mkdir(exist_ok=True)
    log_file_path = log_dir / f"sort_log_{datetime.now():%Y%m%d_%H%M%S}.txt"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def organize_files():
    """設定に基づいてファイルを整理する"""
    try:
        config = load_config()
        target_dir = Path(config.get('Settings', 'TargetDirectory'))
        log_dir_name = config.get('Settings', 'LogDirectoryName')
    except (FileNotFoundError, configparser.Error) as e:
        print(f"設定ファイルの読み込みに失敗しました: {e}")
        return

    log_dir = target_dir / log_dir_name
    setup_logging(log_dir)

    logging.info(f"処理を開始します。対象ディレクトリ: {target_dir}")

    if not target_dir.is_dir():
        logging.error(f"指定されたディレクトリが見つかりません: {target_dir}")
        return

    for source_path in target_dir.iterdir():
        if not source_path.is_file() or source_path.parent == log_dir:
            continue

        extension = source_path.suffix[1:] if source_path.suffix else "no_extension"
        destination_dir = target_dir / extension
        
        if not destination_dir.exists():
            try:
                destination_dir.mkdir()
                logging.info(f"ディレクトリを作成しました: {destination_dir}")
            except OSError as e:
                logging.error(f"ディレクトリの作成に失敗しました: {destination_dir} - {e}")
                continue

        destination_path = destination_dir / source_path.name
        counter = 1
        while destination_path.exists():
            counter += 1
            new_name = f"{source_path.stem}_{counter}{source_path.suffix}"
            destination_path = destination_dir / new_name
        
        try:
            shutil.move(str(source_path), str(destination_path))
            if source_path.name != destination_path.name:
                logging.info(f"移動しました: {source_path.name} -> {destination_path.name} ({destination_dir.name})")
            else:
                logging.info(f"移動しました: {source_path.name} -> ({destination_dir.name})")
        except (OSError, shutil.Error) as e:
            logging.error(f"移動に失敗しました: {source_path.name} - {e}")

    logging.info("すべての処理が完了しました。")

if __name__ == "__main__":
    organize_files()
    os.system("pause")