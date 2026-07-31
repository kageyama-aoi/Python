"""任意のダークテーマ適用ヘルパー。

sv_ttk / pywinstyles が未インストールの環境では何もせず、標準ttkテーマで
正常動作する（00_ランチャー、33_テキスト・CSV前処理サポートと同じ任意依存パターン）。
"""
import sys

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


def apply_dark_theme():
    """sv_ttkが利用可能ならダークテーマを適用する。未導入なら何もしない。"""
    if SV_TTK_AVAILABLE:
        _sv_ttk.set_theme("dark")


def style_titlebar(window):
    """タイトルバーをダークテーマに揃える（sv_ttk＋pywinstylesがあるときだけ。失敗しても無害）。
    Windows 11 はヘッダー色の直接指定、Windows 10 はダークスタイル適用＋再描画ハックで対応する。"""
    if not (SV_TTK_AVAILABLE and PYWINSTYLES_AVAILABLE):
        return
    if window.state() == "withdrawn":
        # withdraw()されたウィンドウ（テスト実行時など）にpywinstylesを適用すると
        # Tclのafter()タイマーが不安定になる現象を確認したため、非表示中はスキップする。
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
