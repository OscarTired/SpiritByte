"""
SpiritByte - Vault Dialogs
Add/Edit entry, Delete confirmation, and Category delete dialogs.
All handlers are async for non-blocking UI. Updates are batched.
"""
import flet as ft
from typing import Callable, Optional

from data.vault import VaultManager
from data.password_generator import generate_password
from data.settings import Settings, get_accent, get_text_main, get_text_sec

_BORDER = "#333333"
_BG = "#0a0a0a"
_SURFACE = "#1a1a1a"
_DANGER = "#ff4444"

_CATEGORY_ICON_DEFAULT = "LABEL_OUTLINED"
_ICON_PAGE_SIZE = 180
_CATEGORY_ICON_OPTIONS: list[str] = sorted(
    name
    for name in dir(ft.Icons)
    if name.isupper()
)

def _field(label: str, value: str = "", **kwargs) -> ft.TextField:
    """Factory for consistently styled text fields."""
    defaults = dict(
        label=label,
        value=value,
        width=460,
        border_color=_BORDER,
        focused_border_color=get_accent(),
        cursor_color=get_accent(),
        text_style=ft.TextStyle(color=get_text_main()),
        label_style=ft.TextStyle(color=get_text_sec()),
    )
    defaults.update(kwargs)
    return ft.TextField(**defaults)

def _normalize_icon_name(icon_name: str) -> str:
    normalized = (icon_name or "").strip().upper()
    return normalized or _CATEGORY_ICON_DEFAULT

def _format_icon_title(icon_name: str) -> str:
    return icon_name.replace("_OUTLINED", "").replace("_", " ").title()

def resolve_category_icon(icon_name: str):
    """Resolve persisted icon key into a Flet icon enum value."""
    normalized = _normalize_icon_name(icon_name)
    return getattr(ft.Icons, normalized, ft.Icons.LABEL_OUTLINED)

def show_category_icon_picker_dialog(
    page: ft.Page,
    selected_icon: str,
    on_select: Callable[[str], None],
) -> None:
    """Open a modal category icon picker with a grid of available icons."""
    state = {
        "icon": _normalize_icon_name(selected_icon),
        "query": "",
        "page": 0,
    }
    picker_accent = get_accent()

    selected_preview = ft.Icon(resolve_category_icon(state["icon"]), size=20, color=picker_accent)
    selected_label = ft.Text(_format_icon_title(state["icon"]), size=10, color=get_text_sec())
    icon_grid = ft.Row(wrap=True, spacing=8, run_spacing=8)
    icon_count_label = ft.Text("", size=10, color=get_text_sec())
    page_label = ft.Text("", size=10, color=get_text_sec())
    prev_button = ft.IconButton(
        icon=ft.Icons.CHEVRON_LEFT,
        icon_size=16,
        icon_color=get_text_sec(),
        tooltip="Previous page",
        width=30,
        height=30,
    )
    next_button = ft.IconButton(
        icon=ft.Icons.CHEVRON_RIGHT,
        icon_size=16,
        icon_color=get_text_sec(),
        tooltip="Next page",
        width=30,
        height=30,
    )

    def _filtered_icons() -> list[str]:
        query = (state["query"] or "").strip().upper()
        if not query:
            return _CATEGORY_ICON_OPTIONS
        return [icon_name for icon_name in _CATEGORY_ICON_OPTIONS if query in icon_name]

    def _paged_icons(filtered: list[str]) -> tuple[list[str], int]:
        total_pages = max(1, (len(filtered) + _ICON_PAGE_SIZE - 1) // _ICON_PAGE_SIZE)
        state["page"] = min(max(state["page"], 0), total_pages - 1)
        start = state["page"] * _ICON_PAGE_SIZE
        end = start + _ICON_PAGE_SIZE
        return filtered[start:end], total_pages

    def _pick(icon_name: str):
        state["icon"] = icon_name
        selected_preview.icon = resolve_category_icon(icon_name)
        selected_label.value = _format_icon_title(icon_name)
        _rebuild_grid()
        page.update()

    def _rebuild_grid():
        filtered = _filtered_icons()
        visible_icons, total_pages = _paged_icons(filtered)

        icon_grid.controls.clear()
        for icon_name in visible_icons:
            is_selected = icon_name == state["icon"]
            icon_grid.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                resolve_category_icon(icon_name),
                                size=20,
                                color=picker_accent if is_selected else get_text_main(),
                            ),
                            ft.Text(
                                _format_icon_title(icon_name),
                                size=9,
                                color=get_text_sec(),
                                text_align=ft.TextAlign.CENTER,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=3,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    width=78,
                    height=68,
                    padding=6,
                    border_radius=8,
                    border=ft.Border.all(1.5, picker_accent if is_selected else _BORDER),
                    bgcolor=_SURFACE if is_selected else "#111111",
                    ink=True,
                    on_click=lambda _, n=icon_name: _pick(n),
                )
            )

        count = len(filtered)
        icon_count_label.value = f"{count} icon{'s' if count != 1 else ''}"
        page_label.value = f"Page {state['page'] + 1}/{total_pages}"
        prev_button.disabled = state["page"] <= 0
        next_button.disabled = state["page"] >= total_pages - 1

    def _go_prev(_):
        state["page"] = max(0, state["page"] - 1)
        _rebuild_grid()
        page.update()

    def _go_next(_):
        filtered = _filtered_icons()
        total_pages = max(1, (len(filtered) + _ICON_PAGE_SIZE - 1) // _ICON_PAGE_SIZE)
        state["page"] = min(total_pages - 1, state["page"] + 1)
        _rebuild_grid()
        page.update()

    def _on_search_change(e):
        state["query"] = (e.control.value or "").strip()
        state["page"] = 0
        _rebuild_grid()
        page.update()

    search_field = ft.TextField(
        hint_text="Search icon (e.g. LOCK, CLOUD, EMAIL)",
        width=300,
        height=34,
        text_size=11,
        border_color=_BORDER,
        focused_border_color=picker_accent,
        cursor_color=picker_accent,
        text_style=ft.TextStyle(color=get_text_main()),
        hint_style=ft.TextStyle(color=get_text_sec()),
        on_change=_on_search_change,
    )

    prev_button.on_click = _go_prev
    next_button.on_click = _go_next

    _rebuild_grid()

    async def _close(_=None):
        dialog.open = False
        page.update()

    async def _apply(_):
        picked = state["icon"]
        dialog.open = False
        page.update()
        on_select(picked)

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=_BG,
        title=ft.Row(
            controls=[
                ft.Icon(ft.Icons.GRID_VIEW_OUTLINED, size=20, color=picker_accent),
                ft.Text("Category Icon", size=15, weight=ft.FontWeight.BOLD, color=picker_accent),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("Selected:", size=11, color=get_text_sec()),
                            selected_preview,
                            selected_label,
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[
                            search_field,
                            icon_count_label,
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=ft.Column(controls=[icon_grid], scroll=ft.ScrollMode.AUTO),
                        height=320,
                    ),
                    ft.Row(
                        controls=[prev_button, page_label, next_button],
                        spacing=6,
                        alignment=ft.MainAxisAlignment.END,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=8,
                tight=True,
            ),
            width=520,
        ),
        actions=[
            ft.TextButton(content=ft.Text("Cancel", color=get_text_sec()), on_click=_close),
            ft.Button(
                content=ft.Text("Use Icon", color=get_text_main(), weight=ft.FontWeight.W_500),
                bgcolor=picker_accent,
                width=110,
                height=36,
                on_click=_apply,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def show_add_edit_dialog(
    page: ft.Page,
    vault: VaultManager,
    on_save: Callable,
    entry: Optional[dict] = None,
) -> None:
    """Show a modal dialog to add or edit a vault entry."""
    is_edit = entry is not None

    title_field = _field("Title", entry.get("title", "") if is_edit else "")
    username_field = _field("Username / Email", entry.get("username", "") if is_edit else "")
    password_field = _field(
        "Password", entry.get("password", "") if is_edit else "",
        password=True, can_reveal_password=True,
    )
    url_field = _field("URL", entry.get("url", "") if is_edit else "")
    notes_field = _field(
        "Notes", entry.get("notes", "") if is_edit else "",
        multiline=True, min_lines=1, max_lines=3,
    )

    _sentinel = "__new__"
    selectable = vault.get_all_selectable_categories()

    def _cat_opts():
        opts = [ft.dropdown.Option(c) for c in selectable]
        opts.append(ft.dropdown.Option(_sentinel, text="+ New Category"))
        return opts

    category_dropdown = ft.Dropdown(
        label="Category",
        value=entry.get("category", "Other") if is_edit else "Other",
        width=460,
        border_color=_BORDER,
        focused_border_color=get_accent(),
        text_style=ft.TextStyle(color=get_text_main()),
        label_style=ft.TextStyle(color=get_text_sec()),
        options=_cat_opts(),
        bgcolor=_SURFACE,
    )

    new_cat_field = _field("New category name", width=300)
    selected_new_cat_icon = {"name": _CATEGORY_ICON_DEFAULT}
    new_cat_icon_name = ft.Text("Label", size=11, color=get_text_sec(), width=62)
    new_cat_icon_button = ft.IconButton(
        icon=resolve_category_icon(selected_new_cat_icon["name"]),
        icon_color=get_text_sec(),
        icon_size=18,
        tooltip="Choose category icon",
    )
    new_cat_row = ft.Container(visible=False)

    def _reset_new_cat_icon():
        selected_new_cat_icon["name"] = _CATEGORY_ICON_DEFAULT
        new_cat_icon_button.icon = resolve_category_icon(_CATEGORY_ICON_DEFAULT)
        new_cat_icon_name.value = "Label"

    def _set_new_cat_icon(icon_name: str):
        selected_new_cat_icon["name"] = _normalize_icon_name(icon_name)
        new_cat_icon_button.icon = resolve_category_icon(selected_new_cat_icon["name"])
        new_cat_icon_name.value = selected_new_cat_icon["name"].replace("_OUTLINED", "").replace("_", " ").title()
        page.update()

    async def _open_new_cat_icon_picker(_):
        show_category_icon_picker_dialog(
            page,
            selected_new_cat_icon["name"],
            on_select=_set_new_cat_icon,
        )

    new_cat_icon_button.on_click = _open_new_cat_icon_picker

    async def _on_cat_change(e):
        if category_dropdown.value == _sentinel:
            new_cat_row.visible = True
            new_cat_row.content = ft.Row(
                controls=[
                    new_cat_field,
                    new_cat_icon_button,
                    new_cat_icon_name,
                    ft.IconButton(icon=ft.Icons.CHECK, icon_color="#4CAF50",
                                  icon_size=18, tooltip="Add", on_click=_add_new_cat),
                    ft.IconButton(icon=ft.Icons.CLOSE, icon_color=get_text_sec(),
                                  icon_size=18, tooltip="Cancel",
                                  on_click=_cancel_new_cat),
                ],
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        else:
            new_cat_row.visible = False
        page.update()

    async def _add_new_cat(_):
        name = (new_cat_field.value or "").strip()
        if name and vault.add_category(name, selected_new_cat_icon["name"]):
            selectable.append(name)
            category_dropdown.options = _cat_opts()
            category_dropdown.value = name
        new_cat_row.visible = False
        new_cat_field.value = ""
        _reset_new_cat_icon()
        page.update()

    async def _cancel_new_cat(_):
        category_dropdown.value = "Other"
        new_cat_row.visible = False
        new_cat_field.value = ""
        _reset_new_cat_icon()
        page.update()

    category_dropdown.on_change = _on_cat_change

    error_text = ft.Text(value="", color=_DANGER, size=12, visible=False)

    gen_length_slider = ft.Slider(
        min=8, max=64, value=16, divisions=56,
        active_color=get_accent(), inactive_color=_BORDER, width=260,
    )
    gen_length_label = ft.Text("16", size=12, color=get_text_main(), width=30)
    gen_upper = ft.Checkbox(label="A-Z", value=True, active_color=get_accent(),
                            label_style=ft.TextStyle(color=get_text_sec(), size=11))
    gen_lower = ft.Checkbox(label="a-z", value=True, active_color=get_accent(),
                            label_style=ft.TextStyle(color=get_text_sec(), size=11))
    gen_digits = ft.Checkbox(label="0-9", value=True, active_color=get_accent(),
                             label_style=ft.TextStyle(color=get_text_sec(), size=11))
    gen_symbols = ft.Checkbox(label="!@#", value=True, active_color=get_accent(),
                              label_style=ft.TextStyle(color=get_text_sec(), size=11))
    gen_panel = ft.Container(visible=False)

    async def _on_slider_change(e):
        gen_length_label.value = str(int(gen_length_slider.value))
        page.update()

    gen_length_slider.on_change = _on_slider_change

    async def _generate_password(_):
        password_field.value = generate_password(
            length=int(gen_length_slider.value),
            uppercase=gen_upper.value, lowercase=gen_lower.value,
            digits=gen_digits.value, symbols=gen_symbols.value,
        )
        page.update()

    async def _toggle_generator(_):
        gen_panel.visible = not gen_panel.visible
        if gen_panel.visible and gen_panel.content is None:
            gen_panel.content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Password Generator", size=12, color=get_accent(),
                                weight=ft.FontWeight.BOLD),
                        ft.Row(
                            controls=[
                                ft.Text("Length:", size=11, color=get_text_sec()),
                                gen_length_slider, gen_length_label,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        ft.Row(controls=[gen_upper, gen_lower, gen_digits, gen_symbols],
                               spacing=4),
                        ft.Button(
                            content=ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.REFRESH, size=14, color=get_text_main()),
                                    ft.Text("Generate", size=12, color=get_text_main()),
                                ],
                                spacing=4,
                            ),
                            bgcolor=get_accent(), height=32, on_click=_generate_password,
                        ),
                    ],
                    spacing=5,
                ),
                bgcolor="#111111", border_radius=6, padding=10,
            )
        page.update()

    async def _close(_=None):
        dialog.open = False
        page.update()

    async def _handle_save(_):
        title_val = (title_field.value or "").strip()
        password_val = (password_field.value or "").strip()

        if not title_val:
            error_text.value = "Title is required"
            error_text.visible = True
            page.update()
            return
        if not password_val:
            error_text.value = "Password is required"
            error_text.visible = True
            page.update()
            return

        error_text.visible = False
        cat = category_dropdown.value or "Other"

        if is_edit:
            vault.update_entry(
                entry["id"],
                title=title_val,
                username=(username_field.value or "").strip(),
                password=password_val,
                url=(url_field.value or "").strip(),
                notes=(notes_field.value or "").strip(),
                category=cat,
            )
        else:
            vault.add_entry(
                title=title_val,
                username=(username_field.value or "").strip(),
                password=password_val,
                url=(url_field.value or "").strip(),
                notes=(notes_field.value or "").strip(),
                category=cat,
            )

        dialog.open = False
        page.update()
        on_save()

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=_BG,
        title=ft.Row(
            controls=[
                ft.Icon(ft.Icons.EDIT if is_edit else ft.Icons.ADD_CIRCLE_OUTLINE,
                        size=20, color=get_accent()),
                ft.Text("Edit Entry" if is_edit else "New Entry", size=16,
                        weight=ft.FontWeight.BOLD, color=get_accent()),
            ],
            spacing=8,
        ),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    title_field, username_field,
                    ft.Row(
                        controls=[
                            ft.Container(content=password_field, expand=True),
                            ft.IconButton(icon=ft.Icons.AUTO_AWESOME, icon_color=get_accent(),
                                          icon_size=20, tooltip="Password Generator",
                                          on_click=_toggle_generator),
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    gen_panel, url_field, notes_field,
                    category_dropdown, new_cat_row, error_text,
                ],
                spacing=8,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=500,
        ),
        actions=[
            ft.TextButton(content=ft.Text("Cancel", color=get_text_sec()), on_click=_close),
            ft.Button(
                content=ft.Text("Save" if is_edit else "Add", color=get_text_main(),
                                weight=ft.FontWeight.W_500),
                bgcolor=get_accent(), width=100, height=38, on_click=_handle_save,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def show_delete_dialog(
    page: ft.Page,
    entry_title: str,
    on_confirm: Callable,
) -> None:
    """Compact confirmation dialog for deleting a credential."""

    async def _close(_=None):
        dialog.open = False
        page.update()

    async def _handle_confirm(_):
        dialog.open = False
        page.update()
        on_confirm()

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=_BG,
        title=ft.Text("Delete Entry", size=14, weight=ft.FontWeight.BOLD, color=_DANGER),
        content=ft.Column(
            controls=[
                ft.Text(f'Delete "{entry_title}"?', size=12, color=get_text_main()),
                ft.Text("This cannot be undone.", size=11, color=get_text_sec()),
            ],
            spacing=4,
            tight=True,
        ),
        actions=[
            ft.TextButton(content=ft.Text("Cancel", color=get_text_sec()), on_click=_close),
            ft.Button(
                content=ft.Text("Delete", color=get_text_main(), weight=ft.FontWeight.W_500),
                bgcolor=_DANGER, width=100, height=32, on_click=_handle_confirm,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def show_delete_category_dialog(
    page: ft.Page,
    category_name: str,
    entry_count: int,
    on_confirm: Callable,
) -> None:
    """Compact confirmation dialog for deleting a category."""

    async def _close(_=None):
        dialog.open = False
        page.update()

    async def _handle_confirm(_):
        dialog.open = False
        page.update()
        on_confirm()

    content_controls = [
        ft.Text(f'Delete category "{category_name}"?', size=12, color=get_text_main()),
    ]
    if entry_count > 0:
        content_controls.append(
            ft.Text(
                f"{entry_count} credential{'s' if entry_count != 1 else ''} will be moved.",
                size=11, color=get_text_sec(),
            )
        )

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor=_BG,
        title=ft.Text("Delete Category", size=14, weight=ft.FontWeight.BOLD, color=_DANGER),
        content=ft.Column(controls=content_controls, spacing=4, tight=True),
        actions=[
            ft.TextButton(content=ft.Text("Cancel", color=get_text_sec()), on_click=_close),
            ft.Button(
                content=ft.Text("Delete", color=get_text_main(), weight=ft.FontWeight.W_500),
                bgcolor=_DANGER, width=100, height=32, on_click=_handle_confirm,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()
