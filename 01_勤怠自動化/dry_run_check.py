import sys
import os

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    print("Checking config loading (Common Defaults Move)...")
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

    # 2. Common Defaults (Moved from main to TR common)
    if 'common_defaults' in config.CONF:
        cd = config.CONF['common_defaults']
        if 'Schools' in cd and cd['Schools'] == 'shimamura':
            print("Common Defaults (Merged): OK")
        else:
            print("Common Defaults (Merged): NG - Content mismatch")
    else:
        print("Common Defaults (Merged): NG - Key not found")

    # 3. CrowdLog Configの内容
    if 'crowdlog_settings' in config.CONF:
        print("Mode Config (CrowdLog): OK")
    else:
        print("Mode Config (CrowdLog): NG")

    print("\nDry run completed successfully.")

except Exception as e:
    print(f"\nDry run FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)