"""設定編集ウィンドウのUIと操作を提供するモジュール。

タブごとの実装は以下に分割している:
- settings_tab.py : 基本設定タブ（ウィンドウ設定・遷移先・ページ順同期）
- pages_tab.py    : ページ編集タブ（一覧・並べ替え・表示/非表示）
- button_form.py  : ボタン設定フォーム（右ペイン・パラメータ編集）
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
import copy

from . import constants as C
from . import theme
from .config_manager import ConfigManager
from .settings_tab import SettingsTabMixin
from .pages_tab import PagesTabMixin
from .button_form import ButtonFormMixin


class SettingsEditor(SettingsTabMixin, PagesTabMixin, ButtonFormMixin, tk.Toplevel):
    """設定ファイル編集用のGUIを提供するウィンドウ。"""
    SETTING_LABELS = {
        "window_title": "ウィンドウタイトル",
        "geometry": "ウィンドウサイズ",
        "resizable": "サイズ変更可否",
        "icon_folder": "アイコンフォルダ",
        "window_icon": "ウィンドウアイコン",
        "default_button_icon": "デフォルトボタンアイコン",
        "initial_page": "起動時のページ",
        "menu_order": "メニュー表示順",
    }
    MENU_ORDER_DISPLAY_TO_VALUE = {
        "通常": "normal",
        "逆順": "reverse",
        "全体設定に従う": "global",
    }
    MENU_ORDER_VALUE_TO_DISPLAY = {
        value: key for key, value in MENU_ORDER_DISPLAY_TO_VALUE.items()
    }

    def __init__(self, master, config_manager: ConfigManager, on_save_callback=None):
        """設定編集ウィンドウを初期化し、初期フォームを構築する。"""
        super().__init__(master)
        self.title("設定エディタ")
        theme.style_titlebar(self)
        self.config_manager = config_manager
        self.on_save_callback = on_save_callback
        self.geometry("900x640")
        self.minsize(740, 620)

        # 編集用の一時的なconfigのコピーを作成
        self.config = copy.deepcopy(self.config_manager.get_config())

        self.current_parameters = []
        self.create_widgets()

    def _format_setting_label(self, key: str) -> str:
        """設定キーを「日本語（英語）」形式のラベルへ変換する。"""
        key_value = key.value if hasattr(key, "value") else key
        ja = self.SETTING_LABELS.get(key_value, key_value)
        return f"{ja} ({key_value})"

    def _format_page_tab_label(self, page_name: str, page_data: dict) -> str:
        """ページタブを「日本語（英語）」形式で表示する。"""
        title = page_data.get(C.ConfigKey.TITLE, page_name)
        # 日本語タイトル内の英語補足（例: [Tframe], (memo)）を除去して重複表記を防ぐ
        cleaned_title = re.sub(r"\s*[\[\(（]\s*[A-Za-z0-9_\- ]+\s*[\]\)）]\s*", "", str(title)).strip()
        if not cleaned_title:
            cleaned_title = page_name
        return f"{cleaned_title} ({page_name})"

    def _build_page_selector_maps(self):
        """ページ選択用の表示名<->IDマップを構築する。"""
        self.page_display_to_id = {}
        self.page_id_to_display = {}
        pages = self.config.get(C.ConfigKey.PAGES, {})
        for page_name, page_data in pages.items():
            display_label = self._format_page_tab_label(page_name, page_data)
            self.page_display_to_id[display_label] = page_name
            self.page_id_to_display[page_name] = display_label

    def create_widgets(self):
        """ウィンドウ全体のレイアウトとタブを構築する。"""
        self._build_page_selector_maps()
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # 下部の操作領域（保存ボタン・ステータス）を Notebook より先に確保する。
        # Notebook を先に pack すると「基本設定」タブの要求高さが大きく、
        # ウィンドウが小さいときに最後の保存ボタンが数pxまで潰れてしまうため（#148）。
        # 保存ボタン（sv_ttk導入時はAccentスタイルで強調。未導入なら通常ボタンにフォールバック）
        save_button = ttk.Button(
            main_frame, text="保存して閉じる", command=self.save_config, style="Accent.TButton"
        )
        save_button.pack(side="bottom", pady=10)

        # 操作結果を非モーダルで表示するステータス
        self.status_var = tk.StringVar(value="準備完了")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(side="bottom", fill="x", pady=(8, 0))

        # Notebook (タブ) — 残りの領域を埋める
        notebook = ttk.Notebook(main_frame)
        notebook.pack(side="top", fill="both", expand=True)

        # ページ編集タブ
        pages_tab = ttk.Frame(notebook)
        notebook.add(pages_tab, text="ページ編集")
        self.create_pages_tab(pages_tab)

        # 設定タブ
        settings_tab = ttk.Frame(notebook)
        notebook.add(settings_tab, text="基本設定")
        self.create_settings_tab(settings_tab)

    def _set_status(self, message: str):
        """設定画面下部のステータスを更新する。"""
        if hasattr(self, "status_var"):
            self.status_var.set(message)

    def save_config(self):
        """編集内容を検証して設定ファイルへ保存する。"""
        # settingsの保存
        settings = self.config.get(C.ConfigKey.SETTINGS, {})
        for key, var in self.settings_vars.items():
            value = var.get()
            if key == C.ConfigKey.RESIZABLE:
                try:
                    # 'True, False' のような文字列を [True, False] のようなリストに変換
                    settings[key] = [
                        v.strip().lower() in ('true', '1', 't', 'y', 'yes')
                        for v in value.split(',')
                    ]
                except Exception as e:
                    messagebox.showerror("入力エラー", f"'{C.ConfigKey.RESIZABLE}' の値は 'True, False' のようにカンマ区切りの真偽値で入力してください。\nエラー: {e}")
                    return
            elif key == C.ConfigKey.MENU_ORDER:
                normalized_value = self.MENU_ORDER_DISPLAY_TO_VALUE.get(value, value)
                if normalized_value not in ("normal", "reverse"):
                    messagebox.showerror("入力エラー", f"'{C.ConfigKey.MENU_ORDER}' は 通常 または 逆順 を選択してください。")
                    return
                settings[key] = normalized_value
            elif key == C.ConfigKey.INITIAL_PAGE:
                page_names = set(self.config.get(C.ConfigKey.PAGES, {}).keys())
                normalized_value = self.page_display_to_id.get(value, value)
                if normalized_value not in page_names:
                    messagebox.showerror("入力エラー", f"'{C.ConfigKey.INITIAL_PAGE}' は既存ページから選択してください。")
                    return
                settings[key] = normalized_value
            else:
                settings[key] = value
        self.config[C.ConfigKey.SETTINGS] = settings

        # show_page の遷移先保存
        if hasattr(self, "transition_target_rows"):
            page_names = set(self.config.get(C.ConfigKey.PAGES, {}).keys())
            for row in self.transition_target_rows:
                target_display_or_id = row["target_var"].get()
                target_id = self.page_display_to_id.get(target_display_or_id, target_display_or_id)
                if target_id not in page_names:
                    messagebox.showerror("入力エラー", f"遷移先 '{target_display_or_id}' は既存ページから選択してください。")
                    return
                entry_ref = row.get("entry_ref")
                if entry_ref is not None:
                    entry_ref[C.ConfigKey.TARGET] = target_id

            # 遷移先変更をページ順へ反映してから保存する
            self._recompute_page_order_from_transitions()

        # ページ順の保存（dictの挿入順で保持）
        pages = self.config.get(C.ConfigKey.PAGES, {})
        ordered_page_ids = self._get_page_order_ids()
        reordered_pages = {}
        for page_id in ordered_page_ids:
            if page_id in pages:
                reordered_pages[page_id] = pages[page_id]
        for page_id, page_data in pages.items():
            if page_id not in reordered_pages:
                reordered_pages[page_id] = page_data
        self.config[C.ConfigKey.PAGES] = reordered_pages

        # pagesのmenu_order保存（globalは未設定として扱う）
        for page_name, var in self.page_menu_order_vars.items():
            display_value = var.get()
            value = self.MENU_ORDER_DISPLAY_TO_VALUE.get(display_value, display_value)
            if value not in ("global", "normal", "reverse"):
                messagebox.showerror("入力エラー", f"ページ '{page_name}' の表示順は 全体設定に従う / 通常 / 逆順 のいずれかを選択してください。")
                return

            page_data = self.config.get(C.ConfigKey.PAGES, {}).get(page_name)
            if not page_data:
                continue

            if value == "global":
                page_data.pop(C.ConfigKey.MENU_ORDER, None)
            else:
                page_data[C.ConfigKey.MENU_ORDER] = value

        # 新しい設定をConfigManager経由で保存
        if self.config_manager.save_config(self.config):
            messagebox.showinfo("成功", "設定を保存しました。")
            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()
        else:
            # 保存失敗のメッセージはConfigManagerが表示するのでここでは不要
            pass
