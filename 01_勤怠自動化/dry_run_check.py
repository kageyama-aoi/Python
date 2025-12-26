import sys
import os

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    print("Checking config loading (Split Configs - Final).")
    import config
    # main.yaml をロード
    config.load_config("config/main.yaml")
    
    # マージ確認
    print("\n--- Merge Verification ---")
    
    # 1. Main Configの内容 (app.download_dir)
    if 'app' in config.CONF and 'download_dir' in config.CONF['app']:
        print("Main Config (download_dir): OK")
    else:
        print("Main Config: NG")

    # 2. CrowdLog Configの内容 (entry_url, selectors)
    if 'crowdlog_settings' in config.CONF:
        cl = config.CONF['crowdlog_settings']
        if 'entry_url' in cl and 'selectors' in cl:
            print("Mode Config (CrowdLog Settings): OK")
        else:
            print("Mode Config (CrowdLog Settings): NG - Missing keys")
    else:
        print("Mode Config (CrowdLog Settings): NG - Key not found")

    # 3. TaskReport Common Configの内容
    if 'task_report_settings' in config.CONF:
        tr = config.CONF['task_report_settings']
        if 'fields' in tr and 'selectors' in tr:
            print("Mode Config (TR Common Settings): OK")
        else:
             print("Mode Config (TR Common Settings): NG - Missing keys")
    else:
        print("Mode Config (TR Common Settings): NG - Key not found")

    # 4. Shimamura Configの内容
    if 's' in config.CONF.get('school_specific_defaults', {}):
        print("Mode Config (Shimamura Defaults): OK")
    else:
        print("Mode Config (Shimamura Defaults): NG")

    print("\nChecking GUI module import...")
    import gui
    print("GUI module imported successfully.")

    print("\nDry run completed successfully (Config Final Split Check).")

except Exception as e:
    print(f"\nDry run FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
