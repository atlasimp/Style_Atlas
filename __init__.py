"""Style Atlas for ComfyUI - 🎨 Style Atlas · 🧑 Character Atlas · 🏞️ Setting Atlas."""
import os
import traceback

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "wildcards"), exist_ok=True)

for _name in ("style_atlas", "character_atlas", "setting_atlas"):
    try:
        _m = __import__(f"{__name__}.{_name}", fromlist=["NODE_CLASS_MAPPINGS"])
        NODE_CLASS_MAPPINGS.update(_m.NODE_CLASS_MAPPINGS)
        NODE_DISPLAY_NAME_MAPPINGS.update(_m.NODE_DISPLAY_NAME_MAPPINGS)
    except Exception:
        print(f"[Style Atlas] {_name} failed to load:")
        traceback.print_exc()

WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
