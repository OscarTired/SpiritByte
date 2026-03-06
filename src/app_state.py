"""
SpiritByte - Global Application State (Singleton)
"""
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime
import threading

@dataclass
class AppState:
    """Global application state singleton"""
    
    is_authenticated: bool = False
    master_key: Optional[bytes] = None
    last_activity: Optional[datetime] = None
    
    auto_lock_minutes: int = 15
    
    background_image: Optional[str] = None
    background_opacity: float = 0.5
    
    _on_lock_callbacks: list = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    _instance: Optional["AppState"] = field(default=None, repr=False)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def check_auto_lock(self) -> bool:
        """Check if auto-lock should trigger"""
        if not self.is_authenticated or self.last_activity is None:
            return False
        
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        return elapsed >= (self.auto_lock_minutes * 60)
    
    def lock(self):
        """Lock the application"""
        with self._lock:
            self.is_authenticated = False
            self.master_key = None
            for callback in self._on_lock_callbacks:
                callback()
    
    def unlock(self, master_key: bytes):
        """Unlock the application with master key"""
        with self._lock:
            self.master_key = master_key
            self.is_authenticated = True
            self.update_activity()
    
    def on_lock(self, callback: Callable):
        """Register a callback for when app locks"""
        self._on_lock_callbacks.append(callback)
    
    def clear_sensitive_data(self):
        """Clear all sensitive data from memory"""
        self.master_key = None
        self.is_authenticated = False

state = AppState()
