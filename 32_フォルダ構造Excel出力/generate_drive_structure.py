import os
import pandas as pd
import json
import datetime
import re
import logging
import tkinter as tk
from tkinter import filedialog

# === 🔧 設定ファイルのパス ===
# スクリプトと同じディレクトリにある config.json を参照
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(BASE_DIR, "config.json")
LOG_DIR = os.path.join(BASE_DIR, "logs")

def setup_logging():
    """ロギングを設定する"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)
    
    log_filename = os.path.join(LOG_DIR, f"script_{datetime.datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler() # コンソールにも出力
        ])

# === カスタム例外クラスの定義 ===
class ScriptError(Exception):
    """スクリプトのベースとなる例外クラス"""
    pass

class ConfigError(ScriptError):
    """設定関連のエラー"""
    pass

class ScanError(ScriptError):
    """ディレクトリスキャン中のエラー"""
    pass
class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self._config = self._load()
        self._validate()
        self._set_defaults()

    def _load(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise ConfigError(f"設定ファイル '{self.config_path}' が見つかりませんでした。")
        except json.JSONDecodeError:
            raise ConfigError(f"設定ファイル '{self.config_path}' のJSON形式が正しくありません。")

    def _validate(self):
        required_keys = ["root_dir", "output_base_dir", "output_filename"]
        if not all(key in self._config for key in required_keys):
            raise ConfigError(f"設定ファイル '{self.config_path}' に必須キー ({', '.join(required_keys)}) が不足しています。")

        if not isinstance(self._config["root_dir"], str):
            raise ConfigError(f"設定 'root_dir' は文字列である必要があります。設定値: {self._config['root_dir']}")
        # 他のキーの型チェックもここに追加可能
        # 例: if not os.path.isdir(self.root_dir): raise ConfigError(f"root_dir '{self.root_dir}' が見つからないか、ディレクトリではありません。")

    def _set_defaults(self):
        self._config.setdefault("excluded_extensions", [])
        self._config.setdefault("excluded_folder_names", [])

    @property
    def root_dir(self):
        return self._config["root_dir"]

    def save_root_dir(self, new_root_dir):
        """root_dir を更新し、次回のデフォルト選択先として config.json に書き戻す"""
        self._config["root_dir"] = new_root_dir
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)
        logging.info(f"config.json の root_dir を更新しました: {new_root_dir}")

    @property
    def output_base_dir(self):
        path = os.path.expanduser(self._config["output_base_dir"])
        if not os.path.isabs(path):
            path = os.path.join(BASE_DIR, path)
        return path

    @property
    def output_filename(self):
        return self._config["output_filename"]

    def get_excluded_extensions(self):
        return [ext.lower() for ext in self._config.get("excluded_extensions", [])]

    def get_excluded_folder_names(self):
        return [name.lower() for name in self._config.get("excluded_folder_names", [])]

def format_size(size_bytes):
    """バイト数を人が読みやすい単位（B/KB/MB/GB/TB）の文字列に変換する"""
    if size_bytes is None:
        return ''
    size = float(size_bytes)
    for unit in ('B', 'KB', 'MB', 'GB'):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == 'B' else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

class ScannedItem:
    """スキャンで見つかった1件のファイル/フォルダを表す"""
    __slots__ = ('full_path', 'parent_dir', 'levels', 'name', 'item_type', 'size_bytes')

    def __init__(self, full_path, parent_dir, levels, name, item_type, size_bytes=None):
        self.full_path = full_path
        self.parent_dir = parent_dir
        self.levels = levels
        self.name = name
        self.item_type = item_type
        self.size_bytes = size_bytes

class DirectoryScanner:
    def __init__(self, root_path, excluded_extensions=None, excluded_folder_names=None):
        self.root_path = root_path
        self.excluded_extensions = excluded_extensions if excluded_extensions is not None else []
        self.excluded_folder_names = excluded_folder_names if excluded_folder_names is not None else []
        self.scanned_data = []

    def scan(self):
        """
        指定されたディレクトリをスキャンし、ファイル構造データを ScannedItem のリストとして収集する。
        収集されたデータは self.scanned_data にも格納される。
        """
        if not os.path.isdir(self.root_path):
            # logging.warning は残しつつ、呼び出し元で処理できるように例外も発生させるか検討
            # ここでは DirectoryScanner の責務としてスキャン対象がないことを警告し、空リストを返す
            logging.warning(f"指定されたルートディレクトリ '{self.root_path}' が見つからないか、ディレクトリではありません。")
            return []

        excluded_folder_names_lower = [name.lower() for name in self.excluded_folder_names]
        file_structure = []

        for dirpath, dirnames, filenames in os.walk(self.root_path):
            dirnames.sort()
            filenames.sort()

            rel_path_to_item_parent = os.path.relpath(dirpath, self.root_path)
            parent_levels = rel_path_to_item_parent.split(os.sep) if rel_path_to_item_parent != '.' else []

            original_dirnames = list(dirnames)
            dirnames[:] = [d for d in dirnames if d.lower() not in excluded_folder_names_lower]
            for excluded_dir in set(original_dirnames) - set(dirnames):
                logging.info(f"除外しました (フォルダ名): {os.path.join(dirpath, excluded_dir)} およびその配下")

            for dirname in dirnames:
                item_full_path = os.path.join(dirpath, dirname)
                # フォルダの配下合計サイズは計算しない（処理速度とシンプルさを優先）
                file_structure.append(ScannedItem(item_full_path, dirpath, parent_levels, dirname, 'folder'))

            for filename in filenames:
                _name, ext = os.path.splitext(filename)
                # 拡張子リストと比較する際は、設定ファイルから読み込んだものをそのまま使う (小文字変換はConfigManagerで行っている)
                if ext.lower() in self.excluded_extensions or filename in self.excluded_extensions:
                    logging.info(f"除外しました (拡張子/ファイル名): {os.path.join(dirpath, filename)}")
                    continue

                item_full_path = os.path.join(dirpath, filename)
                try:
                    size_bytes = os.path.getsize(item_full_path)
                except OSError as e:
                    logging.warning(f"サイズを取得できませんでした: {item_full_path} ({e})")
                    size_bytes = None
                file_structure.append(ScannedItem(item_full_path, dirpath, parent_levels, filename, 'file', size_bytes))

        self.scanned_data = file_structure
        return self.scanned_data

def create_dataframe_with_fullpath(scanned_items):
    """収集した ScannedItem のリストから Pandas DataFrame を作成する。フルパス列・タイプ列・サイズ列を含む。"""
    if not scanned_items:
        return pd.DataFrame()

    max_levels_plus_name_len = max(
        (len(item.levels) + 1 for item in scanned_items), default=0
    )

    processed_data = []
    for item in scanned_items:
        # アイテムが 'file' の場合、表示する親のフルパスを空にする
        parent_dir_fullpath_display = '' if item.item_type == 'file' else item.parent_dir

        levels_and_name_parts = item.levels + [item.name]
        padded_parts = levels_and_name_parts + [''] * (max_levels_plus_name_len - len(levels_and_name_parts))

        size_bytes_display = item.size_bytes if item.size_bytes is not None else ''
        size_display = format_size(item.size_bytes)

        processed_data.append(
            [item.full_path, item.item_type, parent_dir_fullpath_display, size_bytes_display, size_display] + padded_parts
        )

    level_columns = [] # type: ignore
    if max_levels_plus_name_len > 1: # Level列が存在する場合 (アイテム名列以外にレベル列がある)
        level_columns = [f"Level{i+1}" for i in range(max_levels_plus_name_len - 1)]

    final_columns = ['_item_self_path', 'タイプ', 'フルパス', 'サイズ(バイト)', 'サイズ']
    if max_levels_plus_name_len > 0: # アイテム名またはLevel列が存在する場合
        final_columns.extend(level_columns)
        final_columns.append('アイテム名') # 以前は 'ファイル名'

    return pd.DataFrame(processed_data, columns=final_columns)

def save_dataframe_to_excel(df, excel_path):
    """DataFrameをExcelファイルとして保存し、条件付き書式とハイパーリンクを適用する"""
    try:
        # 表示用のDataFrameから内部処理用の列を除外
        df_display = df.drop(columns=['_item_self_path'])

        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            # Pandasのデフォルトヘッダー書き込みを抑制し、データのみ書き込む (ヘッダーは後で手動設定)
            df_display.to_excel(writer, index=False, sheet_name='Sheet1', startrow=1, header=False)
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']

            # ヘッダー用の書式を定義
            header_format = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': 'black', 'align': 'center', 'valign': 'vcenter'})

            # ヘッダーを手動で書き込む
            for col_num, value in enumerate(df_display.columns.values):
                worksheet.write(0, col_num, value, header_format)

            hyperlink_format = workbook.add_format({'font_color': 'blue', 'underline': 1})

            # 書式を定義
            folder_format = workbook.add_format({'bg_color': '#FFFFCC', 'bold': True}) # 薄い黄色、太字
            file_format = workbook.add_format({'bg_color': '#CCEEFF'})   # 薄い水色

            try:
                # 表示用DataFrameでのタイプ列の位置を再計算 (df_display基準)
                type_col_idx_display = df_display.columns.get_loc('タイプ')
                # 表示用DataFrameでのフルパス列の位置
                fullpath_col_idx_display = df_display.columns.get_loc('フルパス')
            except KeyError:
                logging.warning("DataFrameに 'タイプ'列または'フルパス'列が見つかりません。書式設定に影響する可能性があります。")
                return

            # ハイパーリンクの設定 (to_excelで書き込んだセルに対してURLを設定)
            # dfのインデックスを使って元のデータにアクセス
            for row_idx in df.index:
                excel_data_row = row_idx + 1 # Excelの行は1から始まる (0行目はヘッダー)
                item_actual_path = df.loc[row_idx, '_item_self_path']
                # 表示されるフルパス文字列 (ファイルの場合は空になっているはず)
                display_text_for_link = str(df.loc[row_idx, 'フルパス'])
                
                # 表示テキストが空でなければハイパーリンクを設定
                if display_text_for_link:
                    url = f"file:///{item_actual_path.replace(os.sep, '/')}"
                    # フルパス列 (df_displayでのインデックス fullpath_col_idx_display) にハイパーリンクを設定
                    worksheet.write_url(excel_data_row, fullpath_col_idx_display, url, string=display_text_for_link, cell_format=hyperlink_format)

            num_rows = len(df_display.index)
            num_cols = len(df_display.columns)
            # 条件付き書式を適用する範囲 (ヘッダー行を除く全データ範囲)
            # A列から始まる全データ範囲
            apply_range = f'A2:{chr(ord("A") + num_cols - 1)}{num_rows + 1}'
            type_col_letter_display = chr(ord('A') + type_col_idx_display)

            # フォルダの条件付き書式
            worksheet.conditional_format(apply_range, {'type': 'formula',
                                          'criteria': f'=${type_col_letter_display}2="folder"',
                                          'format': folder_format})

            # ファイルの条件付き書式
            worksheet.conditional_format(apply_range,
                                         {'type': 'formula',
                                          'criteria': f'=${type_col_letter_display}2="file"',
                                          'format': file_format})
            
            # タイプ列を非表示にする場合 (オプション)
            # worksheet.set_column(type_col_idx, type_col_idx, None, None, {'hidden': True})
    except ImportError:
        logging.warning("`xlsxwriter` がインストールされていません。`pip install xlsxwriter` を実行してください。")
        logging.info("条件付き書式やハイパーリンクなしでExcelファイルを出力します。")
        df.drop(columns=['_item_self_path']).to_excel(excel_path, index=False) # 通常の出力
    except Exception as e:
        raise ScriptError(f"Excelファイル '{excel_path}' への保存中に予期せぬエラーが発生しました。") from e


def manage_old_output_files(output_dir: str, base_filename_config: str, current_timestamped_filename: str):
    """
    指定されたディレクトリ内の古い出力ファイル（タイムスタンプ付き）を検索し、
    ユーザーに確認の上で削除する。
    """
    if not os.path.isdir(output_dir):
        return

    base_name, ext = os.path.splitext(base_filename_config)
    # 古いファイルのパターン: base_name_YYYYMMDD_HHMMSS.ext
    # re.escapeでベース名に含まれる可能性のある正規表現特殊文字をエスケープ
    pattern_str = rf"^{re.escape(base_name)}_\d{{8}}_\d{{6}}{re.escape(ext)}$"
    pattern = re.compile(pattern_str)

    old_files_to_delete = []
    for f_name in os.listdir(output_dir):
        if pattern.match(f_name) and f_name != current_timestamped_filename:
            old_files_to_delete.append(os.path.join(output_dir, f_name))

    if old_files_to_delete:
        logging.info("\n古い出力ファイルが見つかりました:")
        for old_file in old_files_to_delete:
            print(f"  - {old_file}")
        
        confirm = input("これらの古いファイルを削除しますか？ (y/n): ").strip().lower()
        if confirm == 'y':
            for old_file in old_files_to_delete:
                try:
                    os.remove(old_file)
                    logging.info(f"削除しました: {old_file}")
                except OSError as e:
                    logging.warning(f"削除できませんでした: {old_file} ({e})")
        else:
            logging.info("古いファイルは保持されます。")

def ask_directory(initial_dir):
    """フォルダ選択ダイアログを表示し、選択されたパスを返す（キャンセル時は空文字）"""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # ランチャー経由でも背面に隠れないように
    try:
        return filedialog.askdirectory(
            title="スキャンするフォルダを選択してください",
            initialdir=initial_dir if os.path.isdir(initial_dir) else os.path.expanduser("~"),
        )
    finally:
        root.destroy()

def main():
    """スクリプトのメイン処理"""
    setup_logging() # ロギング設定を呼び出し
    try:
        logging.info("スクリプト実行開始")

        config_manager = ConfigManager(CONFIG_FILE_PATH)

        root_dir_path = ask_directory(config_manager.root_dir)
        if not root_dir_path:
            logging.info("フォルダが選択されなかったため、処理を中断します。")
            return
        if root_dir_path != config_manager.root_dir:
            config_manager.save_root_dir(root_dir_path)

        logging.info(f"スキャンを開始します: {root_dir_path}")
        excluded_exts = config_manager.get_excluded_extensions()
        excluded_folders = config_manager.get_excluded_folder_names()
        scanner = DirectoryScanner(root_dir_path, excluded_extensions=excluded_exts, excluded_folder_names=excluded_folders)
        file_data = scanner.scan()

        if file_data:
            file_data.sort(key=lambda item: item.full_path)
        
        if not file_data:
            # scanner.scan()内でroot_dirが存在しない場合は警告ログが出ている
            if os.path.isdir(root_dir_path): # root_dirは存在するがアイテムが0件
                 logging.info(f"指定されたフォルダ '{root_dir_path}' にスキャン対象アイテム（ファイルまたはフォルダ）が見つかりませんでした。")
            logging.info("処理を終了します。")
            return

        logging.info(f"{len(file_data)} 件のアイテム情報を取得しました。DataFrameを作成します...")
        df = create_dataframe_with_fullpath(file_data)
        
        if df.empty:
            logging.warning("DataFrameが空のため、Excelファイルは生成されません。")
            logging.info("処理を終了します。")
            return

        output_base_dir = config_manager.output_base_dir
        base_output_filename_from_config = config_manager.output_filename

        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        base_name, ext = os.path.splitext(base_output_filename_from_config)
        timestamped_output_filename = f"{base_name}_{timestamp}{ext}"

        if not os.path.exists(output_base_dir):
            logging.info(f"出力先フォルダ {output_base_dir} を作成します...")
            try:
                os.makedirs(output_base_dir, exist_ok=True)
            except OSError as e:
                raise ScriptError(f"出力先フォルダ '{output_base_dir}' の作成に失敗しました。") from e

        manage_old_output_files(output_base_dir, base_output_filename_from_config, timestamped_output_filename)
                
        output_excel_path = os.path.join(output_base_dir, timestamped_output_filename)

        logging.info(f"Excelファイルに出力します: {output_excel_path}")
        save_dataframe_to_excel(df, output_excel_path)
        if os.path.exists(output_excel_path):
             logging.info(f"フォルダ構造を出力しました: {output_excel_path}")

    except ConfigError as e:
        logging.critical(f"設定エラーが発生しました: {e}")
    except ScanError as e: # DirectoryScanner内で発生させる場合
        logging.critical(f"スキャンエラーが発生しました: {e}")
    except ScriptError as e: # save_dataframe_to_excel やその他の ScriptError
        logging.critical(f"スクリプト処理中にエラーが発生しました: {e}", exc_info=True)
    except Exception as e: # 予期せぬその他のエラー
        logging.critical(f"予期せぬエラーが発生しました。", exc_info=True)
    finally:
        logging.info("スクリプト実行終了")

if __name__ == "__main__":
    main()
