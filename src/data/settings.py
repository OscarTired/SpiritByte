"""
SpiritByte – User settings (persisted as JSON).
Singleton access via Settings.get_instance() or the get_accent() shortcut.
"""
import json
import os
from typing import Optional

_DEFAULT_ACCENT = "#4a9eff"

ACCENT_PRESETS: list[str] = [
    "#4a9eff",   # Blue (default)
    "#748ffc",   # Indigo
    "#cc5de8",   # Purple
    "#f06595",   # Pink
    "#ff6b6b",   # Red
    "#ff922b",   # Orange
    "#ffd43b",   # Yellow
    "#a9e34b",   # Lime
    "#51cf66",   # Green
    "#20c997",   # Teal
    "#22b8cf",   # Cyan
    "#99e9f2",   # Light Cyan
]

class Settings:
    """Singleton that loads / saves user preferences to *settings.json*."""

    _instance: Optional["Settings"] = None

    def __init__(self, path: str):
        self._path = path
        self._data: dict = {
            "accent_color": _DEFAULT_ACCENT,
            "text_main_color": "#ffffff",
            "text_sec_color": "#888888",
            "bg_opacity": 0.42,
            "app_background": "",
            "lock_background": "",
        }
        self._load()

    @classmethod
    def get_instance(cls, path: Optional[str] = None) -> "Settings":
        if cls._instance is None:
            if path is None:
                raise RuntimeError("Settings not initialised – call with path first")
            cls._instance = cls(path)
        return cls._instance

    def _load(self):
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                if isinstance(stored, dict):
                    self._data.update(stored)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    @property
    def accent_color(self) -> str:
        return self._data.get("accent_color", _DEFAULT_ACCENT)

    @accent_color.setter
    def accent_color(self, value: str):
        self._data["accent_color"] = value
        self.save()

    @property
    def text_main_color(self) -> str:
        return self._data.get("text_main_color", "#ffffff")

    @text_main_color.setter
    def text_main_color(self, value: str):
        self._data["text_main_color"] = value
        self.save()

    @property
    def text_sec_color(self) -> str:
        return self._data.get("text_sec_color", "#888888")

    @text_sec_color.setter
    def text_sec_color(self, value: str):
        self._data["text_sec_color"] = value
        self.save()

    def save_colors(self, accent: str, text_main: str, text_sec: str) -> None:
        """Update all three colour settings with a single file write."""
        self._data["accent_color"] = accent
        self._data["text_main_color"] = text_main
        self._data["text_sec_color"] = text_sec
        self.save()

    @property
    def bg_opacity(self) -> float:
        return self._data.get("bg_opacity", 0.42)

    @bg_opacity.setter
    def bg_opacity(self, value: float):
        self._data["bg_opacity"] = value
        self.save()

    @property
    def app_background(self) -> str:
        return str(self._data.get("app_background", "") or "")

    @app_background.setter
    def app_background(self, value: str):
        self._data["app_background"] = (value or "").strip()
        self.save()

    @property
    def lock_background(self) -> str:
        return str(self._data.get("lock_background", "") or "")

    @lock_background.setter
    def lock_background(self, value: str):
        self._data["lock_background"] = (value or "").strip()
        self.save()

def get_accent() -> str:
    """Convenience: returns the current accent colour."""
    return Settings.get_instance().accent_color

def get_text_main() -> str:
    return Settings.get_instance().text_main_color

def get_text_sec() -> str:
    return Settings.get_instance().text_sec_color

def get_bg_opacity() -> float:
    return Settings.get_instance().bg_opacity
