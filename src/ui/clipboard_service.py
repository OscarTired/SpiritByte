"""
SpiritByte - Clipboard Service
Copies text to the system clipboard and automatically clears it
after a configurable timeout (default 30 seconds).
"""
import asyncio
from typing import Optional

import flet as ft

CLEAR_TIMEOUT_SECONDS = 30

class ClipboardService:
    """Copy-to-clipboard with automatic clearing after timeout."""

    def __init__(self, page: ft.Page):
        self._page = page
        self._clipboard: Optional[ft.Clipboard] = None
        self._clear_task: Optional[asyncio.Task] = None

    def _ensure_clipboard(self) -> ft.Clipboard:
        """Lazily initialize the Clipboard service on first use."""
        if self._clipboard is None:
            self._clipboard = ft.Clipboard()
            self._page.services.append(self._clipboard)
        return self._clipboard

    def copy(self, text: str, on_feedback: Optional[callable] = None) -> None:
        """Copy *text* to the clipboard and start the auto-clear timer.

        If a previous timer is running it is cancelled first so only the
        most recent copy triggers a clear.

        Args:
            text: The string to place on the clipboard.
            on_feedback: Optional callback invoked with a status message.
        """
        self._cancel_timer()

        clipboard = self._ensure_clipboard()

        async def _do():
            await clipboard.set(text)
            if on_feedback:
                on_feedback(f"Copied! Clears in {CLEAR_TIMEOUT_SECONDS}s")

        self._page.run_task(_do)

        async def _delayed_clear():
            try:
                await asyncio.sleep(CLEAR_TIMEOUT_SECONDS)
                await clipboard.set("")
            except asyncio.CancelledError:
                pass

        self._clear_task = self._page.run_task(_delayed_clear)

    def _cancel_timer(self) -> None:
        if self._clear_task is not None and not self._clear_task.done():
            self._clear_task.cancel()
            self._clear_task = None
