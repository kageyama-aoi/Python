"""任意のダークテーマ適用ヘルパー。

sv_ttk / pywinstyles が未インストールの環境では何もせず、標準ttkテーマで
正常動作する（00_ランチャー、33_テキスト・CSV前処理サポートと同じ任意依存パターン）。
"""
import sys
import tkinter as tk
from tkinter import ttk

try:
    import sv_ttk as _sv_ttk
    SV_TTK_AVAILABLE = True
except ImportError:
    SV_TTK_AVAILABLE = False

try:
    import pywinstyles as _pywinstyles
    PYWINSTYLES_AVAILABLE = True
except ImportError:
    PYWINSTYLES_AVAILABLE = False


# sv_ttk dark のほぼ純黒(#1c1c1c)だとダークエディタと同化して見づらいため、
# わずかに青みグレー寄りのダークサーフェス色へ寄せる（#157）。
DARK_SURFACE = "#23272e"

# 視認性の高いUIフォント（#159）。Meiryo UI は Windows 標準で必ず利用でき、
# かな・小書き文字が読みやすい。未インストール環境向けに代替も並べる。
UI_FONT_FAMILY = "Meiryo UI"
UI_FONT = (UI_FONT_FAMILY, 11)
SMALL_FONT = (UI_FONT_FAMILY, 10)
HEADER_FONT = (UI_FONT_FAMILY, 13, "bold")

# UI_FONT を適用する ttk スタイル（config.json の styles 指定があればそちらが優先）。
_FONT_STYLES = (
    "TButton",
    "TLabel",
    "TEntry",
    "TCombobox",
    "TCheckbutton",
    "TRadiobutton",
    "TNotebook.Tab",
    "Treeview",
    "TLabelframe.Label",
)

# この背景を適用する ttk スタイル。入力欄（Entry/Combobox/Listbox）はあえて
# 従来の暗色のままにし、フィールドが軽く沈んで見えるようにする。
_SURFACE_STYLES = (
    "TFrame",
    "TLabel",
    "TLabelframe",
    "TLabelframe.Label",
    "TNotebook",
    "TPanedwindow",
    "TCheckbutton",
    "TRadiobutton",
    "Treeview",
    "Header.TLabel",
    "Status.TLabel",
)


def apply_dark_theme(root=None):
    """ダークテーマとUIフォントを適用する。

    sv_ttk があればダークテーマ＋背景色調整を行う。無ければ標準ttkテーマのまま。
    UIフォント（Meiryo UI）は sv_ttk の有無にかかわらず適用する。
    """
    if SV_TTK_AVAILABLE:
        _sv_ttk.set_theme("dark")
        _tint_surfaces()
    _apply_ui_font(root)


def _tint_surfaces():
    """sv_ttk dark の背景を DARK_SURFACE へ寄せる（sv_ttk 適用後に呼ぶ）。"""
    style = ttk.Style()
    for name in _SURFACE_STYLES:
        style.configure(name, background=DARK_SURFACE)


def _apply_ui_font(root=None):
    """UI_FONT を ttk 各スタイルと Listbox へ適用する（テーマ適用後に呼ぶ）。"""
    style = ttk.Style()
    style.configure(".", font=UI_FONT)
    for name in _FONT_STYLES:
        style.configure(name, font=UI_FONT)
    style.configure("Header.TLabel", font=HEADER_FONT)
    style.configure("Status.TLabel", font=SMALL_FONT)

    target = root or getattr(tk, "_default_root", None)
    if target is not None:
        try:
            target.option_add("*Listbox.font", UI_FONT)
        except tk.TclError:
            pass


def style_titlebar(window):
    """タイトルバーをダークテーマに揃える（sv_ttk＋pywinstylesがあるときだけ。失敗しても無害）。
    Windows 11 はヘッダー色の直接指定、Windows 10 はダークスタイル適用＋再描画ハックで対応する。"""
    if not SV_TTK_AVAILABLE:
        return

    # ウィンドウ地の色も DARK_SURFACE に合わせる（ttkウィジェットの隙間対策）。
    try:
        window.configure(background=DARK_SURFACE)
    except Exception:
        pass

    if not PYWINSTYLES_AVAILABLE:
        return
    if window.state() == "withdrawn":
        # withdraw()されたウィンドウ（テスト実行時など）にpywinstylesを適用すると
        # Tclのafter()タイマーが不安定になる現象を確認したため、非表示中はスキップする。
        return
    try:
        version = sys.getwindowsversion()
        if version.major == 10 and version.build >= 22000:   # Windows 11
            _pywinstyles.change_header_color(window, DARK_SURFACE)
        elif version.major == 10:                            # Windows 10
            _pywinstyles.apply_style(window, "dark")
            window.wm_attributes("-alpha", 0.99)              # 色が即時反映されないための再描画ハック
            window.wm_attributes("-alpha", 1)
    except Exception:
        pass
