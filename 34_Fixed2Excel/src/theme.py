"""任意のダークテーマ／UIフォント／ボタン3段階スタイルの適用ヘルパー。

sv_ttk / pywinstyles が未インストールの環境では標準ttkテーマのまま正常動作する。
00_ランチャー/theme.py・81_open_shortcut/src/theme.py と同型（将来の共通モジュール化の土台）。
"""
import sys
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

# 視認性の高いUIフォントに統一する（#163、81_open_shortcut #159 と同方針）。
# Meiryo UI は Windows 標準で必ず利用でき、かな・小書き文字が読みやすい。
# Yu Gothic UI より字面がやや大きいため、旧サイズから 1pt 引き上げている。
UI_FONT_FAMILY = "Meiryo UI"
UI_FONT = (UI_FONT_FAMILY, 10)
UI_FONT_BOLD = (UI_FONT_FAMILY, 10, "bold")
HEADER_FONT = (UI_FONT_FAMILY, 12, "bold")
# ログ表示は等幅（全角=半角2倍幅を保証）。"MS ゴシック"（半角表記）は比例幅の
# "ＭＳ Ｐゴシック" に誤マッチするため、必ず全角表記で指定する。
LOG_FONT = ("ＭＳ ゴシック", 10)

# パレット（テーマに依存させたくない固定色）
MUTED_FG = "#888888"
ACCENT_FG = "#4a9eff"
SUCCESS_FG = "#4ec94e"
ERROR_FG = "#ff5555"
ERROR_SOFT_FG = "#ff7777"
WARN_FG = "#ffb347"

# Treeview 選択行（sv_ttk ダークの既定は低コントラストなため明示指定）
TREE_SELECT_BG = "#2f6fed"
TREE_SELECT_FG = "#ffffff"

# ログ欄の地色
LOG_BG = "#1e1e1e"
LOG_FG = "#e0e0e0"

# ボタン3段階の共通スタイル（全ボタンは必ずこの3種のどれかで生成する）
#   Primary   : 主操作（▶ 実行）。14pt bold・高さ42px
#   Secondary : 標準操作（設定を編集・開く・Stop 等）。11pt・高さ34px
#   Tertiary  : 補助操作（↻ 等）。10pt・高さ28px・枠なし
BTN_PRIMARY = "Primary.Accent.TButton"
BTN_SECONDARY = "Secondary.TButton"
BTN_TERTIARY = "Tertiary.Toolbutton"
_BUTTON_SPECS = {
    BTN_PRIMARY:   {"font": (UI_FONT_FAMILY, 14, "bold"), "height": 42, "hpad": 20},
    BTN_SECONDARY: {"font": (UI_FONT_FAMILY, 11),         "height": 34, "hpad": 12},
    BTN_TERTIARY:  {"font": (UI_FONT_FAMILY, 10),         "height": 28, "hpad": 6},
}

_FONT_STYLES = ("TLabel", "TButton", "TCheckbutton", "TEntry", "TLabelframe", "Treeview")


def apply_theme(root):
    """sv_ttk dark（あれば）＋UIフォント＋ボタン3段階スタイルを適用し、ttk.Style を返す。

    フォント統一はテーマ適用後に行う（sv_ttk の上書きを防ぐため）。
    """
    if SV_TTK_AVAILABLE:
        _sv_ttk.set_theme("dark")
    style = ttk.Style(root)
    _apply_fonts(style)
    style.map("Treeview",
              background=[("selected", TREE_SELECT_BG)],
              foreground=[("selected", TREE_SELECT_FG)])
    _apply_button_styles(style, root)
    return style


def _apply_fonts(style):
    style.configure(".", font=UI_FONT)  # 個別指定しないウィジェットへのフォールバック（標準ttk時のみ有効）
    for name in _FONT_STYLES:
        style.configure(name, font=UI_FONT)
    style.configure("TLabelframe.Label", font=UI_FONT_BOLD)


def _apply_button_styles(style, root):
    """ボタン3段階: 目標高さ(px)に合わせて縦paddingを実測較正する。

    フォント行高やテーマのchrome（枠線・フォーカスリング）はDPI・テーマ依存のため、
    padding=0 のプローブボタンで素の高さを測り、不足分を上下paddingに配分する。
    """
    for style_name, spec in _BUTTON_SPECS.items():
        style.configure(style_name, font=spec["font"], padding=(spec["hpad"], 0))
        probe = ttk.Button(root, text="あ", style=style_name)
        root.update_idletasks()
        base_h = probe.winfo_reqheight()
        probe.destroy()
        extra = max(0, spec["height"] - base_h)
        top, bottom = extra // 2, extra - extra // 2
        style.configure(style_name, padding=(spec["hpad"], top, spec["hpad"], bottom))
    style.configure(BTN_TERTIARY, foreground=MUTED_FG)


def style_titlebar(window):
    """タイトルバーをダークテーマに揃える（sv_ttk＋pywinstylesがあるときだけ。失敗しても無害）。
    Windows 11 はヘッダー色の直接指定、Windows 10 はダークスタイル適用＋再描画ハックで対応する。"""
    if not (SV_TTK_AVAILABLE and PYWINSTYLES_AVAILABLE):
        return
    try:
        version = sys.getwindowsversion()
        if version.major == 10 and version.build >= 22000:   # Windows 11
            _pywinstyles.change_header_color(window, "#1c1c1c")
        elif version.major == 10:                            # Windows 10
            _pywinstyles.apply_style(window, "dark")
            window.wm_attributes("-alpha", 0.99)              # 色が即時反映されないための再描画ハック
            window.wm_attributes("-alpha", 1)
    except Exception:
        pass
