"""
SpiritByte - Background composition helpers.
"""

import flet as ft

from data.wallpaper_store import resolve_wallpaper_src

def _overlay_argb(alpha: float) -> str:
    alpha = max(0.0, min(1.0, alpha))
    value = int(round(alpha * 255))
    return f"#{value:02x}000000"

def build_wallpaper_background(
    content: ft.Control,
    wallpaper_src: str,
    fallback_color: str = "#0a0a0a",
    overlay_alpha: float = 0.5,
) -> ft.Control:
    """Wrap content with wallpaper + dark overlay if a valid source exists."""
    resolved_src = resolve_wallpaper_src(wallpaper_src)
    if not resolved_src:
        return ft.Container(expand=True, bgcolor=fallback_color, content=content)

    return ft.Container(
        expand=True,
        content=ft.Stack(
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    image=ft.DecorationImage(
                        src=resolved_src,
                        fit=ft.BoxFit.FILL,
                    ),
                ),
                ft.Container(expand=True, bgcolor=_overlay_argb(overlay_alpha)),
                content,
            ],
        ),
    )
