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
        
        # Load clipboard content
        self.load_clipboard_content()
    
    def load_clipboard_content(self):
        """Load content from the clipboard into the text input."""
        try:
            # Get the clipboard from the current display
            clipboard = Gdk.Display.get_default().get_clipboard()
            
            # Create a cancellable object to allow cancelling the operation if needed
            cancellable = Gio.Cancellable()
            self.clipboard_cancellable = cancellable  # Store for potential later cancellation
            
            # Request text from clipboard with proper cancellable and user_data
            # Note: passing self as user_data to access it in the callback
            clipboard.read_text_async(cancellable, self.on_clipboard_text_received, self)
            
            logger.debug("Clipboard read request initiated")
        except Exception as e:
            logger.debug(f"Could not initiate clipboard access: {str(e)}")
    
    def on_clipboard_text_received(self, clipboard, result, user_data):
        """Handle clipboard text when received.
        
        This follows the GAsyncReadyCallback signature from GLib:
        callback(source_object, result, user_data)
        """
        try:
            # The proper way to finish the async operation and get the text
            text = clipboard.read_text_finish(result)
            
            if text:
                self.buffer.set_text(text, -1)
                logger.debug("Clipboard content loaded into input")
            else:
                # This is not an error - just means clipboard had no text content
                logger.debug("Clipboard contained no text content")
                
        except GLib.Error as e:
            # Handle specific GLib errors properly
            if e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                # This is expected if we cancelled the operation
                logger.debug("Clipboard operation was cancelled")
            elif "Cannot read from empty clipboard" in str(e):
                # This is a common error in Wayland when clipboard is inaccessible
                logger.debug(f"Clipboard access issue: {str(e)}")
                
                # Consider implementing a fallback method here
                self._try_clipboard_fallback()
            else:
                # Real errors should be logged appropriately
                logger.warning(f"Error reading clipboard: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error reading clipboard: {str(e)}")

    def _try_clipboard_fallback(self):
        """Try alternative approaches to get clipboard content."""
        try:
            # Try the primary selection instead (highlighted text)
            primary = Gdk.Display.get_default().get_primary_clipboard()
            primary.read_text_async(None, self._on_primary_text_received, self)
            logger.debug("Trying primary selection as fallback")
        except Exception as e:
            logger.debug(f"Primary selection fallback failed: {str(e)}")

    def _on_primary_text_received(self, clipboard, result, user_data):
        """Handle text from primary selection clipboard."""
        try:
            text = clipboard.read_text_finish(result)
            if text:
                self.buffer.set_text(text, -1)
                logger.debug("Primary selection content loaded into input")
            else:
                logger.debug("No text in primary selection")
        except Exception as e:
            logger.debug(f"Error reading primary selection: {str(e)}")
    
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