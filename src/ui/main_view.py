"""
SpiritByte - Main View
Password vault interface with sidebar, entry list, and detail panel.
All event handlers are async. UI updates are batched (single page.update per action).
"""
import asyncio
import flet as ft
import os
from typing import Optional

from app_state import state
from core.security import SecurityManager
from data.settings import Settings, get_accent, get_text_main, get_text_sec, get_bg_opacity
from data.vault import VaultManager, VIRTUAL_CATEGORIES
from data.wallpaper_store import resolve_wallpaper_src
from ui.clipboard_service import ClipboardService
from ui.color_picker import show_color_picker_dialog
from ui.vault_dialogs import (
    resolve_category_icon,
    show_add_edit_dialog,
    show_category_icon_picker_dialog,
    show_delete_dialog,
    show_delete_category_dialog,
)
from ui.wallpaper_picker import show_wallpaper_picker_dialog

_BG = "#0a0a0a"
_SURFACE = "#1a1a1a"
_BORDER = "#333333"
_DANGER = "#ff4444"

class MainView(ft.Container):
    """Main application view with sidebar and password vault."""

    def __init__(self, page: ft.Page, security: SecurityManager):
        super().__init__(expand=True, bgcolor=_BG)

        self._page = page
        self._security = security

        app_data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "app_data",
        )
        vault_path = os.path.join(app_data_dir, "vault.dat")
        self._vault = VaultManager(security, vault_path)
        self._vault.load()

        self._clip = ClipboardService(page)

        self._selected_category = "All"
        self._selected_entry_id: Optional[str] = None
        self._search_query = ""
        self._password_visible = False
        self._password_hide_task: Optional[asyncio.Task] = None

        self._main_stack: ft.Stack = None
        self._build()

    def _build(self):
        self._category_column = ft.Column(spacing=2)
        self._build_categories()

        sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Image(
                                    src="images/SpireByte.png",
                                    width=20,
                                    height=20,
                                    fit=ft.BoxFit.CONTAIN,
                                ),
                                ft.Text("SpiritByte", size=16,
                                        weight=ft.FontWeight.BOLD, color=get_text_main()),
                            ],
                            spacing=8,
                        ),
                        padding=ft.Padding(left=16, right=16, top=20, bottom=16),
                    ),
                    ft.Container(
                        content=self._category_column,
                        expand=True,
                        padding=ft.Padding(left=8, right=8, top=0, bottom=0),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Button(
                                    content=ft.Row(
                                        controls=[
                                            ft.Icon(ft.Icons.ADD, size=14, color=get_text_main()),
                                            ft.Text("Add Entry", size=12, color=get_text_main()),
                                        ],
                                        spacing=6,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                    bgcolor=get_accent(), width=180, height=36,
                                    on_click=self._on_add_entry,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.TextButton(
                                            content=ft.Row(
                                                controls=[
                                                    ft.Icon(ft.Icons.LOCK_OUTLINE, size=14,
                                                            color=get_text_sec()),
                                                    ft.Text("Lock", size=12, color=get_text_sec()),
                                                ],
                                                spacing=6,
                                            ),
                                            on_click=self._on_lock,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.WALLPAPER_OUTLINED,
                                            icon_size=16,
                                            icon_color=get_text_sec(),
                                            tooltip="Wallpaper",
                                            on_click=self._on_open_wallpaper_picker,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.PALETTE_OUTLINED,
                                            icon_size=16,
                                            icon_color=get_text_sec(),
                                            tooltip="Theme Colours",
                                            on_click=self._on_open_color_picker,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=0,
                                ),
                            ],
                            spacing=4,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.Padding(left=8, right=8, top=8, bottom=16),
                    ),
                ],
            ),
            width=210,
            bgcolor="#88111111",
            border=ft.Border(right=ft.BorderSide(1, "#222222")),
        )

        self._search_field = ft.TextField(
            hint_text="Search...",
            prefix_icon=ft.Icons.SEARCH,
            width=300, height=38, text_size=13,
            border_color=_BORDER, focused_border_color=get_accent(), cursor_color=get_accent(),
            text_style=ft.TextStyle(color=get_text_main()),
            hint_style=ft.TextStyle(color=get_text_sec()),
            on_submit=self._on_search_change,
            on_change=self._on_search_clear,
        )
        self._count_label = ft.Text("", size=11, color=get_text_sec())

        search_bar = ft.Container(
            content=ft.Row(
                controls=[self._search_field, self._count_label],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=16, right=16, top=12, bottom=8),
        )

        self._entry_list = ft.ListView(spacing=2, expand=True, item_extent=52)
        self._detail_panel = ft.Container(expand=True)
        self._feedback_text = ft.Text("", size=11, color=get_accent())

        content_area = ft.Column(
            controls=[
                search_bar,
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=self._entry_list, width=320,
                                alignment=ft.Alignment(0, -1),
                                border=ft.Border(right=ft.BorderSide(1, "#222222")),
                                padding=ft.Padding(left=8, right=8, top=0, bottom=0),
                            ),
                            ft.Container(
                                content=ft.Column(
                                    controls=[self._detail_panel, self._feedback_text],
                                    spacing=8,
                                ),
                                expand=True,
                                padding=ft.Padding(left=20, right=20, top=8, bottom=8),
                            ),
                        ],
                        expand=True, spacing=0,
                    ),
                    expand=True,
                ),
            ],
            expand=True, spacing=0,
        )

        base_content = ft.Row(
            controls=[sidebar, ft.Container(content=content_area, expand=True)],
            expand=True, spacing=0,
        )

        if self._main_stack is None:
            resolved = resolve_wallpaper_src(Settings.get_instance().app_background)
            self._wallpaper_img = ft.Container(
                expand=True,
                image=ft.DecorationImage(
                    src=resolved or "",
                    fit=ft.BoxFit.FILL,
                ),
                visible=bool(resolved),
            )
            self._bg_overlay = ft.Container(
                expand=True, bgcolor="#000000", opacity=get_bg_opacity(), visible=bool(resolved),
            )
            self._main_stack = ft.Stack(
                expand=True,
                controls=[self._wallpaper_img, self._bg_overlay, base_content],
            )
            self.content = ft.Container(
                expand=True,
                bgcolor=_BG,
                content=self._main_stack,
            )
        else:
            self._main_stack.controls[2] = base_content

        self._refresh_list()

    def _build_categories(self):
        """Rebuild sidebar category list (no page.update — caller decides)."""
        cats = self._vault.get_categories()
        self._category_column.controls.clear()
        virtual = set(VIRTUAL_CATEGORIES)

        for name, count in cats:
            is_selected = name == self._selected_category
            icon = resolve_category_icon(self._vault.get_category_icon(name))
            is_virtual = name in virtual

            row_controls = [
                ft.Icon(icon, size=16,
                        color=get_accent() if is_selected else get_text_sec()),
                ft.Text(name, size=12, expand=True,
                        color=get_text_main() if is_selected else get_text_sec(),
                        weight=ft.FontWeight.BOLD if is_selected else None),
                ft.Text(str(count), size=11,
                        color=get_accent() if is_selected else get_text_sec()),
            ]
            if not is_virtual:
                row_controls.append(
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        icon_size=14,
                        icon_color=get_text_sec(),
                        tooltip="Options",
                        items=[
                            ft.PopupMenuItem(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.EDIT_OUTLINED, size=14, color=get_text_sec()),
                                        ft.Text("Rename", size=12, color=get_text_main()),
                                    ],
                                    spacing=8,
                                ),
                                on_click=lambda _, n=name: self._on_rename_category(n),
                            ),
                            ft.PopupMenuItem(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.IMAGE_OUTLINED, size=14, color=get_text_sec()),
                                        ft.Text("Edit Icon", size=12, color=get_text_main()),
                                    ],
                                    spacing=8,
                                ),
                                on_click=lambda _, n=name: self._on_edit_category_icon(n),
                            ),
                            ft.PopupMenuItem(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.DELETE_OUTLINED, size=14, color=_DANGER),
                                        ft.Text("Delete", size=12, color=_DANGER),
                                    ],
                                    spacing=8,
                                ),
                                on_click=lambda _, n=name, c=count: self._on_delete_category(n, c),
                            ),
                        ],
                    )
                )

            self._category_column.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=row_controls, spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(left=12, right=4, top=8, bottom=8),
                    border_radius=6,
                    bgcolor=_SURFACE if is_selected else None,
                    on_click=lambda _, n=name: self._on_category_click(n),
                    ink=True,
                )
            )

        self._category_column.controls.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ADD, size=14, color=get_text_sec()),
                        ft.Text("New Category", size=11, color=get_text_sec()),
                    ],
                    spacing=6,
                ),
                padding=ft.Padding(left=12, right=12, top=6, bottom=6),
                border_radius=6,
                on_click=self._on_new_category,
                ink=True,
            )
        )

    def _on_category_click(self, name: str):
        self._selected_category = name
        self._selected_entry_id = None
        self._password_visible = False
        self._detail_panel.content = None
        self._feedback_text.value = ""
        self._build_categories()
        self._refresh_list()
        self._page.update()

    def _on_new_category(self, _):
        """Replace the '+ New Category' button with an inline text field."""
        selected_icon = {"name": "LABEL_OUTLINED"}

        field = ft.TextField(
            hint_text="Category name", width=108, height=34, text_size=12,
            border_color=_BORDER, focused_border_color=get_accent(), cursor_color=get_accent(),
            text_style=ft.TextStyle(color=get_text_main()),
            hint_style=ft.TextStyle(color=get_text_sec()),
            autofocus=True,
        )

        icon_button = ft.IconButton(
            icon=resolve_category_icon(selected_icon["name"]),
            icon_size=16,
            icon_color=get_text_sec(),
            tooltip="Category icon",
            width=28,
            height=28,
        )

        def _set_icon(icon_name: str):
            selected_icon["name"] = (icon_name or "LABEL_OUTLINED").strip().upper() or "LABEL_OUTLINED"
            icon_button.icon = resolve_category_icon(selected_icon["name"])
            icon_button.tooltip = selected_icon["name"].replace("_OUTLINED", "").replace("_", " ").title()
            self._page.update()

        def _open_icon_picker(_):
            show_category_icon_picker_dialog(
                self._page,
                selected_icon["name"],
                on_select=_set_icon,
            )

        icon_button.on_click = _open_icon_picker

        def _confirm(_):
            name = (field.value or "").strip()
            if name and self._vault.add_category(name, selected_icon["name"]):
                self._selected_category = name
            self._build_categories()
            self._refresh_list()
            self._page.update()

        def _cancel(_):
            self._build_categories()
            self._page.update()

        if self._category_column.controls:
            self._category_column.controls[-1] = ft.Container(
                content=ft.Row(
                    controls=[
                        field,
                        icon_button,
                        ft.IconButton(icon=ft.Icons.CHECK, icon_size=14,
                                      icon_color="#4CAF50", on_click=_confirm,
                                      width=28, height=28),
                        ft.IconButton(icon=ft.Icons.CLOSE, icon_size=14,
                                      icon_color=get_text_sec(), on_click=_cancel,
                                      width=28, height=28),
                    ],
                    spacing=2,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(left=8, right=4, top=4, bottom=4),
            )
            self._page.update()

    def _on_rename_category(self, name: str):
        """Replace the category row with an inline rename field."""
        field = ft.TextField(
            value=name, width=110, height=34, text_size=12,
            border_color=_BORDER, focused_border_color=get_accent(), cursor_color=get_accent(),
            text_style=ft.TextStyle(color=get_text_main()),
            autofocus=True,
        )

        def _confirm(_):
            new_name = (field.value or "").strip()
            if new_name and new_name != name:
                if self._vault.rename_category(name, new_name):
                    if self._selected_category == name:
                        self._selected_category = new_name
            self._build_categories()
            self._refresh_list()
            self._page.update()

        def _cancel(_):
            self._build_categories()
            self._page.update()

        cats = self._vault.get_categories()
        for i, (cat_name, _) in enumerate(cats):
            if cat_name == name:
                self._category_column.controls[i] = ft.Container(
                    content=ft.Row(
                        controls=[
                            field,
                            ft.IconButton(icon=ft.Icons.CHECK, icon_size=14,
                                          icon_color="#4CAF50", on_click=_confirm,
                                          width=28, height=28),
                            ft.IconButton(icon=ft.Icons.CLOSE, icon_size=14,
                                          icon_color=get_text_sec(), on_click=_cancel,
                                          width=28, height=28),
                        ],
                        spacing=2,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(left=8, right=4, top=4, bottom=4),
                )
                break
        self._page.update()

    def _on_edit_category_icon(self, name: str):
        """Open icon picker for an existing category and persist selection."""
        current_icon = self._vault.get_category_icon(name)

        def _apply(icon_name: str):
            if self._vault.set_category_icon(name, icon_name):
                self._build_categories()
                self._refresh_list()
                self._page.update()

        show_category_icon_picker_dialog(
            self._page,
            current_icon,
            on_select=_apply,
        )

    def _on_delete_category(self, name: str, entry_count: int):
        """Show confirmation dialog then delete category."""
        def _do_delete():
            self._vault.remove_category(name)
            if self._selected_category == name:
                self._selected_category = "All"
            self._selected_entry_id = None
            self._detail_panel.content = None
            self._build_categories()
            self._refresh_list()
            self._page.update()

        show_delete_category_dialog(
            self._page, name, entry_count, on_confirm=_do_delete,
        )

    def _refresh_list(self):
        """Rebuild the entry list (no page.update — caller decides)."""
        entries = (
            self._vault.search(self._search_query, self._selected_category)
            if self._search_query
            else self._vault.get_entries_summary(self._selected_category)
        )

        self._count_label.value = f"{len(entries)} item{'s' if len(entries) != 1 else ''}"
        self._entry_list.controls.clear()

        if not entries:
            self._entry_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(ft.Icons.INBOX_OUTLINED, size=48, color=_BORDER),
                            ft.Container(height=8),
                            ft.Text("No passwords yet", size=14, color=get_text_sec()),
                            ft.Container(height=8),
                            ft.TextButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.ADD, size=14, color=get_accent()),
                                        ft.Text("Add your first password", size=12,
                                                color=get_accent()),
                                    ],
                                    spacing=4,
                                ),
                                on_click=self._on_add_entry,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.Padding(top=60, left=0, right=0, bottom=0),
                )
            )
        else:
            for e in entries:
                is_sel = e["id"] == self._selected_entry_id
                cat_icon = resolve_category_icon(self._vault.get_category_icon(e["category"]))
                self._entry_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(cat_icon, size=16,
                                        color=get_accent() if is_sel else get_text_sec()),
                                ft.Column(
                                    controls=[
                                        ft.Text(e["title"], size=13,
                                                color=get_text_main() if is_sel else get_text_sec(),
                                                weight=ft.FontWeight.W_500,
                                                max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                        ft.Text(e["username"], size=11, color=get_text_sec() if is_sel else get_text_sec(),
                                                max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS),
                                    ],
                                    spacing=1, expand=True,
                                ),
                                ft.Icon(ft.Icons.STAR, size=14, color=get_accent(),
                                        visible=e.get("favorite", False)),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.Padding(left=12, right=12, top=10, bottom=10),
                        border_radius=6,
                        bgcolor=_SURFACE if is_sel else None,
                        on_click=lambda _, eid=e["id"]: self._on_entry_click(eid),
                        ink=True,
                    )
                )

    def _on_entry_click(self, entry_id: str):
        self._selected_entry_id = entry_id
        self._password_visible = False
        self._feedback_text.value = ""
        self._cancel_password_hide()
        self._show_detail(entry_id)
        self._refresh_list()
        self._page.update()

    def _show_detail(self, entry_id: str):
        """Build the detail panel for *entry_id* (no page.update)."""
        detail = self._vault.get_entry_detail(entry_id)
        if detail is None:
            self._detail_panel.content = None
            return

        password_display = ft.Text(
            "••••••••••••", size=13, color=get_text_main(), font_family="Consolas",
        )

        def _toggle_password(_):
            if self._password_visible:
                password_display.value = "••••••••••••"
                self._password_visible = False
                self._cancel_password_hide()
            else:
                pwd = self._vault.get_password(entry_id)
                if pwd:
                    password_display.value = pwd
                    self._password_visible = True
                    self._schedule_password_hide(password_display)
            self._page.update()

        def _copy_password(_):
            pwd = self._vault.get_password(entry_id)
            if pwd:
                self._clip.copy(pwd, on_feedback=self._show_feedback)
                self._feedback_text.value = "Copied! Clears in 30s"
                self._page.update()

        def _copy_username(_):
            if detail["username"]:
                self._clip.copy(detail["username"], on_feedback=self._show_feedback)
                self._feedback_text.value = "Username copied!"
                self._page.update()

        def _toggle_fav(_):
            self._vault.toggle_favorite(entry_id)
            self._show_detail(entry_id)
            self._build_categories()
            self._refresh_list()
            self._page.update()

        def _edit_entry(_):
            full = self._vault.get_entry_detail(entry_id)
            if full is None:
                return
            pwd = self._vault.get_password(entry_id)
            full["password"] = pwd or ""
            show_add_edit_dialog(
                self._page, self._vault,
                on_save=lambda: self._after_save(entry_id),
                entry=full,
            )

        def _delete_entry(_):
            show_delete_dialog(
                self._page, detail["title"],
                on_confirm=lambda: self._after_delete(entry_id),
            )

        def _detail_row(label, value, icon, copy_handler=None, extra_actions=None):
            ctrls = [
                ft.Icon(icon, size=14, color=get_accent()),
                ft.Text(label, size=11, color=get_text_sec(), width=70),
            ]
            if label == "Password":
                ctrls.append(ft.Container(content=password_display, expand=True))
            else:
                ctrls.append(
                    ft.Text(value or "-", size=13, color=get_text_main(), expand=True,
                            max_lines=3 if label == "Notes" else 1,
                            overflow=ft.TextOverflow.ELLIPSIS, selectable=True),
                )
            if extra_actions:
                ctrls.extend(extra_actions)
            if copy_handler:
                ctrls.append(
                    ft.IconButton(icon=ft.Icons.COPY, icon_size=14,
                                  icon_color=get_text_sec(), tooltip="Copy",
                                  on_click=copy_handler),
                )
            return ft.Container(
                content=ft.Row(controls=ctrls, spacing=8,
                               vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding(left=0, right=0, top=4, bottom=4),
            )

        fav_icon = ft.Icons.STAR if detail.get("favorite") else ft.Icons.STAR_OUTLINE
        fav_color = get_accent() if detail.get("favorite") else get_text_sec()

        self._detail_panel.content = ft.Column(
            controls=[
                ft.Row(controls=[
                    ft.Text(detail["title"], size=20, weight=ft.FontWeight.BOLD,
                            color=get_text_main(), expand=True),
                    ft.IconButton(icon=fav_icon, icon_size=18, icon_color=fav_color,
                                  tooltip="Toggle Favorite", on_click=_toggle_fav),
                ]),
                ft.Text(detail.get("category", "Other"), size=11, color=get_accent()),
                ft.Divider(height=1, color="#222222"),
                _detail_row("Username", detail["username"], ft.Icons.PERSON_OUTLINED,
                            copy_handler=_copy_username),
                _detail_row("Password", "", ft.Icons.KEY_OUTLINED,
                            copy_handler=_copy_password,
                            extra_actions=[
                                ft.IconButton(
                                    icon=ft.Icons.VISIBILITY_OFF if self._password_visible
                                    else ft.Icons.VISIBILITY,
                                    icon_size=14, icon_color=get_text_sec(),
                                    tooltip="Toggle Visibility",
                                    on_click=_toggle_password),
                            ]),
                _detail_row("URL", detail["url"], ft.Icons.LINK),
                _detail_row("Notes", detail["notes"], ft.Icons.NOTES_OUTLINED),
                ft.Container(height=8),
                ft.Row(
                    controls=[
                        ft.Button(
                            content=ft.Row(controls=[
                                ft.Icon(ft.Icons.EDIT, size=14, color=get_text_main()),
                                ft.Text("Edit", size=12, color=get_text_main()),
                            ], spacing=4),
                            bgcolor=_BORDER, height=34, on_click=_edit_entry,
                        ),
                        ft.Button(
                            content=ft.Row(controls=[
                                ft.Icon(ft.Icons.DELETE_OUTLINED, size=14, color=_DANGER),
                                ft.Text("Delete", size=12, color=_DANGER),
                            ], spacing=4),
                            bgcolor="#1a0000", height=34, on_click=_delete_entry,
                        ),
                    ],
                    spacing=8,
                ),
            ],
            spacing=6,
        )

    def _schedule_password_hide(self, password_display: ft.Text):
        self._cancel_password_hide()

        async def _hide():
            try:
                await asyncio.sleep(10)
                password_display.value = "••••••••••••"
                self._password_visible = False
                self._page.update()
            except asyncio.CancelledError:
                pass

        self._password_hide_task = self._page.run_task(_hide)

    def _cancel_password_hide(self):
        if self._password_hide_task and not self._password_hide_task.done():
            self._password_hide_task.cancel()
            self._password_hide_task = None

    async def _on_add_entry(self, _=None):
        show_add_edit_dialog(
            self._page, self._vault,
            on_save=lambda: self._after_save(None),
        )

    def _after_save(self, entry_id: Optional[str]):
        self._build_categories()
        self._refresh_list()
        if entry_id:
            self._show_detail(entry_id)
        self._page.update()

    def _after_delete(self, entry_id: str):
        self._vault.delete_entry(entry_id)
        self._selected_entry_id = None
        self._detail_panel.content = None
        self._feedback_text.value = ""
        self._build_categories()
        self._refresh_list()
        self._page.update()

    def _on_open_color_picker(self, _=None):
        show_color_picker_dialog(self._page, on_apply=self._on_accent_change)

    def _on_open_wallpaper_picker(self, _=None):
        show_wallpaper_picker_dialog(self._page, on_apply=self._on_wallpaper_change)

    def _on_accent_change(self, color: str, text_main: str, text_sec: str):
        """Persist new colours, then rebuild in a task (non-blocking)."""
        async def _rebuild():
            self._build()
            if self._selected_entry_id:
                self._show_detail(self._selected_entry_id)
            self._page.update()

        self._page.run_task(_rebuild)

    def _on_wallpaper_change(self):
        """Update wallpaper image and opacity in-place — no rebuild, no re-parenting."""
        resolved = resolve_wallpaper_src(Settings.get_instance().app_background)
        has_wp = bool(resolved)
        self._wallpaper_img.image.src = resolved or ""
        self._wallpaper_img.visible = has_wp
        self._bg_overlay.visible = has_wp
        self._bg_overlay.opacity = get_bg_opacity()
        self._page.update()

    async def _on_lock(self, _=None):
        state.lock()
        await self._page.push_route("/login")

    async def _on_search_change(self, e):
        """Fires on Enter — executes the search rebuild."""
        self._search_query = (e.control.value or "").strip()
        self._selected_entry_id = None
        self._detail_panel.content = None
        self._refresh_list()
        self._page.update()

    async def _on_search_clear(self, e):
        """Fires on every keystroke — only rebuilds when field is cleared."""
        if not (e.control.value or "").strip():
            self._search_query = ""
            self._selected_entry_id = None
            self._detail_panel.content = None
            self._refresh_list()
            self._page.update()

    def _show_feedback(self, msg: str):
        self._feedback_text.value = msg
        self._page.update()
