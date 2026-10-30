import inspect
import traceback

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


def _register(module, default_display):
    """Use the module's own mappings if it has them, otherwise find node classes automatically."""
    if hasattr(module, "NODE_CLASS_MAPPINGS"):
        NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
        NODE_DISPLAY_NAME_MAPPINGS.update(getattr(module, "NODE_DISPLAY_NAME_MAPPINGS", {}))
        return
    found = [
        (name, cls) for name, cls in inspect.getmembers(module, inspect.isclass)
        if cls.__module__ == module.__name__ and hasattr(cls, "INPUT_TYPES") and hasattr(cls, "FUNCTION")
    ]
    for name, cls in found:
        NODE_CLASS_MAPPINGS[name] = cls
        NODE_DISPLAY_NAME_MAPPINGS[name] = default_display if len(found) == 1 else name
    print(f"[Style Atlas] registered from {module.__name__}: {[n for n, _ in found]}")


# --- Style Atlas ---
try:
    from . import style_atlas
    _register(style_atlas, "🎨 Style Atlas")
except Exception:
    print("[Style Atlas] Style Atlas node failed to load:")
    traceback.print_exc()

# --- Character Atlas ---
try:
    from . import character_atlas
    _register(character_atlas, "🧑 Character Atlas")
except Exception:
    print("[Style Atlas] Character Atlas node failed to load:")
    traceback.print_exc()

WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
