"""
SpiritByte - Splash Screen with ASCII Lock + Glitch Effect
"""
import flet as ft
import random
import asyncio
from typing import Callable, Optional
import random
import asyncio
import math
import time

from data.settings import get_accent, get_text_main, get_text_sec
from .ascii_lock import LOCK_OPEN, LOCK_CLOSED

_LOCK_OPEN_CHARS: list = list(LOCK_OPEN)
_LOCK_CLOSED_CHARS: list = list(LOCK_CLOSED)

GLITCH_CHARS = "10101010<>/\\|?*+=-_.:;!¡¦|¦|_¬⌐"
VHS_CHARS = "01░▒▓¢£¥§©®±µ¶·¸¹º»¼½¾¿"

def _non_space_positions(text: str) -> list[int]:
    return [i for i, ch in enumerate(text) if ch not in (" ", "\n")]

class GlitchEngine:
    """Handles all glitch effects adapted from TSX shaders"""
    
    def __init__(self):
        self.time = 0.0
        self.glitch_intensity = 0.5
        self.noise_intensity = 0.5
        self.jitter_intensity = 0.5
        self.scanline_enabled = True
        
    def apply_noise(
        self,
        text: str,
        intensity: float,
        positions: Optional[list[int]] = None,
        base_chars: Optional[list] = None,
    ) -> str:
        """Replace random characters with glitch chars (from ascii.txt noise effect)"""
        if not positions:
            result = list(text)
            for i, char in enumerate(result):
                if char not in (" ", "\n") and random.random() < intensity:
                    result[i] = random.choice(GLITCH_CHARS)
            return "".join(result)

        result = list(base_chars) if base_chars is not None else list(text)
        count = max(1, int(len(positions) * intensity * 0.06))
        count = min(count, len(positions))
        for idx in random.sample(positions, k=count):
            result[idx] = random.choice(GLITCH_CHARS)
        return "".join(result)
    
    def apply_jitter(self, text: str, intensity: float) -> str:
        """Horizontal displacement effect (from ascii.txt jitter)"""
        lines = text.split('\n')
        result = []
        for line in lines:
            if random.random() < intensity:
                offset = random.randint(-2, 2)
                if offset > 0:
                    line = ' ' * offset + line[:-offset] if len(line) > offset else line
                elif offset < 0:
                    line = line[-offset:] + ' ' * (-offset)
            result.append(line)
        return '\n'.join(result)
    
    def apply_vhs_distortion(self, text: str, intensity: float) -> str:
        """VHS vertical bar distortion (from glith.txt)"""
        lines = text.split('\n')
        result = []
        distort_start = random.randint(0, max(1, len(lines) - 3))
        distort_length = random.randint(1, 3)
        
        for i, line in enumerate(lines):
            if distort_start <= i < distort_start + distort_length and random.random() < intensity:
                shift = random.randint(-3, 3)
                if shift > 0:
                    line = ' ' * shift + line
                elif shift < 0:
                    line = line[-shift:]
            result.append(line)
        return '\n'.join(result)
    
    def apply_rgb_shift_simulation(self, intensity: float) -> tuple:
        """Simulate RGB shift by returning offset values for layered text"""
        if random.random() < intensity:
            return (random.randint(-2, 0), random.randint(0, 2))
        return (0, 0)
    
    def apply_block_glitch(self, text: str, intensity: float) -> str:
        """Random block replacement (from glith.txt glitchBlocks)"""
        if random.random() > intensity:
            return text
            
        lines = text.split('\n')
        if not lines:
            return text
            
        start_line = random.randint(0, max(0, len(lines) - 2))
        block_height = random.randint(1, 2)
        
        for i in range(start_line, min(start_line + block_height, len(lines))):
            if lines[i]:
                start_char = random.randint(0, max(0, len(lines[i]) - 4))
                block_width = random.randint(2, 6)
                line_list = list(lines[i])
                for j in range(start_char, min(start_char + block_width, len(line_list))):
                    if line_list[j] != ' ':
                        line_list[j] = random.choice(VHS_CHARS)
                lines[i] = ''.join(line_list)
        
        return '\n'.join(lines)
    
    def get_glitched_frame(
        self,
        base_text: str,
        intensity_multiplier: float = 1.0,
        positions: Optional[list[int]] = None,
        base_chars: Optional[list] = None,
    ) -> str:
        """Apply all glitch effects for one frame"""
        result = base_text
        
        if random.random() < 0.4 * intensity_multiplier:
            result = self.apply_noise(result, self.noise_intensity * intensity_multiplier, positions, base_chars)
        
        if random.random() < 0.25 * intensity_multiplier:
            result = self.apply_jitter(result, self.jitter_intensity * intensity_multiplier)
        
        if random.random() < 0.15 * intensity_multiplier:
            result = self.apply_vhs_distortion(result, 0.5 * intensity_multiplier)
        
        if random.random() < 0.1 * intensity_multiplier:
            result = self.apply_block_glitch(result, 0.3 * intensity_multiplier)
        
        self.time += 0.05
        return result

class SplashScreen(ft.Container):
    """Splash screen with animated ASCII lock and glitch effects"""
    
    def __init__(self, on_complete: Optional[Callable] = None):
        self.on_complete = on_complete
        self.glitch_engine = GlitchEngine()
        self.max_glitch_frames = 30
        self.transition_frames = 20
        self.frame_delay = 1 / 30
        self._is_mounted = False
        self._animation_done = False
        self._open_positions = _non_space_positions(LOCK_OPEN)
        self._closed_positions = _non_space_positions(LOCK_CLOSED)
        self._open_chars = _LOCK_OPEN_CHARS
        self._closed_chars = _LOCK_CLOSED_CHARS
        
        self.ascii_text = ft.Text(
            value=LOCK_OPEN,
            font_family="Consolas",
            size=8,
            color=get_text_main(),
            text_align=ft.TextAlign.LEFT,
        )
        
        self.red_layer = ft.Text(
            value="",
            font_family="Consolas",
            size=8,
            color="#ff000033",
            text_align=ft.TextAlign.LEFT,
        )
        
        self.blue_layer = ft.Text(
            value="",
            font_family="Consolas",
            size=8,
            color="#0000ff33",
            text_align=ft.TextAlign.LEFT,
        )
        
        self.title_text = ft.Text(
            value="SPIRITBYTE",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=get_text_main(),
            opacity=0,
            animate_opacity=ft.Animation(450, ft.AnimationCurve.EASE_OUT),
        )
        
        super().__init__(
            content=ft.Stack(
                controls=[
                    ft.Container(expand=True, bgcolor="#0a0a0a"),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Stack(
                                    controls=[self.red_layer, self.blue_layer, self.ascii_text],
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Container(height=20),
                                self.title_text,
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            expand=True,
            bgcolor="#0a0a0a",
        )
    
    def did_mount(self):
        """Called when control is added to page"""
        self._is_mounted = True
        self.page.run_task(self._run_animation)
            
    def will_unmount(self):
        """Called when control is removed"""
        self._is_mounted = False

    async def _render_frame(
        self,
        base_text: str,
        intensity: float,
        positions: list[int],
        show_layers: bool,
        force_layers: bool = False,
        base_chars: Optional[list] = None,
    ) -> bool:
        if not self._is_mounted:
            return False
        glitched = self.glitch_engine.get_glitched_frame(base_text, intensity, positions, base_chars)
        self.ascii_text.value = glitched

        if show_layers:
            r_off, b_off = self.glitch_engine.apply_rgb_shift_simulation(0.3)
            show = force_layers or r_off or b_off
            self.red_layer.value = glitched if show else ""
            self.blue_layer.value = glitched if show else ""
        else:
            self.red_layer.value = ""
            self.blue_layer.value = ""

        try:
            self.update()
        except Exception:
            return False
            
        await asyncio.sleep(self.frame_delay)
        return True

    async def _run_animation(self):
        """Main animation loop"""
        try:
            for _ in range(self.max_glitch_frames):
                if not await self._render_frame(LOCK_OPEN, 1.0, self._open_positions, True,
                                                base_chars=self._open_chars):
                    return
            
            for i in range(self.transition_frames):
                intensity = 1.5 + (i / self.transition_frames)
                base = LOCK_CLOSED if i > self.transition_frames // 2 else LOCK_OPEN
                positions = self._closed_positions if base == LOCK_CLOSED else self._open_positions
                chars = self._closed_chars if base == LOCK_CLOSED else self._open_chars
                if not await self._render_frame(base, intensity, positions, True,
                                                force_layers=True, base_chars=chars):
                    return
            
            for i in range(15):
                intensity = 1.0 - (i / 15) * 0.8
                show_layers = intensity >= 0.3
                if not await self._render_frame(
                    LOCK_CLOSED,
                    intensity,
                    self._closed_positions,
                    show_layers,
                    base_chars=self._closed_chars,
                ):
                    return
            
            if not self._is_mounted:
                return
            self.ascii_text.value = LOCK_CLOSED
            self.red_layer.value = ""
            self.blue_layer.value = ""
            self.update()
            
            if not self._is_mounted:
                return
            self.title_text.opacity = 1
            self.update()
            await asyncio.sleep(0.5)
            
            await asyncio.sleep(0.8)
            
            if not self._animation_done and self.on_complete:
                self._animation_done = True
                try:
                    self.on_complete()
                except Exception as e:
                    print(f"[SPLASH] Navigation callback error: {e}")
                    import traceback
                    traceback.print_exc()
                
        except Exception as e:
            print(f"[SPLASH] Animation error: {e}")
            import traceback
            traceback.print_exc()