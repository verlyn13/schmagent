# schmagent/main.py
"""Main entry point for the Schmagent application."""

import sys
import asyncio
import logging
import signal
import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from .ui.window import SchmagentWindow
from .ui.clipboard import ClipboardManager
from .models.chat_model import Message
from .models.openai import OpenAIModel
from .utils.config import config

# Set up logging
logger = logging.getLogger(__name__)

# System prompt template
SYSTEM_PROMPT = """
You are Schmagent, a helpful desktop AI assistant integrated into the GNOME environment. 
Your purpose is to assist the user with various tasks by responding to clipboard text or screenshots they share with you.

## Your Capabilities
- Process text from the user's clipboard 
- Analyze screenshots when provided
- Answer questions and provide information
- Help with code, including debugging, explaining, and improving code snippets
- Assist with text composition, editing, and formatting
- Summarize content upon request
- Provide step-by-step guidance for technical tasks
- Maintain context within the current session

## Your Personality
- Professional but friendly
- Clear and concise in your responses
- Proactive in identifying the user's needs
- Helpful without being overwhelming
- Detail-oriented when precision matters
- Efficient with the user's time

## Response Guidelines
1. Be concise: Users are using you within their workflow, so prioritize brevity while maintaining clarity.
2. Format smartly: Use markdown formatting for readability
3. Context awareness: Remember the flow of the current session
4. When handling code: Provide explanations alongside solutions
5. With screenshots: Reference visual elements clearly

If you're uncertain about what the user wants, ask for clarification rather than making assumptions.
"""

class SchmagentApplication(Adw.Application):
    """Main application class for Schmagent."""
    
    def __init__(self):
        """Initialize the application."""
        print("SchmagentApplication.__init__ called")
        super().__init__(
            application_id="org.gnome.Schmagent",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        
        # Set up logging based on configuration
        log_level_str = config.get("app", "log_level", "INFO")
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Set DEBUG level for our specific modules
        logging.getLogger("schmagent.ui.window").setLevel(logging.DEBUG)
        logging.getLogger("schmagent.ui.clipboard").setLevel(logging.DEBUG)
        
        # Initialize properties
        self.window = None
        self.chat_model = None
        
        # Initialize clipboard manager
        try:
            print("Attempting to initialize clipboard manager")
            self.clipboard_manager = ClipboardManager(config)
            if self.clipboard_manager:
                print(f"Clipboard manager initialized successfully: {self.clipboard_manager}")
            else:
                print("Clipboard manager is None after initialization")
        except Exception as e:
            print(f"Failed to initialize clipboard manager: {str(e)}")
            self.clipboard_manager = None
        
        # Connect signals
        self.connect("activate", self.on_activate)
        
        # Set up asyncio integration with GTK's main loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        logger.info("Schmagent application initialized")
    
    def on_activate(self, app):
        """Handle application activation."""
        # Initialize the chat model
        self.initialize_chat_model()
        
        # Create the main window
        self.window = SchmagentWindow(self)
        self.window.set_chat_model(self.chat_model)
        
        # Set the clipboard manager
        if self.clipboard_manager:
            print(f"Setting clipboard manager in window: {self.clipboard_manager}")
            self.window.set_clipboard_manager(self.clipboard_manager)
            print("Clipboard manager set in window")
        else:
            print("Clipboard manager is None, cannot set in window")
        self.window.present()
        
        logger.info("Schmagent window created and presented")
    
    def initialize_chat_model(self):
        """Initialize the chat model based on configuration."""
        provider = config.get("model", "default", "openai")
        
        # For now, we only implement OpenAI
        if provider == "openai":
            self.chat_model = OpenAIModel(config)
        else:
            logger.warning(f"Provider {provider} not implemented yet, falling back to OpenAI")
            self.chat_model = OpenAIModel(config)
        
        # Set the system prompt
        self.chat_model.set_system_prompt(SYSTEM_PROMPT)
        
        logger.info(f"Chat model initialized: {provider}")

def main():
    """Main entry point for the application."""
    # Handle keyboard interrupts gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    # Initialize and run the application
    app = SchmagentApplication()
    
    # Run the application with the event loop
    try:
        return app.run(sys.argv)
    finally:
        # Clean up the event loop when the application exits
        if hasattr(app, 'loop') and app.loop.is_running():
            app.loop.close()

if __name__ == "__main__":
    sys.exit(main())
