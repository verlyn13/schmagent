# schmagent/ui/clipboard.py

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib, Gio
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
        print(f"ClipboardManager.get_text called with callback: {callback}")
        try:
            # Create a cancellable object to allow cancelling the operation if needed
            cancellable = None  # Gio.Cancellable() - not needed for simple operations
            
            # Request text from clipboard with proper cancellable and user_data
            print(f"Calling read_text_async on clipboard: {self.clipboard}")
            self.clipboard.read_text_async(cancellable, self._on_text_received, callback)
            print("Clipboard read request initiated")
            logger.debug("Clipboard read request initiated")
        except Exception as e:
            print(f"Could not initiate clipboard access: {str(e)}")
            logger.error(f"Could not initiate clipboard access: {str(e)}")
            callback(None)
    
    def _on_text_received(self, clipboard, result, callback):
        """Handle clipboard text when received."""
        print(f"ClipboardManager._on_text_received called with result: {result}")
        try:
            # The proper way to finish the async operation and get the text
            text = clipboard.read_text_finish(result)
            print(f"Clipboard text received: {text}")
            
            if text:
                logger.debug("Clipboard text received successfully")
                callback(text)
                
                # Set up auto-clear if enabled
                if self.auto_clear:
                    self._schedule_clipboard_clear()
            else:
                # This is not an error - just means clipboard had no text content
                print("Clipboard contained no text content")
                logger.debug("Clipboard contained no text content")
                callback(None)
                
        except Exception as e:
            # Handle specific errors
            print(f"Error reading clipboard: {str(e)}")
            if "Cannot read from empty clipboard" in str(e):
                # This is a common error in Wayland when clipboard is inaccessible
                print(f"Clipboard access issue: {str(e)}")
                logger.debug(f"Clipboard access issue: {str(e)}")
                self._try_clipboard_fallback(callback)
            else:
                # Real errors should be logged appropriately
                logger.error(f"Error reading clipboard: {str(e)}")
                callback(None)
    
    def _try_clipboard_fallback(self, callback):
        """Try alternative approaches to get clipboard content."""
        try:
            # In GTK4, the primary selection might not be directly accessible through Python bindings
            # Let's try a different approach by using the regular clipboard again
            logger.debug("Trying alternative clipboard access methods")
            
            # Get the default display
            display = Gdk.Display.get_default()
            
            # Try to get the clipboard again - sometimes a second attempt works
            try:
                # Get the regular clipboard again
                clipboard = display.get_clipboard()
                clipboard.read_text_async(None, self._on_primary_text_received, callback)
                logger.debug("Retrying with regular clipboard")
            except Exception as e:
                logger.debug(f"Regular clipboard retry failed: {str(e)}")
                
                # If all else fails, inform the user
                logger.debug("All clipboard access methods failed")
                callback(None)
        except Exception as e:
            logger.debug(f"Primary selection fallback failed: {str(e)}")
            callback(None)
    
    def _on_primary_text_received(self, clipboard, result, callback):
        """Handle text from primary selection clipboard."""
        try:
            text = clipboard.read_text_finish(result)
            if text:
                logger.debug("Primary selection content received")
                callback(text)
            else:
                logger.debug("No text in primary selection")
                callback(None)
        except Exception as e:
            logger.debug(f"Error reading primary selection: {str(e)}")
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
