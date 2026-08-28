"""任意のダークテーマ／UIフォント／ボタン3段階スタイルの適用ヘルパー。

sv_ttk / pywinstyles が未インストールの環境では標準ttkテーマのまま正常動作する
（33_テキスト・CSV前処理サポート、81_open_shortcut と同じ任意依存パターン）。
81_open_shortcut/src/theme.py と同型。将来 00 と 33 で共通モジュール化する際の土台。
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

# 視認性の高いUIフォントに統一する（#160、81_open_shortcut #159 と同方針）。
# Meiryo UI は Windows 標準で必ず利用でき、かな・小書き文字が読みやすい。
# Yu Gothic UI より字面がやや大きいため、旧サイズから 1pt ずつ引き上げている。
UI_FONT_FAMILY = "Meiryo UI"
UI_FONT = (UI_FONT_FAMILY, 10)
UI_FONT_BOLD = (UI_FONT_FAMILY, 10, "bold")
HEADER_FONT = (UI_FONT_FAMILY, 12, "bold")   # カテゴリ見出し
TAG_FONT = (UI_FONT_FAMILY, 9)               # 種別タグ等の補足テキスト
PATH_FONT = (UI_FONT_FAMILY, 9)              # 相対パス表示

# テーマに依存させたくない固定色（補助テキスト・ステータス）
MUTED_FG = "#888888"
STATUS_FG = "#4a9eff"

# ボタン3段階の共通スタイル（全ボタンは必ずこの3種のどれかで生成する）
#   Primary   : サブウィンドウの主操作（保存して閉じる）。14pt bold・高さ42px
#   Secondary : ツール実行ボタン・キャンセル等の標準操作。11pt・高さ34px
#   Tertiary  : ★お気に入り・⚙設定・参照...等の補助操作。10pt・高さ28px・枠なし
BTN_PRIMARY = "Primary.Accent.TButton"
BTN_SECONDARY = "Secondary.TButton"
BTN_TERTIARY = "Tertiary.Toolbutton"
_BUTTON_SPECS = {
    BTN_PRIMARY:   {"font": (UI_FONT_FAMILY, 14, "bold"), "height": 42, "hpad": 20},
    BTN_SECONDARY: {"font": (UI_FONT_FAMILY, 11),         "height": 34, "hpad": 12},
    BTN_TERTIARY:  {"font": (UI_FONT_FAMILY, 10),         "height": 28, "hpad": 6},
}

_FONT_STYLES = ("TLabel", "TButton", "TCheckbutton", "TEntry", "TLabelframe")


def apply_theme(root):
    """sv_ttk dark（あれば）＋UIフォント＋ボタン3段階スタイルを適用し、ttk.Style を返す。

    フォント統一はテーマ適用後に行う（sv_ttk の上書きを防ぐため）。
    """
    if SV_TTK_AVAILABLE:
        _sv_ttk.set_theme("dark")
    style = ttk.Style(root)
    _apply_fonts(style)
    _apply_button_styles(style, root)
    return style


def _apply_fonts(style):
    # "." は個別指定しないウィジェットへのフォールバック（sv_ttk 有効時は Sun Valley 側が優先されるため標準ttk時のみ効く）
    style.configure(".", font=UI_FONT)
    for name in _FONT_STYLES:
        style.configure(name, font=UI_FONT)
    style.configure("TLabelframe.Label", font=UI_FONT_BOLD)  # ツール名見出し


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
