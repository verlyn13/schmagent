# schmagent/ui/window.py

# Type checking comments for linters
# type: ignore
# pyright: reportMissingImports=false
# pylint: disable=import-error,no-name-in-module
import gi  # type: ignore
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk, Gio  # type: ignore
import logging
import asyncio
from typing import Optional, List

from ..models.chat_model import Message
from ..utils.config import config

logger = logging.getLogger(__name__)

class SchmagentWindow(Adw.ApplicationWindow):
    """Main application window for Schmagent."""
    
    def __init__(self, app, **kwargs):
        """Initialize the main window."""
        super().__init__(
            application=app,
            default_width=config.get("ui", "window_width", 800),
            default_height=config.get("ui", "window_height", 600),
            title=config.get("app", "name", "Schmagent"),
            **kwargs
        )
        
        self.chat_model = None  # Will be set by the application
        self.clipboard_manager = None  # Will be set by the application
        self.messages = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface components."""
        # Main layout box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)
        
        # Add a header bar with title
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Message display area (scrollable)
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        
        # Message list box
        self.message_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        scrolled_window.set_child(self.message_box)
        main_box.append(scrolled_window)
        
        # Input area
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        input_box.set_margin_top(10)
        
        # Text input
        self.text_input = Gtk.TextView()
        self.text_input.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_input.set_vexpand(False)
        self.text_input.set_size_request(-1, 80)
        
        # Get the TextBuffer
        self.buffer = self.text_input.get_buffer()
        
        # Create a ScrolledWindow for the TextView
        input_scroll = Gtk.ScrolledWindow()
        input_scroll.set_hexpand(True)
        input_scroll.set_child(self.text_input)
        input_box.append(input_scroll)
        
        # Paste from clipboard button
        self.paste_button = Gtk.Button(label="Paste")
        self.paste_button.set_tooltip_text("Paste from clipboard")
        self.paste_button.connect("clicked", self.on_paste_clicked)
        input_box.append(self.paste_button)
        
        # Send button
        self.send_button = Gtk.Button(label="Send")
        self.send_button.connect("clicked", self.on_send_clicked)
        input_box.append(self.send_button)
        
        main_box.append(input_box)
        
        # Set the main box as the content of the window
        self.set_content(main_box)
        
        # Connect key press event
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.text_input.add_controller(key_controller)
    
    def on_paste_clicked(self, button):
        """Handle the paste button click event."""
        print(f"Paste button clicked, clipboard_manager: {getattr(self, 'clipboard_manager', None)}")
        
        if not hasattr(self, 'clipboard_manager') or self.clipboard_manager is None:
            print("No clipboard manager available")
            logger.warning("No clipboard manager available")
            self.show_toast("Clipboard manager not available")
            return
            
        # Use the clipboard manager to get text
        self.clipboard_manager.get_text(self._handle_clipboard_text)
        logger.debug("Manual clipboard paste requested")
    
    def _handle_clipboard_text(self, text):
        """Handle text received from clipboard manager."""
        if text:
            # Set the text in the input buffer
            self.buffer.set_text(text, -1)
            logger.debug("Clipboard content pasted into input")
        else:
            # Show a message if no text was available
            logger.debug("No text content in clipboard")
            self.show_toast("No text found in clipboard")
    
    def show_toast(self, message):
        """Show a toast notification with the given message."""
        # In GTK4/libadwaita, we need to create a toast and show it
        # Since we don't have a toast overlay, we'll just log the message
        # and show it in the message area as a system message
        logger.info(f"Toast message: {message}")
        
        # Add a temporary message to the UI
        message_frame = Adw.PreferencesGroup()
        message_frame.set_title("System")
        
        message_label = Gtk.Label()
        message_label.set_markup(f"<i>{message}</i>")
        message_label.set_wrap(True)
        message_label.set_xalign(0)
        
        message_frame.add(message_label)
        self.message_box.append(message_frame)
        self.scroll_to_bottom()
        
        # Remove the message after a few seconds
        GLib.timeout_add_seconds(3, lambda: self._remove_toast_message(message_frame))
    
    def _remove_toast_message(self, message_frame):
        """Remove a toast message from the UI."""
        if message_frame in self.message_box:
            self.message_box.remove(message_frame)
        return False  # Don't repeat
    
    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press events in the text input."""
        # Check for Ctrl+Enter to send
        if keyval == Gdk.KEY_Return and (state & Gdk.ModifierType.CONTROL_MASK):
            self.on_send_clicked(None)
            return True
        return False
    
    def on_send_clicked(self, button):
        """Handle the send button click event."""
        # Get the text from the input
        start, end = self.buffer.get_bounds()
        text = self.buffer.get_text(start, end, False)
        
        if not text.strip():
            return
        
        # Add user message to UI
        self.add_message_to_ui("user", text)
        
        # Clear the input
        self.buffer.set_text("", 0)
        
        # Create a message object
        user_message = Message("user", text)
        self.messages.append(user_message)
        
        # Generate a response asynchronously
        self.send_button.set_sensitive(False)
        self.add_thinking_indicator()
        
        # Use GLib to run the async function properly in GTK's main loop
        asyncio.get_event_loop().create_task(self.get_model_response([user_message]))
    
    async def get_model_response(self, messages):
        """Get a response from the model asynchronously."""
        try:
            if not self.chat_model:
                GLib.idle_add(self.remove_thinking_indicator)
                GLib.idle_add(lambda: self.add_message_to_ui("assistant", "Error: No AI model configured."))
                GLib.idle_add(lambda: self.send_button.set_sensitive(True))
                return
            
            # Add a timeout to prevent hanging
            response = await asyncio.wait_for(
                self.chat_model.generate_response(messages),
                timeout=30  # 30 second timeout
            )
            
            # Update UI with response
            GLib.idle_add(self.remove_thinking_indicator)
            GLib.idle_add(lambda: self.add_message_to_ui("assistant", response))
            GLib.idle_add(lambda: self.send_button.set_sensitive(True))
            
            # Add to message history
            self.messages.append(Message("assistant", response))
            
        except asyncio.TimeoutError:
            logger.warning("Model response timed out")
            GLib.idle_add(self.remove_thinking_indicator)
            GLib.idle_add(lambda: self.add_message_to_ui("assistant", "Error: Request timed out. Please try again."))
            GLib.idle_add(lambda: self.send_button.set_sensitive(True))
        except Exception as e:
            logger.error(f"Error in model response: {str(e)}")
            GLib.idle_add(self.remove_thinking_indicator)
            GLib.idle_add(lambda: self.add_message_to_ui("assistant", f"Error: {str(e)}"))
            GLib.idle_add(lambda: self.send_button.set_sensitive(True))
    
    def add_message_to_ui(self, role, content):
        """Add a message to the UI."""
        # Create message container
        message_frame = Adw.PreferencesGroup()
        
        # Set up styling based on role
        if role == "user":
            message_frame.set_title("You")
        elif role == "assistant":
            message_frame.set_title("Schmagent")
        else:
            message_frame.set_title(role.capitalize())
        
        # Create a label for the content with markup
        content_label = Gtk.Label()
        content_label.set_markup(content)
        content_label.set_wrap(True)
        content_label.set_xalign(0)  # Align text to the left
        content_label.set_selectable(True)
        
        # Add label to the frame
        message_frame.add(content_label)
        
        # Add the message to the message box
        self.message_box.append(message_frame)
        
        # Scroll to the bottom
        self.scroll_to_bottom()
    
    def add_thinking_indicator(self):
        """Add a thinking indicator while waiting for a response."""
        self.thinking_frame = Adw.PreferencesGroup()
        self.thinking_frame.set_title("Schmagent")
        
        thinking_label = Gtk.Label()
        thinking_label.set_markup("<i>Thinking...</i>")
        thinking_label.set_xalign(0)
        
        self.thinking_frame.add(thinking_label)
        self.message_box.append(self.thinking_frame)
        self.scroll_to_bottom()
    
    def remove_thinking_indicator(self):
        """Remove the thinking indicator."""
        if hasattr(self, 'thinking_frame'):
            self.message_box.remove(self.thinking_frame)
            delattr(self, 'thinking_frame')
    
    def scroll_to_bottom(self):
        """Scroll the message area to the bottom."""
        # Enqueue this for after rendering
        GLib.idle_add(self._do_scroll_to_bottom)
    
    def _do_scroll_to_bottom(self):
        """Actually perform the scroll (called by idle_add)."""
        parent = self.message_box.get_parent()
        if isinstance(parent, Gtk.ScrolledWindow):
            adj = parent.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())
        return False  # Don't call again
    
    def set_chat_model(self, model):
        """Set the chat model to use for generating responses."""
        self.chat_model = model
        logger.info(f"Chat model set to: {model.provider_name}")
        
    def set_clipboard_manager(self, manager):
        """Set the clipboard manager to use for clipboard operations."""
        print(f"SchmagentWindow.set_clipboard_manager called with manager: {manager}")
        self.clipboard_manager = manager
        print(f"SchmagentWindow.clipboard_manager set to: {self.clipboard_manager}")
        logger.debug("Clipboard manager set")
