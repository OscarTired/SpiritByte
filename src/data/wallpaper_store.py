"""
SpiritByte - Wallpaper storage helpers.
Imports user-selected images/GIFs into app assets and validates stored paths.
"""

import os
import shutil
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

SUPPORTED_WALLPAPER_EXTENSIONS = ["png", "jpg", "jpeg", "gif"]

_MAX_GIF_BYTES = 8 * 1024 * 1024
_MAX_SOURCE_BYTES = 25 * 1024 * 1024
_MAX_STATIC_SIZE = (1920, 1080)

_ASSET_PREFIX = "images/wallpapers"
_VALID_SLOTS = {"app", "lock"}

def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

def _assets_root() -> str:
    return os.path.join(_project_root(), "assets")

def _wallpaper_assets_dir() -> str:
    return os.path.join(_assets_root(), "images", "wallpapers")

def _normalize_path(value: str) -> str:
    return (value or "").strip().replace("\\", "/").lstrip("./")

def _save_static_image(source_path: str, destination_path: str, ext: str) -> None:
    """Downscale/compress static images so wallpapers stay responsive."""
    try:
        with Image.open(source_path) as img:
            img.load()
            img.thumbnail(_MAX_STATIC_SIZE, Image.Resampling.LANCZOS)

            if ext in ("jpg", "jpeg"):
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                img.save(
                    destination_path,
                    format="JPEG",
                    quality=85,
                    optimize=True,
                )
                return

            if img.mode not in ("RGB", "RGBA", "L", "LA", "P"):
                img = img.convert("RGBA")
            img.save(destination_path, format="PNG", optimize=True)
    except (UnidentifiedImageError, OSError, ValueError) as ex:
        raise ValueError("Invalid image file") from ex

def resolve_wallpaper_src(stored_path: str) -> str:
    """Return an absolute file path for the wallpaper, or empty string.

    Flet's built-in asset server only indexes files present at startup,
    so dynamically imported wallpapers must be referenced by absolute path.
    """
    normalized = _normalize_path(stored_path)
    if not normalized:
        return ""

    if os.path.isabs(normalized):
        return ""

    if normalized.startswith("assets/"):
        normalized = normalized[len("assets/") :]

    absolute = os.path.join(_assets_root(), *normalized.split("/"))
    if os.path.isfile(absolute):
        return absolute.replace("\\", "/")
    return ""

def import_wallpaper_to_assets(source_path: str, slot: str) -> str:
    """Copy a selected wallpaper into app assets and return relative src path."""
    if slot not in _VALID_SLOTS:
        raise ValueError("Invalid wallpaper slot")

    source = (source_path or "").strip()
    if not source or not os.path.isfile(source):
        raise ValueError("Wallpaper file not found")

    ext = Path(source).suffix.lower().lstrip(".")
    if ext not in SUPPORTED_WALLPAPER_EXTENSIONS:
        raise ValueError("Unsupported wallpaper format")

    source_size = os.path.getsize(source)
    if source_size > _MAX_SOURCE_BYTES:
        raise ValueError("Wallpaper is too large (max 25 MB)")
    if ext == "gif" and source_size > _MAX_GIF_BYTES:
        raise ValueError("GIF is too large (max 8 MB)")

    destination_dir = _wallpaper_assets_dir()
    os.makedirs(destination_dir, exist_ok=True)

    slot_prefix = f"{slot}_"
    for filename in os.listdir(destination_dir):
        if filename.startswith(slot_prefix):
            stale = os.path.join(destination_dir, filename)
            try:
                os.remove(stale)
            except OSError:
                pass

    destination_name = f"{slot}_{uuid.uuid4().hex}.{ext}"
    destination_path = os.path.join(destination_dir, destination_name)
    if ext == "gif":
        shutil.copy2(source, destination_path)
    else:
        _save_static_image(source, destination_path, ext)
    return f"{_ASSET_PREFIX}/{destination_name}"

def remove_imported_wallpaper(stored_path: str) -> None:
    """Delete an imported wallpaper file if it belongs to the managed directory."""
    src = resolve_wallpaper_src(stored_path)
    if not src:
        return

    managed = _wallpaper_assets_dir().replace("\\", "/")
    if not src.startswith(managed):
        return

    try:
        os.remove(src)
    except OSError:
        pass

def load_wallpaper_bytes(stored_path: str) -> bytes | None:
    """Return wallpaper file bytes for rendering, or None if unavailable."""
    src = resolve_wallpaper_src(stored_path)
    if not src:
        return None

    try:
        with open(src, "rb") as fh:
            return fh.read()
    except OSError:
        return None
