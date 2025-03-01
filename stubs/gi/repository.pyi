"""Type stubs for gi.repository module."""
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, overload

# GTK namespace
class Gtk:
    """GTK namespace."""
    
    class Application:
        """GTK Application class."""
        ...
    
    class Widget:
        """GTK Widget class."""
        ...
    
    class Window:
        """GTK Window class."""
        ...
    
    class Box:
        """GTK Box class."""
        ...
    
    class Button:
        """GTK Button class."""
        ...
    
    class Label:
        """GTK Label class."""
        ...
    
    class Entry:
        """GTK Entry class."""
        ...
    
    class TextView:
        """GTK TextView class."""
        ...
    
    class TextBuffer:
        """GTK TextBuffer class."""
        ...
    
    class ScrolledWindow:
        """GTK ScrolledWindow class."""
        ...
    
    class HeaderBar:
        """GTK HeaderBar class."""
        ...
    
    class Orientation:
        """GTK Orientation enum."""
        HORIZONTAL: int
        VERTICAL: int
    
    class Align:
        """GTK Align enum."""
        START: int
        END: int
        CENTER: int
        FILL: int
    
    class PolicyType:
        """GTK PolicyType enum."""
        ALWAYS: int
        AUTOMATIC: int
        NEVER: int
    
    # Add more GTK classes and enums as needed

# Adwaita namespace
class Adw:
    """Adwaita namespace."""
    
    class Application:
        """Adwaita Application class."""
        def __init__(self, application_id: str, flags: Any) -> None: ...
        def connect(self, signal: str, callback: Callable[..., Any]) -> int: ...
        def run(self, argv: List[str]) -> int: ...
    
    class ApplicationWindow:
        """Adwaita ApplicationWindow class."""
        def __init__(self, application: Any = None, default_width: int = 0, default_height: int = 0, title: str = "", **kwargs: Any) -> None: ...
        def present(self) -> None: ...
        def set_default_size(self, width: int, height: int) -> None: ...
        def set_content(self, content: Any) -> None: ...
    
    class HeaderBar:
        """Adwaita HeaderBar class."""
        ...
    
    class Window:
        """Adwaita Window class."""
        def present(self) -> None: ...
        def set_default_size(self, width: int, height: int) -> None: ...
    
    # Add more Adwaita classes as needed

# GLib namespace
class GLib:
    """GLib namespace."""
    
    @staticmethod
    def timeout_add_seconds(interval: int, function: Callable[[], bool], *data: Any) -> int: ...
    
    @staticmethod
    def source_remove(source_id: int) -> bool: ...
    
    # Add more GLib functions and classes as needed

# GDK namespace
class Gdk:
    """GDK namespace."""
    
    class Display:
        """GDK Display class."""
        
        @staticmethod
        def get_default() -> "Gdk.Display": ...
        
        def get_clipboard(self) -> "Gdk.Clipboard": ...
    
    class Clipboard:
        """GDK Clipboard class."""
        
        def set_text(self, text: str) -> None: ...
        def read_text_async(self, cancellable: Optional[Any], callback: Callable[..., Any], user_data: Any) -> None: ...
        def read_text_finish(self, result: Any) -> Optional[str]: ...
    
    # Add more GDK classes as needed

# GIO namespace
class Gio:
    """GIO namespace."""
    
    class ApplicationFlags:
        """GIO ApplicationFlags enum."""
        FLAGS_NONE: int
    
    # Add more GIO classes and enums as needed
