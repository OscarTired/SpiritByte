"""
SpiritByte - Vault Manager
Handles CRUD operations for password entries with encrypted storage.
All sensitive fields are kept encrypted in memory; passwords are only
decrypted on demand (Just-in-Time).
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from core.security import SecurityManager

_INITIAL_CATEGORIES = ["Social", "Email", "Finance", "Work", "Other"]

_DEFAULT_CATEGORY_ICONS = {
    "All": "FOLDER_OUTLINED",
    "Social": "PEOPLE_OUTLINED",
    "Email": "EMAIL_OUTLINED",
    "Finance": "ACCOUNT_BALANCE_OUTLINED",
    "Work": "WORK_OUTLINED",
    "Other": "MORE_HORIZ",
    "Favorites": "STAR_OUTLINE",
}

def _normalize_category_icon_name(icon_name: str) -> str:
    normalized = (icon_name or "").strip().upper()
    return normalized or "LABEL_OUTLINED"

VIRTUAL_CATEGORIES = ["All", "Favorites"]

class VaultManager:
    """Manages the encrypted password vault."""

    def __init__(self, security: SecurityManager, vault_path: str):
        self._security = security
        self._vault_path = vault_path
        self._entries: list[dict] = []  # encrypted entries in memory
        self._categories: list[str] = []  # all user-managed categories
        self._category_icons: dict[str, str] = {}

    def load(self) -> None:
        """Load encrypted entries from disk."""
        if not os.path.exists(self._vault_path):
            self._entries = []
            self._categories = list(_INITIAL_CATEGORIES)
            self._category_icons = {
                c: _normalize_category_icon_name(_DEFAULT_CATEGORY_ICONS.get(c, "LABEL_OUTLINED"))
                for c in self._categories
            }
            return
        try:
            with open(self._vault_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._entries = data.get("entries", [])
            stored = data.get("categories", None)
            if stored is not None:
                self._categories = stored
            else:
                custom = data.get("custom_categories", [])
                self._categories = list(_INITIAL_CATEGORIES) + custom

            stored_icons = data.get("category_icons", {})
            if isinstance(stored_icons, dict):
                self._category_icons = {
                    str(k): _normalize_category_icon_name(str(v))
                    for k, v in stored_icons.items()
                    if isinstance(k, str) and isinstance(v, str)
                }
            else:
                self._category_icons = {}

            for category in self._categories:
                self._category_icons.setdefault(
                    category,
                    _normalize_category_icon_name(
                        _DEFAULT_CATEGORY_ICONS.get(category, "LABEL_OUTLINED")
                    ),
                )
        except Exception as e:
            print(f"[VAULT] Error loading vault: {e}")
            self._entries = []
            self._categories = list(_INITIAL_CATEGORIES)
            self._category_icons = {
                c: _normalize_category_icon_name(_DEFAULT_CATEGORY_ICONS.get(c, "LABEL_OUTLINED"))
                for c in self._categories
            }

    def save(self) -> None:
        """Persist encrypted entries to disk."""
        try:
            os.makedirs(os.path.dirname(self._vault_path), exist_ok=True)
            category_icons = {
                category: _normalize_category_icon_name(
                    self._category_icons.get(
                        category,
                        _DEFAULT_CATEGORY_ICONS.get(category, "LABEL_OUTLINED"),
                    )
                )
                for category in self._categories
            }
            with open(self._vault_path, "w", encoding="utf-8") as f:
                json.dump({
                    "entries": self._entries,
                    "categories": self._categories,
                    "category_icons": category_icons,
                }, f)
        except Exception as e:
            print(f"[VAULT] Error saving vault: {e}")

    def get_entries_summary(self, category: Optional[str] = None) -> list[dict]:
        """Return a summary list with title and username decrypted.

        Each dict: {id, title, username, category, favorite, updated_at}
        Password and other sensitive fields are NOT decrypted here.
        """
        results = []
        for entry in self._entries:
            if category and category != "All" and category != "Favorites":
                if entry.get("category", "Other") != category:
                    continue
            if category == "Favorites" and not entry.get("favorite", False):
                continue
            try:
                results.append({
                    "id": entry["id"],
                    "title": self._security.decrypt(entry["title"]),
                    "username": self._security.decrypt(entry["username"]),
                    "category": entry.get("category", "Other"),
                    "favorite": entry.get("favorite", False),
                    "updated_at": entry.get("updated_at", ""),
                })
            except Exception:
                continue
        return results

    def get_entry_detail(self, entry_id: str) -> Optional[dict]:
        """Decrypt url and notes for the detail panel (NOT password)."""
        entry = self._find(entry_id)
        if entry is None:
            return None
        try:
            return {
                "id": entry["id"],
                "title": self._security.decrypt(entry["title"]),
                "username": self._security.decrypt(entry["username"]),
                "url": self._security.decrypt(entry["url"]),
                "notes": self._security.decrypt(entry["notes"]),
                "category": entry.get("category", "Other"),
                "favorite": entry.get("favorite", False),
                "created_at": entry.get("created_at", ""),
                "updated_at": entry.get("updated_at", ""),
            }
        except Exception as e:
            print(f"[VAULT] Error decrypting entry detail: {e}")
            return None

    def get_password(self, entry_id: str) -> Optional[str]:
        """JIT: Decrypt and return the password for a single entry."""
        entry = self._find(entry_id)
        if entry is None:
            return None
        try:
            return self._security.decrypt(entry["password"])
        except Exception as e:
            print(f"[VAULT] Error decrypting password: {e}")
            return None

    def add_entry(
        self,
        title: str,
        username: str,
        password: str,
        url: str = "",
        notes: str = "",
        category: str = "Other",
        favorite: bool = False,
    ) -> dict:
        """Encrypt all fields and add a new entry. Returns the summary."""
        now = datetime.now(timezone.utc).isoformat()
        entry = {
            "id": str(uuid.uuid4()),
            "title": self._security.encrypt(title),
            "username": self._security.encrypt(username),
            "password": self._security.encrypt(password),
            "url": self._security.encrypt(url),
            "notes": self._security.encrypt(notes),
            "category": category,
            "favorite": favorite,
            "created_at": now,
            "updated_at": now,
        }
        self._entries.append(entry)
        self.save()
        return {
            "id": entry["id"],
            "title": title,
            "username": username,
            "category": category,
            "favorite": favorite,
            "updated_at": now,
        }

    def update_entry(self, entry_id: str, **fields) -> Optional[dict]:
        """Re-encrypt only the changed fields and save."""
        entry = self._find(entry_id)
        if entry is None:
            return None

        encrypted_fields = {"title", "username", "password", "url", "notes"}
        for key, value in fields.items():
            if key in encrypted_fields:
                entry[key] = self._security.encrypt(value)
            elif key in ("category", "favorite"):
                entry[key] = value

        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save()
        return self.get_entry_detail(entry_id)

    def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry by id."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e["id"] != entry_id]
        if len(self._entries) < before:
            self.save()
            return True
        return False

    def toggle_favorite(self, entry_id: str) -> bool:
        """Toggle the favorite flag and return new state."""
        entry = self._find(entry_id)
        if entry is None:
            return False
        entry["favorite"] = not entry.get("favorite", False)
        self.save()
        return entry["favorite"]

    def search(self, query: str, category: Optional[str] = None) -> list[dict]:
        """Search entries by title or username (case-insensitive)."""
        if not query:
            return self.get_entries_summary(category)
        q = query.lower()
        results = []
        for entry in self._entries:
            if category and category != "All" and category != "Favorites":
                if entry.get("category", "Other") != category:
                    continue
            if category == "Favorites" and not entry.get("favorite", False):
                continue
            try:
                title = self._security.decrypt(entry["title"]).lower()
                username = self._security.decrypt(entry["username"]).lower()
                if q in title or q in username:
                    results.append({
                        "id": entry["id"],
                        "title": self._security.decrypt(entry["title"]),
                        "username": self._security.decrypt(entry["username"]),
                        "category": entry.get("category", "Other"),
                        "favorite": entry.get("favorite", False),
                        "updated_at": entry.get("updated_at", ""),
                    })
            except Exception:
                continue
        return results

    def get_all_selectable_categories(self) -> list[str]:
        """Return all categories that can be assigned to entries."""
        return list(self._categories)

    def get_category_icon(self, name: str) -> str:
        """Return icon key for a category (and virtual categories)."""
        return _normalize_category_icon_name(
            self._category_icons.get(name, _DEFAULT_CATEGORY_ICONS.get(name, "LABEL_OUTLINED"))
        )

    def set_category_icon(self, name: str, icon_name: str) -> bool:
        """Update icon for an existing user category."""
        if name not in self._categories:
            return False
        self._category_icons[name] = _normalize_category_icon_name(icon_name)
        self.save()
        return True

    def add_category(self, name: str, icon_name: str = "LABEL_OUTLINED") -> bool:
        """Add a new category. Returns False if it already exists."""
        name = name.strip()
        if not name:
            return False
        if name in self._categories or name in VIRTUAL_CATEGORIES:
            return False
        self._categories.append(name)
        self._category_icons[name] = _normalize_category_icon_name(icon_name)
        self.save()
        return True

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """Rename a category. Updates all entries that use it."""
        new_name = new_name.strip()
        if not new_name or old_name not in self._categories:
            return False
        if new_name in self._categories or new_name in VIRTUAL_CATEGORIES:
            return False
        idx = self._categories.index(old_name)
        self._categories[idx] = new_name
        old_icon = self._category_icons.pop(
            old_name,
            _DEFAULT_CATEGORY_ICONS.get(old_name, "LABEL_OUTLINED"),
        )
        self._category_icons[new_name] = _normalize_category_icon_name(old_icon)
        for entry in self._entries:
            if entry.get("category") == old_name:
                entry["category"] = new_name
        self.save()
        return True

    def remove_category(self, name: str) -> bool:
        """Remove any category. Entries in it become uncategorized ('Other' fallback)."""
        if name not in self._categories:
            return False
        self._categories.remove(name)
        self._category_icons.pop(name, None)
        fallback = self._categories[0] if self._categories else "Other"
        for entry in self._entries:
            if entry.get("category") == name:
                entry["category"] = fallback
        self.save()
        return True

    def get_categories(self) -> list[tuple[str, int]]:
        """Return categories with entry counts (including virtual ones)."""
        counts: dict[str, int] = {c: 0 for c in self._categories}
        total = 0
        fav_count = 0
        for entry in self._entries:
            cat = entry.get("category", "Other")
            counts[cat] = counts.get(cat, 0) + 1
            total += 1
            if entry.get("favorite", False):
                fav_count += 1
        result = [("All", total)]
        for c in self._categories:
            result.append((c, counts.get(c, 0)))
        result.append(("Favorites", fav_count))
        return result

    def _find(self, entry_id: str) -> Optional[dict]:
        for entry in self._entries:
            if entry["id"] == entry_id:
                return entry
        return None
