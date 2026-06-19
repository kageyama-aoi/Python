import csv
import os
from datetime import datetime

# ==========================================
# ⚙️ 設定エリア（ここを変更してください）
# ==========================================
INPUT_FILE = 'users (3).csv'       # 読み込みたいファイル名
HEADER_NAME = 'user_name'          # 探したいカラム名（ヘッダー文字列）

# 🔍 モード選択（どちらかを選んでください）
# 'name'  -> HEADER_NAME に指定した名前の列を1行目から自動で探す
# 'index' -> これまで通り TARGET_COLUMN_INDEX で指定した列番号を直接使う
MODE = 'name'

# MODE = 'index' の場合のみ使用される列番号（0=1列目、1=2列目...）
TARGET_COLUMN_INDEX = 1            

# 出力ファイル名（{timestamp} の部分が自動で日時に変わります）
OUTPUT_FILE_TEMPLATE = 'generated_in_clause_{timestamp}.txt'


# ==========================================
# 🛠️ 処理エリア（ここは触らなくてOKです）
# ==========================================
def generate_in_clause():
    user_names = []
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ エラー: 入力ファイル '{INPUT_FILE}' が見つかりません。")
        return

    _, ext = os.path.splitext(INPUT_FILE)
    
    if ext.lower() == '.csv':
        # 1. CSVファイルを読み込む場合
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            # デフォルトとして直接指定の列番号を入れておく
            target_idx = TARGET_COLUMN_INDEX
            
            if MODE == 'name':
                # 📄 ヘッダー名から列番号を自動探索する処理
                try:
                    first_row = next(reader) # 1行目（ヘッダー行）を取得
                    if HEADER_NAME in first_row:
                        # 見つかったら、その位置（インデックス）を自動セット
                        target_idx = first_row.index(HEADER_NAME)
                        print(f"🔍 CSVからヘッダー '{HEADER_NAME}' を発見しました！（{target_idx + 1}列目）")
                    else:
                        # 見つからなかった場合の安全対策（バックアップ挙動）
                        print(f"⚠️ 警告: ヘッダー '{HEADER_NAME}' が見つかりません。設定の TARGET_COLUMN_INDEX ({TARGET_COLUMN_INDEX}) で処理します。")
                        if len(first_row) > target_idx:
                            user_names.append(first_row[target_idx].strip())
                except StopIteration:
                    print("❌ エラー: ファイルが空です。")
                    return
            
            # 2行目以降のデータを処理
            for row in reader:
                if row and len(row) > target_idx:
                    val = row[target_idx].strip()
                    if val == HEADER_NAME: # 重複スキップ用
                        continue
                    user_names.append(val)
                    
    else:
        # 2. テキストファイル（SQL結果など）を読み込む場合
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('+') or line.startswith('-') or HEADER_NAME in line:
                    continue
                if '|' in line:
                    parts = [p.strip() for p in line.split('|') if p.strip()]
                    if parts and len(parts) > TARGET_COLUMN_INDEX:
                        user_names.append(parts[TARGET_COLUMN_INDEX])
                else:
                    user_names.append(line)

    # 重複を削除して並び替え
    user_names = sorted(list(set(user_names)))

    # 各ユーザー名をシングルクォーテーションで囲んでカンマで結合
    quoted_users = [f"'{name}'" for name in user_names if name]
    in_clause_string = ", ".join(quoted_users)
    result_text = f"IN ({in_clause_string})"
    
    # 画面に表示
    print("\n--- 生成されたIN句 ---")
    print(result_text)
    print("----------------------")
    
    # テキストファイルに出力
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    actual_output_file = OUTPUT_FILE_TEMPLATE.format(timestamp=now_str)
    
    with open(actual_output_file, "w", encoding="utf-8") as f:
        f.write(result_text)
    print(f"\n結果を '{actual_output_file}' に保存しました。")

if __name__ == '__main__':
    generate_in_clause()