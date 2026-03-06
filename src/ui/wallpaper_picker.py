"""
SpiritByte - Wallpaper settings dialog.
Allows choosing static (PNG/JPG) and animated (GIF) backgrounds
for the main UI and lock screen.
"""

from typing import Callable

import flet as ft

from data.settings import Settings, get_accent, get_text_main, get_text_sec, get_bg_opacity
from data.wallpaper_store import (
    SUPPORTED_WALLPAPER_EXTENSIONS,
    import_wallpaper_to_assets,
    remove_imported_wallpaper,
    resolve_wallpaper_src,
)

_BG = "#0a0a0a"
_SURFACE = "#1a1a1a"
_BORDER = "#333333"
_DANGER = "#ff4444"

def show_wallpaper_picker_dialog(
    page: ft.Page,
    on_apply: Callable[[], None] | None = None,
) -> None:
    """Open wallpaper settings modal for app and lock backgrounds."""
    settings = Settings.get_instance()
    state = {
        "app": settings.app_background,
        "lock": settings.lock_background,
        "changed": False,
        "bg_opacity": get_bg_opacity(),
    }

    app_file_text = ft.Text(size=11, color=get_text_sec())
    lock_file_text = ft.Text(size=11, color=get_text_sec())
    error_text = ft.Text(size=11, color=_DANGER, visible=False)

    app_preview = ft.Container(width=120, height=70, border=ft.Border.all(1, _BORDER))
    lock_preview = ft.Container(width=120, height=70, border=ft.Border.all(1, _BORDER))

    def _pretty_name(src: str) -> str:
        resolved = resolve_wallpaper_src(src)
        if not resolved:
            return "No background selected"
        return resolved.split("/")[-1]

    def _build_preview(src: str) -> ft.Control:
        resolved = resolve_wallpaper_src(src)
        if not resolved:
            return ft.Container(
                expand=True,
                bgcolor="#101010",
                alignment=ft.Alignment(0, 0),
                content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED, size=20, color=get_text_sec()),
            )
        if resolved.lower().endswith(".gif"):
            return ft.Container(
                expand=True,
                bgcolor="#101010",
                alignment=ft.Alignment(0, 0),
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.MOVIE_FILTER_OUTLINED, size=18, color=get_text_sec()),
                        ft.Text("GIF selected", size=10, color=get_text_sec()),
                    ],
                    spacing=4,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    tight=True,
                ),
            )
        return ft.Image(
            src=resolved,
            fit=ft.BoxFit.COVER,
            expand=True,
            gapless_playback=False,
        )

    def _refresh_ui():
        app_preview.content = _build_preview(state["app"])
        lock_preview.content = _build_preview(state["lock"])
        app_file_text.value = _pretty_name(state["app"])
        lock_file_text.value = _pretty_name(state["lock"])
        page.update()

    def _apply_slot(slot: str, imported_src: str):
        old_src = state[slot]
        state[slot] = imported_src
        state["changed"] = True

        if slot == "app":
            settings.app_background = imported_src
        else:
            settings.lock_background = imported_src

        if old_src and old_src != imported_src:
            remove_imported_wallpaper(old_src)

        error_text.visible = False
        _refresh_ui()

    def _clear_slot(slot: str):
        old_src = state[slot]
        state[slot] = ""
        state["changed"] = True

        if slot == "app":
            settings.app_background = ""
        else:
            settings.lock_background = ""

        if old_src:
            remove_imported_wallpaper(old_src)

        error_text.visible = False
        _refresh_ui()

    async def _pick_for(slot: str):
        try:
            files = await picker.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=SUPPORTED_WALLPAPER_EXTENSIONS,
                dialog_title="Select wallpaper (PNG/JPG/GIF)",
            )
        except Exception as ex:
            error_text.value = str(ex)
            error_text.visible = True
            page.update()
            return

        if not files:
            return

        picked_path = files[0].path
        if not picked_path:
            return

        try:
            imported_src = import_wallpaper_to_assets(picked_path, slot)
            _apply_slot(slot, imported_src)
        except ValueError as ex:
            error_text.value = str(ex)
            error_text.visible = True
            page.update()

    async def _close(_=None):
        dialog.open = False
        if picker in page.services:
            page.services.remove(picker)
        page.update()

    async def _apply_and_close(_=None):
        await _close()
        if state.get("changed") and on_apply:
            Settings.get_instance().bg_opacity = state["bg_opacity"]
            on_apply()
            state["changed"] = False

    picker = ft.FilePicker()
    page.services.append(picker)

    app_section = ft.Container(
        bgcolor=_SURFACE,
        border=ft.Border.all(1, _BORDER),
        border_radius=8,
        padding=10,
        content=ft.Column(
            controls=[
                ft.Text("General Interface", size=12, weight=ft.FontWeight.BOLD, color=get_text_main()),
                ft.Text("Applies to main vault screen", size=11, color=get_text_sec()),
                ft.Row(
                    controls=[
                        app_preview,
                        ft.Column(
                            controls=[
                                app_file_text,
                                ft.Row(
                                    controls=[
                                        ft.Button(
                                            content=ft.Text("Choose", size=11, color=get_text_main()),
                                            bgcolor=get_accent(),
                                            height=30,
                                            on_click=lambda _: page.run_task(_pick_for, "app"),
                                        ),
                                        ft.Button(
                                            content=ft.Text("Clear", size=11, color=get_text_main()),
                                            bgcolor="#2a2a2a",
                                            height=30,
                                            on_click=lambda _: _clear_slot("app"),
                                        ),
                                    ],
                                    spacing=6,
                                ),
                            ],
                            spacing=6,
                            expand=True,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=6,
            tight=True,
        ),
    )

    lock_section = ft.Container(
        bgcolor=_SURFACE,
        border=ft.Border.all(1, _BORDER),
        border_radius=8,
        padding=10,
        content=ft.Column(
            controls=[
                ft.Text("Lock Screen", size=12, weight=ft.FontWeight.BOLD, color=get_text_main()),
                ft.Text("Applies to master password screen", size=11, color=get_text_sec()),
                ft.Row(
                    controls=[
                        lock_preview,
                        ft.Column(
                            controls=[
                                lock_file_text,
                                ft.Row(
                                    controls=[
                                        ft.Button(
                                            content=ft.Text("Choose", size=11, color=get_text_main()),
                                            bgcolor=get_accent(),
                                            height=30,
                                            on_click=lambda _: page.run_task(_pick_for, "lock"),
                                        ),
                                        ft.Button(
                                            content=ft.Text("Clear", size=11, color=get_text_main()),
                                            bgcolor="#2a2a2a",
                                            height=30,
                                            on_click=lambda _: _clear_slot("lock"),
                                        ),
                                    ],
                                    spacing=6,
                                ),
                            ],
                            spacing=6,
                            expand=True,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            spacing=6,
            tight=True,
        ),
    )

    def _on_opacity_change(e):
        state["bg_opacity"] = e.control.value
        state["changed"] = True
        opacity_text.value = f"{int(e.control.value * 100)}%"
        page.update()

    opacity_slider = ft.Slider(
        min=0.0,
        max=1.0,
        divisions=20,
        value=state["bg_opacity"],
        active_color=get_accent(),
        inactive_color=_BORDER,
        on_change=_on_opacity_change,
        expand=True,
    )
    opacity_text = ft.Text(f"{int(state['bg_opacity'] * 100)}%", size=11, color=get_text_sec(), width=35)

    opacity_section = ft.Container(
        padding=10,
        content=ft.Column(
            controls=[
                ft.Text("Background Overlay", size=12, weight=ft.FontWeight.BOLD, color=get_text_main()),
                ft.Text("Darken the wallpaper to make text readable", size=11, color=get_text_sec()),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.BRIGHTNESS_LOW_OUTLINED, size=16, color=get_text_sec()),
                        opacity_slider,
                        opacity_text,
                    ],
                ),
            ],
            spacing=4,
        ),
        bgcolor="#111111", border_radius=6,
    )

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=_BG,
        title=ft.Row(
            controls=[
                ft.Icon(ft.Icons.WALLPAPER_OUTLINED, size=20, color=get_accent()),
                ft.Text("Wallpaper Settings", size=16, color=get_accent(), weight=ft.FontWeight.BOLD),
            ],
            spacing=8,
        ),
        content=ft.Column(
            controls=[
                ft.Text("Supported formats: PNG, JPG, JPEG, GIF", size=11, color=get_text_sec()),
                ft.Text("Select files, then press Apply.", size=10, color=get_text_sec()),
                app_section,
                lock_section,
                opacity_section,
                error_text,
            ],
            spacing=8,
            tight=True,
            width=500,
        ),
        actions=[
            ft.TextButton(content=ft.Text("Close", color=get_text_main()), on_click=_close),
            ft.Button(
                content=ft.Text("Apply", color=get_text_main(), weight=ft.FontWeight.W_500),
                bgcolor=get_accent(),
                height=34,
                on_click=_apply_and_close,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    _refresh_ui()
