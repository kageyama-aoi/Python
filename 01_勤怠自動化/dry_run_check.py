
import sys
import os

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    print("Checking config loading...")
    import config
    config.load_config("config/config.yaml")
    print("Config loaded successfully.")
    
    # 新しい構造の確認
    menus = config.CONF.get('menus', {})
    if 'modes' in menus and 'tr_options' in menus:
        print("YAML structure: OK")
    else:
        print("YAML structure: NG (Missing modes or tr_options)")

    print("\nChecking GUI module import...")
    import gui
    print("GUI module imported successfully.")

    print("\nDry run completed successfully (Initial check).")

except Exception as e:
    print(f"\nDry run FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
