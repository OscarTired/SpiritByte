"""
SpiritByte – Accent colour picker dialog.
Shows preset swatches + hex input. Calls *on_apply(colour)* when confirmed.
"""
import re
import flet as ft
from typing import Callable

from data.settings import Settings, get_accent, get_text_main, get_text_sec

_BG = "#0a0a0a"
_SURFACE = "#1a1a1a"
_BORDER = "#333333"
_DANGER = "#ff4444"

_DEFAULT_ACCENT = "#ff6b6b"
_DEFAULT_TEXT_MAIN = "#ffffff"
_DEFAULT_TEXT_SEC = "#888888"

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")
_PRESETS = ["#4a9eff", "#34a85a", "#ff9800", "#ff3737", "#8e24aa", "#3f51b5"]

def show_color_picker_dialog(
    page: ft.Page,
    on_apply: Callable[[str, str, str], None],
) -> None:
    """Modal dialog: preset colour grid + hex input + live preview."""
    accent = get_accent()
    text_main = get_text_main()
    text_sec = get_text_sec()

    preview_box = ft.Container(
        width=34, height=34, bgcolor=accent, border_radius=4,
        border=ft.Border.all(1, _BORDER)
    )

    hex_input = ft.TextField(
        value=accent,
        width=130, height=38, text_size=13,
        border_color=_BORDER, focused_border_color=accent,
        cursor_color=accent,
        text_style=ft.TextStyle(color=get_text_main(), font_family="Consolas"),
        hint_style=ft.TextStyle(color=get_text_sec()),
        on_change=lambda e: _on_hex_change(e),
    )

    tab_state = {"index": 0}

    def _get_active_color_key():
        if tab_state["index"] == 0: return "accent"
        if tab_state["index"] == 1: return "text_main"
        return "text_sec"

    def _update_preview():
        key = _get_active_color_key()
        c = state[key]
        preview_box.bgcolor = c if _HEX_RE.match(c) else _BG
        hex_input.value = c
        _rebuild_swatches()
        _rebuild_tabs()
        page.update()

    def _on_tab_change(index: int):
        tab_state["index"] = index
        _update_preview()

    tabs_row = ft.Row(spacing=8, alignment=ft.MainAxisAlignment.CENTER)

    def _rebuild_tabs():
        tabs_row.controls.clear()
        labels = [
            ("Accent", ft.Icons.PALETTE_OUTLINED),
            ("Main Text", ft.Icons.TITLE_OUTLINED),
            ("Sec Text", ft.Icons.SUBTITLES_OUTLINED),
        ]
        for i, (text, icon) in enumerate(labels):
            is_active = (i == tab_state["index"])
            tabs_row.controls.append(
                ft.Container(
                    content=ft.Row([ft.Icon(icon, size=14, color=get_text_main() if is_active else get_text_sec()), 
                                    ft.Text(text, size=12, color=get_text_main() if is_active else get_text_sec())], 
                                   spacing=4),
                    padding=ft.Padding(12, 6, 12, 6),
                    bgcolor=_SURFACE if is_active else "transparent",
                    border=ft.Border.all(1, _BORDER) if is_active else None,
                    border_radius=16,
                    on_click=lambda _, idx=i: _on_tab_change(idx),
                    ink=True,
                )
            )

    _rebuild_tabs()

    state = {
        "accent": accent,
        "text_main": text_main,
        "text_sec": text_sec,
    }

    error_text = ft.Text(value="", color=_DANGER, size=11, visible=False)

    def _on_hex_change(e):
        val = e.control.value or ""
        state[_get_active_color_key()] = val.strip()
        if _HEX_RE.match(val.strip()):
            preview_box.bgcolor = val.strip()
            error_text.visible = False
            _rebuild_swatches()
        else:
            preview_box.bgcolor = _BG
        page.update()

    def _select(c: str):
        state[_get_active_color_key()] = c
        _update_preview()

    swatch_wrap = ft.Row(wrap=True, spacing=8, run_spacing=8)

    def _rebuild_swatches():
        swatch_wrap.controls.clear()
        active_c = state[_get_active_color_key()]
        for c in _PRESETS:
            is_sel = (c.lower() == active_c.lower())
            swatch_wrap.controls.append(
                ft.Container(
                    width=36, height=36,
                    bgcolor=c,
                    border_radius=8,
                    border=ft.Border.all(2.5, get_text_main()) if is_sel else ft.Border.all(1, _BORDER),
                    on_click=lambda _, clr=c: _select(clr),
                    ink=True,
                    animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
                )
            )

    _rebuild_swatches()

    def _on_reset(_):
        state["accent"] = _DEFAULT_ACCENT
        state["text_main"] = _DEFAULT_TEXT_MAIN
        state["text_sec"] = _DEFAULT_TEXT_SEC
        _update_preview()

    async def _close(_=None):
        dialog.open = False
        page.update()

    async def _handle_apply(_):
        for k in ["accent", "text_main", "text_sec"]:
            if not _HEX_RE.match(state[k]):
                error_text.value = f"Invalid hex colour in {k}"
                error_text.visible = True
                page.update()
                return

        Settings.get_instance().save_colors(state["accent"], state["text_main"], state["text_sec"])
        
        dialog.open = False
        page.update()
        on_apply(state["accent"], state["text_main"], state["text_sec"])

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=_BG,
        title=ft.Row(
            controls=[
                ft.Icon(ft.Icons.PALETTE_OUTLINED, size=20, color=get_accent()),
                ft.Text("Theme Colours", size=16, weight=ft.FontWeight.BOLD, color=get_accent()),
            ],
            spacing=8,
        ),
        content=ft.Container(
            width=320,
            content=ft.Column(
                controls=[
                    tabs_row,
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            hex_input,
                            preview_box,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=4),
                    swatch_wrap,
                    error_text,
                ],
                spacing=6,
                tight=True,
            ),
        ),
        actions=[
            ft.TextButton(content=ft.Text("Reset", color=get_text_sec()), on_click=_on_reset),
            ft.TextButton(content=ft.Text("Close", color=get_text_main()), on_click=_close),
            ft.Button(
                content=ft.Text("Apply", color=get_text_main(), weight=ft.FontWeight.W_500),
                bgcolor=get_accent(), width=100, height=36, on_click=_handle_apply,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()
