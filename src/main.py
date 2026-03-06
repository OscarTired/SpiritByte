"""
SpiritByte - Password Manager
Entry Point
"""
import flet as ft
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_state import state
from core.security import get_security_manager
from data.settings import Settings
from ui.splash import SplashScreen


def _project_root() -> str:
    # Basis of the project under development
    return os.path.dirname(os.path.dirname(__file__))


def _runtime_assets_dir() -> str:
    # Folder of assets available at runtime
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "assets")
    return os.path.join(_project_root(), "assets")


def _app_data_dir() -> str:
    # Persistent folder for app data
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "app_data")
    return os.path.join(_project_root(), "app_data")


def main(page: ft.Page):
    page.title = "SpiritByte"
    page.window.icon = "images/SpireByte.ico"
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 1000
    page.window.min_height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a0a0a"

    page.update()

    page.padding = 0
    page.spacing = 0
    
    app_data_dir = _app_data_dir()
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)

    Settings.get_instance(os.path.join(app_data_dir, "settings.json"))
    security = get_security_manager(app_data_dir)

    def navigate(route: str):
        page.run_task(page.push_route, route)

    def _build_view(route: str) -> ft.View:
        if route == "/":
            return ft.View(
                route="/",
                padding=0,
                spacing=0,
                bgcolor="#0a0a0a",
                controls=[
                    SplashScreen(on_complete=lambda: navigate("/login")),
                ],
            )

        if route == "/login":
            from ui.login import create_login_view

            return ft.View(
                route="/login",
                padding=0,
                spacing=0,
                bgcolor="#0a0a0a",
                controls=[
                    create_login_view(page, on_success=lambda: navigate("/main")),
                ],
            )

        if route == "/main":
            if not state.is_authenticated:
                from ui.login import create_login_view

                return ft.View(
                    route="/login",
                    padding=0,
                    spacing=0,
                    bgcolor="#0a0a0a",
                    controls=[
                        create_login_view(page, on_success=lambda: navigate("/main")),
                    ],
                )
            from ui.main_view import MainView

            return ft.View(
                route="/main",
                padding=0,
                spacing=0,
                bgcolor="#0a0a0a",
                controls=[MainView(page, security)],
            )

        return ft.View(
            route="/",
            padding=0,
            spacing=0,
            bgcolor="#0a0a0a",
            controls=[
                SplashScreen(on_complete=lambda: navigate("/login")),
            ],
        )

    def on_route_change(e: ft.RouteChangeEvent):
        route = e.route if e else (page.route or "/")
        page.views.clear()
        page.views.append(_build_view(route))
        page.update()

    def on_view_pop(e: ft.ViewPopEvent):
        if page.views:
            page.views.pop()
        if not page.views:
            navigate("/")
            return
        navigate(page.views[-1].route)

    page.on_route_change = on_route_change
    page.on_view_pop = on_view_pop
    if not page.route:
        navigate("/")
    on_route_change(None)

if __name__ == "__main__":
    assets_dir = _runtime_assets_dir()
    ft.run(main, assets_dir=assets_dir)