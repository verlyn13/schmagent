"""Type stubs for PyGObject (gi module)"""

def require_version(namespace: str, version: str) -> None:
    """Specify a version to be used for a namespace."""
    ...

class repository:
    """Repository of GObject introspection information."""
    
    class Gtk:
        """GTK namespace."""
        ...
    
    class Adw:
        """Adwaita namespace."""
        ...
    
    class GLib:
        """GLib namespace."""
        ...
    
    class Gdk:
        """GDK namespace."""
        ...
    
    class Gio:
        """GIO namespace."""
        ... 