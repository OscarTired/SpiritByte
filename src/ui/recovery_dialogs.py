"""
SpiritByte - Recovery Dialogs
Flet modals for BIP39 mnemonic phrase display, recovery input,
and forced password change after recovery.
"""
import flet as ft
from typing import Callable, Optional

from core.recovery import generate_qr_bytes
from data.settings import Settings, get_accent, get_text_main, get_text_sec

def _word_chip(index: int, word: str) -> ft.Container:
    """Single numbered word chip for the mnemonic grid."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    f"{index}.",
                    size=11,
                    color="#888888",
                    font_family="Consolas",
                    width=22,
                    text_align=ft.TextAlign.RIGHT,
                ),
                ft.Text(
                    word,
                    size=13,
                    color="#ffffff",
                    font_family="Consolas",
                    weight=ft.FontWeight.W_500,
                ),
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.START,
        ),
        bgcolor="#1a1a1a",
        border=ft.Border.all(1, "#333333"),
        border_radius=6,
        padding=ft.Padding(left=8, right=12, top=6, bottom=6),
        width=155,
    )

def show_phrase_dialog(
    page: ft.Page,
    phrase: str,
    on_continue: Callable,
) -> None:
    """Display the 12-word recovery phrase with Copy and QR options."""

    words = phrase.split()
    saved_checkbox = ft.Checkbox(
        label="I have saved my recovery phrase",
        label_style=ft.TextStyle(color="#888888", size=12),
        value=False,
        active_color=get_accent(),
    )
    continue_btn = ft.Button(
        content=ft.Text("Continue", color="#ffffff", weight=ft.FontWeight.W_500),
        bgcolor="#333333",
        width=140,
        height=38,
        disabled=True,
        on_click=lambda _: _close_and_continue(),
    )
    qr_container = ft.Container(visible=False)
    copy_feedback = ft.Text(value="", size=11, color=get_accent())

    def _on_checkbox_change(e):
        continue_btn.disabled = not saved_checkbox.value
        continue_btn.bgcolor = get_accent() if saved_checkbox.value else "#333333"
        page.update()

    saved_checkbox.on_change = _on_checkbox_change

    _clipboard = ft.Clipboard()
    page.services.append(_clipboard)

    async def _do_copy():
        await _clipboard.set(phrase)

    def _copy_phrase(_):
        page.run_task(_do_copy)
        copy_feedback.value = "Copied!"
        page.update()

    def _toggle_qr(_):
        if qr_container.visible:
            qr_container.visible = False
        else:
            if qr_container.content is None:
                qr_bytes = generate_qr_bytes(phrase)
                qr_container.content = ft.Image(
                    src=qr_bytes,
                    width=200,
                    height=200,
                )
            qr_container.visible = True
        page.update()

    def _close_and_continue():
        dialog.open = False
        page.update()
        on_continue()

    grid_rows = []
    for row_idx in range(3):
        row_chips = []
        for col_idx in range(4):
            i = row_idx * 4 + col_idx
            if i < len(words):
                row_chips.append(_word_chip(i + 1, words[i]))
        grid_rows.append(
            ft.Row(controls=row_chips, spacing=8, alignment=ft.MainAxisAlignment.CENTER)
        )

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor="#0a0a0a",
        title=ft.Text(
            "> RECOVERY PHRASE",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=get_accent(),
            font_family="Consolas",
        ),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Write down these 12 words in order. This is the ONLY way to recover your account.",
                        size=12,
                        color="#888888",
                    ),
                    ft.Container(height=8),
                    *grid_rows,
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.TextButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.COPY, size=14, color=get_accent()),
                                        ft.Text("Copy", size=12, color=get_accent()),
                                    ],
                                    spacing=4,
                                ),
                                on_click=_copy_phrase,
                            ),
                            ft.TextButton(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.QR_CODE, size=14, color=get_accent()),
                                        ft.Text("QR Code", size=12, color=get_accent()),
                                    ],
                                    spacing=4,
                                ),
                                on_click=_toggle_qr,
                            ),
                            copy_feedback,
                        ],
                        spacing=8,
                    ),
                    qr_container,
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Text(
                            "⚠ This phrase will NOT be shown again.",
                            size=11,
                            color="#ff4444",
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor="#1a0000",
                        border=ft.Border.all(1, "#ff444444"),
                        border_radius=4,
                        padding=8,
                    ),
                    ft.Container(height=4),
                    saved_checkbox,
                ],
                spacing=4,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=680,
            height=420,
        ),
        actions=[continue_btn],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def show_recovery_input_dialog(
    page: ft.Page,
    on_submit: Callable[[str], None],
    on_cancel: Optional[Callable] = None,
) -> None:
    """Modal for the user to enter their 12-word recovery phrase."""

    phrase_field = ft.TextField(
        label="Enter your 12-word recovery phrase",
        multiline=True,
        min_lines=2,
        max_lines=3,
        width=500,
        border_color="#333333",
        focused_border_color=get_accent(),
        cursor_color=get_accent(),
        text_style=ft.TextStyle(color="#ffffff", font_family="Consolas", size=13),
        label_style=ft.TextStyle(color="#888888"),
    )
    error_text = ft.Text(value="", color="#ff4444", size=12, visible=False)

    def _close():
        dialog.open = False
        page.update()

    def _handle_recover(_):
        value = (phrase_field.value or "").strip()
        if not value:
            error_text.value = "Please enter your recovery phrase"
            error_text.visible = True
            page.update()
            return
        word_count = len(value.split())
        if word_count != 12:
            error_text.value = f"Expected 12 words, got {word_count}"
            error_text.visible = True
            page.update()
            return
        error_text.visible = False
        _close()
        on_submit(value)

    def _handle_cancel(_):
        _close()
        if on_cancel:
            on_cancel()

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor="#0a0a0a",
        title=ft.Text(
            "> ACCOUNT RECOVERY",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=get_accent(),
            font_family="Consolas",
        ),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Enter the 12-word mnemonic phrase you saved when creating your account.",
                        size=12,
                        color="#888888",
                    ),
                    ft.Container(height=8),
                    phrase_field,
                    error_text,
                ],
                spacing=6,
            ),
            width=540,
        ),
        actions=[
            ft.TextButton(
                content=ft.Text("Cancel", color="#888888"),
                on_click=_handle_cancel,
            ),
            ft.Button(
                content=ft.Text("Recover", color="#ffffff", weight=ft.FontWeight.W_500),
                bgcolor=get_accent(),
                width=120,
                height=38,
                on_click=_handle_recover,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()

def show_forced_password_change_dialog(
    page: ft.Page,
    security_manager,
    current_key: bytes,
    on_complete: Callable[[bytes, str], None],
) -> None:
    """Force the user to set a new password after recovery.
    on_complete receives (new_encryption_key, new_recovery_phrase).
    """

    new_pass_field = ft.TextField(
        label="New Master Password",
        password=True,
        can_reveal_password=True,
        width=400,
        border_color="#333333",
        focused_border_color=get_accent(),
        cursor_color=get_accent(),
        text_style=ft.TextStyle(color="#ffffff"),
        label_style=ft.TextStyle(color="#888888"),
    )
    confirm_field = ft.TextField(
        label="Confirm Password",
        password=True,
        can_reveal_password=True,
        width=400,
        border_color="#333333",
        focused_border_color=get_accent(),
        cursor_color=get_accent(),
        text_style=ft.TextStyle(color="#ffffff"),
        label_style=ft.TextStyle(color="#888888"),
    )
    error_text = ft.Text(value="", color="#ff4444", size=12, visible=False)

    def _handle_submit(_):
        new_pass = new_pass_field.value or ""
        confirm = confirm_field.value or ""

        if len(new_pass) < 12:
            error_text.value = "Password must be at least 12 characters"
            error_text.visible = True
            page.update()
            return
        if new_pass != confirm:
            error_text.value = "Passwords do not match"
            error_text.visible = True
            page.update()
            return

        try:
            new_key, new_phrase = security_manager.reset_master(new_pass, current_key)
            if new_key and new_phrase:
                dialog.open = False
                page.update()
                on_complete(new_key, new_phrase)
            else:
                error_text.value = "Failed to reset password"
                error_text.visible = True
                page.update()
        except ValueError as ve:
            error_text.value = str(ve)
            error_text.visible = True
            page.update()
        except Exception as ex:
            error_text.value = f"Error: {str(ex)}"
            error_text.visible = True
            page.update()

    dialog = ft.AlertDialog(
        modal=True,
        bgcolor="#0a0a0a",
        title=ft.Text(
            "> PASSWORD RESET REQUIRED",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=get_accent(),
            font_family="Consolas",
        ),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "You must set a new master password to continue.",
                        size=12,
                        color="#888888",
                    ),
                    ft.Container(height=8),
                    new_pass_field,
                    confirm_field,
                    error_text,
                    ft.Container(height=4),
                    ft.Text(
                        "Minimum 12 characters",
                        size=11,
                        color="#666666",
                    ),
                ],
                spacing=10,
            ),
            width=440,
        ),
        actions=[
            ft.Button(
                content=ft.Text("Set Password", color="#ffffff", weight=ft.FontWeight.W_500),
                bgcolor=get_accent(),
                width=140,
                height=38,
                on_click=_handle_submit,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    page.overlay.append(dialog)
    dialog.open = True
    page.update()
