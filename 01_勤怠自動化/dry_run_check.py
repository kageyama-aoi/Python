import sys
import os

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    print("Checking config loading (Split Configs).")
    import config
    # main.yaml をロード
    config.load_config("config/main.yaml")
    
    # マージ確認
    print("\n--- Merge Verification ---")
    
    # 1. Main Configの内容
    if 'app' in config.CONF:
        print("Main Config (app.url): OK")
    else:
        print("Main Config: NG")

    # 2. CrowdLog Configの内容
    if 'cl' in config.CONF.get('school_specific_defaults', {}):
        print("Mode Config (CrowdLog): OK")
    else:
        print("Mode Config (CrowdLog): NG")

    # 3. Shimamura Configの内容
    if 's' in config.CONF.get('school_specific_defaults', {}):
        print("Mode Config (Shimamura): OK")
    else:
        print("Mode Config (Shimamura): NG")

    # 4. Tframe Templateのマージ確認
    if 'templates' in config.CONF and 'tf' in config.CONF['templates']:
        print("Mode Config (Tframe Templates): OK")
    else:
        print("Mode Config (Tframe Templates): NG")


    print("\nChecking GUI module import...")
    import gui
    print("GUI module imported successfully.")

    print("\nDry run completed successfully (Config Split Check).")

except Exception as e:
    print(f"\nDry run FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)