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

def _parse_extension_groups(config: configparser.ConfigParser) -> dict[str, str]:
    """設定から拡張子グループを解析する"""
    extension_groups = {}
    if config.has_section('ExtensionGroups'):
        for folder_name, extensions_str in config.items('ExtensionGroups'):
            for ext in extensions_str.replace(' ', '').split(','):
                if ext:
                    extension_groups[ext.lower()] = folder_name
    return extension_groups

def _parse_exclude_settings(config: configparser.ConfigParser) -> tuple[set[str], set[str]]:
    """設定から除外設定を解析する"""
    exclude_filenames = set()
    exclude_extensions = set()

    if config.has_section('Exclude'):
        if config.has_option('Exclude', 'filenames'):
            for fname in config.get('Exclude', 'filenames').replace(' ', '').split(','):
                if fname:
                    exclude_filenames.add(fname)
        if config.has_option('Exclude', 'extensions'):
            for ext in config.get('Exclude', 'extensions').replace(' ', '').split(','):
                if ext:
                    exclude_extensions.add(ext.lower())
    return exclude_filenames, exclude_extensions

def get_destination_directory(source_path: Path, target_dir: Path, extension_groups: dict[str, str]) -> Path:
    """ファイルの移動先ディレクトリを決定する"""
    file_extension = source_path.suffix[1:].lower()
    
    if file_extension in extension_groups:
        destination_folder_name = extension_groups[file_extension]
    else:
        destination_folder_name = file_extension if file_extension else "no_extension"
        
    destination_dir = target_dir / destination_folder_name
    
    if not destination_dir.exists():
        try:
            destination_dir.mkdir()
            logging.info(f"ディレクトリを作成しました: {destination_dir}")
        except OSError as e:
            logging.error(f"ディレクトリの作成に失敗しました: {destination_dir} - {e}")
            return None # ディレクトリ作成失敗時はNoneを返す
            
    return destination_dir

def move_file_with_rename(source_path: Path, destination_dir: Path) -> None:
    """ファイルを移動し、必要であればリネームする"""
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

def organize_files():
    """設定に基づいてファイルを整理する"""
    try:
        config = load_config()
        target_dir = Path(config.get('Settings', 'TargetDirectory'))
        log_dir_name = config.get('Settings', 'LogDirectoryName')
        extension_groups = _parse_extension_groups(config)
        exclude_filenames, exclude_extensions = _parse_exclude_settings(config)
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
        # ログディレクトリ自体はスキップする
        if source_path == log_dir:
            continue

        # ファイルでなければスキップ
        if not source_path.is_file():
            continue

        # 除外ファイル名リストに含まれていればスキップ
        if source_path.name in exclude_filenames:
            logging.info(f"除外設定によりスキップしました: {source_path.name}")
            continue

        # 除外拡張子リストに含まれていればスキップ
        file_extension = source_path.suffix[1:].lower()
        if file_extension in exclude_extensions:
            logging.info(f"除外設定によりスキップしました: {source_path.name} (拡張子: .{file_extension})")
            continue

        destination_dir = get_destination_directory(source_path, target_dir, extension_groups)
        if destination_dir is None: # ディレクトリ作成に失敗した場合
            continue
        
        move_file_with_rename(source_path, destination_dir)

    logging.info("すべての処理が完了しました。")

if __name__ == "__main__":
    organize_files()