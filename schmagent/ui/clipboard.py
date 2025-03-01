# schmagent/ui/clipboard.py

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class ClipboardManager:
    """Manages clipboard interactions."""
    
    def __init__(self, config):
        """
        Initialize the clipboard manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.clipboard = Gdk.Display.get_default().get_clipboard()
        self.auto_clear = config.get("security", "clipboard_auto_clear", False)
        self.clear_delay = config.get("security", "clipboard_clear_delay", 60)
        self.clear_timer_id = None
    
    def get_text(self, callback: Callable[[Optional[str]], None]) -> None:
        """
        Get text from the clipboard asynchronously.
        
        Args:
            callback: Function to call with the clipboard text or None
        """
        self.clipboard.read_text_async(None, self._on_text_received, callback)
    
    def _on_text_received(self, clipboard, result, callback):
        """Handle clipboard text when received."""
        try:
            text = clipboard.read_text_finish(result)
            callback(text)
            
            # Set up auto-clear if enabled
            if self.auto_clear and text:
                self._schedule_clipboard_clear()
        except Exception as e:
            logger.error(f"Error reading clipboard: {str(e)}")
            callback(None)
    
    def set_text(self, text: str) -> None:
        """
        Set text to the clipboard.
        
        Args:
            text: Text to put in clipboard
        """
        self.clipboard.set_text(text)
        
        # Set up auto-clear if enabled
        if self.auto_clear:
            self._schedule_clipboard_clear()
    
    def _schedule_clipboard_clear(self) -> None:
        """Schedule clearing the clipboard after the configured delay."""
        # Cancel any existing timer
        if self.clear_timer_id:
            GLib.source_remove(self.clear_timer_id)
        
        # Set up new timer
        self.clear_timer_id = GLib.timeout_add_seconds(
            self.clear_delay, 
            self._clear_clipboard
        )
    
    def _clear_clipboard(self) -> bool:
        """Clear the clipboard content."""
        try:
            self.clipboard.set_text("")
            logger.debug("Clipboard automatically cleared")
            self.clear_timer_id = None
            return False  # Don't repeat
        except Exception as e:
            logger.error(f"Error clearing clipboard: {str(e)}")
            return False  # Don't repeat