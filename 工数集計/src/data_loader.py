import json
import pandas as pd
from . import config as cfg

def load_config():
    """設定ファイルを読み込む"""
    with open(cfg.CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_timesheet(file_path):
    """タイムシートCSVを読み込む"""
    return pd.read_csv(file_path, encoding=cfg.ENCODING_CP932)

def load_bugs_csv(file_path):
    """バグ情報CSVを読み込む"""
    return pd.read_csv(file_path, encoding=cfg.ENCODING_UTF8)
