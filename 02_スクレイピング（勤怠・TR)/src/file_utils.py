"""
ファイル操作に関連するユーティリティモジュール。
ダウンロードされたファイルの移動などを担当します。
"""
import os
import shutil
import time
import glob
from pathlib import Path

def move_latest_downloaded_file(download_dir, target_dir, file_pattern="*.csv", timeout=30):
    """
    ダウンロードフォルダ内の最新のファイルを、指定されたターゲットディレクトリに移動します。

    Args:
        download_dir (str): ブラウザのデフォルトダウンロードディレクトリ
        target_dir (str): 移動先のディレクトリ
        file_pattern (str): 対象とするファイルのパターン（デフォルトは *.csv）
        timeout (int): ファイル出現を待機する最大秒数
    """
    # ターゲットディレクトリが存在しない場合は作成
    os.makedirs(target_dir, exist_ok=True)

    # ダウンロード完了を待機（簡易的な実装：ファイル数が増えるのを待つか、最新ファイルが更新されるのを待つ）
    start_time = time.time()
    initial_files = set(glob.glob(os.path.join(download_dir, file_pattern)))
    
    print(f"Waiting for download in {download_dir}...")
    
    while time.time() - start_time < timeout:
        current_files = set(glob.glob(os.path.join(download_dir, file_pattern)))
        new_files = current_files - initial_files
        
        if new_files:
            # 新しく追加されたファイルの中で最も新しいものを取得
            latest_file = max(new_files, key=os.path.getmtime)
            
            # .crdownload (Chromeのダウンロード中一時ファイル) でないことを確認
            if not latest_file.endswith('.crdownload'):
                time.sleep(1) # 書き込み完了まで少し待機
                filename = os.path.basename(latest_file)
                target_path = os.path.join(target_dir, filename)
                
                print(f"Moving {latest_file} to {target_path}")
                shutil.move(latest_file, target_path)
                return target_path
        
        time.sleep(1)
    
    print("Download timeout reached.")
    return None
