"""
SpiritByte - Login Screen
Handles master password creation and verification
"""
import flet as ft
import os
from core.security import get_security_manager
from app_state import state
from data.settings import Settings, get_accent
from ui.background_layer import build_wallpaper_background
from ui.recovery_dialogs import (
    show_phrase_dialog,
    show_recovery_input_dialog,
    show_forced_password_change_dialog,
)

def create_login_view(page: ft.Page, on_success):
    """Creates and returns the login view controls."""
    
    app_data_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "app_data"
    )
    
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)
    
    security = get_security_manager(app_data_dir)
    is_first_run = not security.master_exists()
    
    error_text = ft.Text(value="", color="#ff4444", size=12, visible=False)
    
    def show_error(message: str):
        error_text.value = message
        error_text.visible = True
        page.update()

    def hide_error():
        error_text.visible = False

    def finish_unlock(key: bytes):
        state.unlock(key)
        if on_success:
            on_success()

    password_field = ft.TextField(
        label="Master Password",
        password=True,
        can_reveal_password=True,
        width=350,
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
        width=350,
        border_color="#333333",
        focused_border_color=get_accent(),
        cursor_color=get_accent(),
        text_style=ft.TextStyle(color="#ffffff"),
        label_style=ft.TextStyle(color="#888888"),
        visible=is_first_run,
    )

    def _show_phrase_then_unlock(key, phrase):
        """Show recovery phrase dialog, then unlock on continue."""
        show_phrase_dialog(page, phrase, on_continue=lambda: finish_unlock(key))

    def _handle_recovery_submit(phrase_text):
        """Called when user submits a recovery phrase."""
        success, key = security.verify_recovery(phrase_text)
        if not success or key is None:
            show_error("Invalid recovery phrase")
            return
        def _on_password_reset(new_key, new_phrase):
            show_phrase_dialog(
                page,
                new_phrase,
                on_continue=lambda: finish_unlock(new_key),
            )
        show_forced_password_change_dialog(page, security, key, _on_password_reset)

    def handle_forgot(_):
        hide_error()
        show_recovery_input_dialog(page, on_submit=_handle_recovery_submit)

    def handle_submit(e):
        hide_error()
        password = password_field.value or ""
        
        if is_first_run:
            confirm = confirm_field.value or ""

            if password != confirm:
                show_error("Passwords do not match")
                return
            
            try:
                key, phrase = security.create_master(password)
                if key and phrase:
                    _show_phrase_then_unlock(key, phrase)
                else:
                    show_error("Failed to create master password")
            except ValueError as ve:
                show_error(str(ve))
            except Exception as ex:
                show_error(f"Error: {str(ex)}")
            return

        if not password:
            show_error("Please enter your password")
            return
        
        success, key, migration_phrase = security.verify_master(password)
        if success and key:
            if migration_phrase:
                _show_phrase_then_unlock(key, migration_phrase)
            else:
                finish_unlock(key)
        else:
            show_error("Incorrect password")

    password_field.on_submit = handle_submit
    confirm_field.on_submit = handle_submit

    submit_button = ft.Button(
        content=ft.Text(
            "Create Password" if is_first_run else "Unlock",
            color="#ffffff",
            weight=ft.FontWeight.W_500,
        ),
        width=350,
        height=45,
        bgcolor=get_accent(),
        on_click=handle_submit,
    )

    def requirement_item(text: str):
        return ft.Row(
            controls=[
                ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=14, color="#666666"),
                ft.Text(text, size=11, color="#666666"),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    password_requirements = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Password Requirements:", size=12, color="#888888", weight=ft.FontWeight.BOLD),
                requirement_item("At least 12 characters"),
                requirement_item("Mix of letters, numbers, and symbols recommended"),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        visible=is_first_run,
        padding=ft.Padding(top=10, left=0, right=0, bottom=0),
    )

    base_content = ft.Container(
        expand=True,
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            controls=[
                ft.Container(height=50),
                ft.Image(
                    src="images/SpireByte.png",
                    width=64,
                    height=64,
                    fit=ft.BoxFit.CONTAIN,
                ),
                ft.Text(
                    value="Create Master Password" if is_first_run else "Enter Master Password",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color="#ffffff",
                ),
                ft.Text(
                    value="This password will protect all your data." if is_first_run
                    else "Enter your master password to unlock SpiritByte",
                    size=14,
                    color="#888888",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=20),
                password_field,
                confirm_field,
                error_text,
                password_requirements,
                ft.Container(height=10),
                submit_button,
                ft.TextButton(
                    content=ft.Text("Forgot?", size=12, color=get_accent()),
                    on_click=handle_forgot,
                    visible=not is_first_run,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=15,
        ),
    )

    return build_wallpaper_background(
        content=base_content,
        wallpaper_src=Settings.get_instance().lock_background,
        fallback_color="#0a0a0a",
        overlay_alpha=0.6,
    )