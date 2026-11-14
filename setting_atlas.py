"""
🏞️ Setting Atlas - decides WHERE the image happens, from setting_atlas_library.xlsx.
Sources: None (bypass) / Preset / Location / Simple Background / Studio / Known Location / Anime Setting
         / 🎲 Random (all sources).
Layers (all optional): Season & Weather, Lighting, Condition, Décor, Palette, Population, Frame.
"""
import random

try:
    from .atlas_core import (NONE, BYPASS, RANDOM, RANDOM_ALL, SEP, Options, clean, hier_label, pick, tidy,
                             load_workbook_dict, library_mtime, register_thumbs, expand_wildcards,
                             wildcard_signature, seed_input, section)
except ImportError:
    from atlas_core import (NONE, BYPASS, RANDOM, RANDOM_ALL, SEP, Options, clean, hier_label, pick, tidy,
                            load_workbook_dict, library_mtime, register_thumbs, expand_wildcards,
                            wildcard_signature, seed_input, section)

LIBRARY = "setting_atlas_library.xlsx"
NODE = "SettingAtlas"
# source label -> (widget, sheet, label columns)
SOURCES = {
    "Preset": ("preset", "Presets", ("Name",)),
    "Location": ("location", "Locations", ("Category", "Umbrella", "Item", "Variant")),
    "Simple Background": ("simple_background", "Simple_Backgrounds", ("Umbrella", "Item", "Variant")),
    "Studio": ("studio", "Studios", ("Umbrella", "Variant")),
    "Known Location": ("known_location", "Known_Locations", ("Franchise", "Location", "Variant")),
    "Anime Setting": ("anime_setting", "Anime_Specific", ("Setting",)),
}
LAYERS = [  # widget, sheet, label columns
    ("weather", "Season_Weather", ("Umbrella", "Variant")),
    ("lighting", "Lighting", ("Umbrella", "Variant")),
    ("condition", "Conditions", ("Umbrella", "Variant")),
    ("decor", "Decor", ("Umbrella", "Variant")),
    ("palette", "Palettes", ("Umbrella", "Variant")),
    ("frame", "Frames", ("Umbrella", "Frame")),
]
LAYER_ORDER = ["weather", "lighting", "condition", "decor", "palette", "population", "frame"]
ORDER = ["setting", "condition", "weather", "decor", "palette", "lighting", "population", "frame"]
SIMPLE_LAYERS = ("palette", "lighting", "frame")
FRAME_LAYOUT, FRAME_DENSITY = "Full Border", "Moderate"

HELP = """🏞️ Setting Atlas decides where the image happens.

• source: Preset, Location, Simple Background, Studio, Known Location, Anime Setting, or 🎲 Random (all sources). None (bypass) does nothing.
• LAYERS (optional): weather, lighting, condition, décor, palette, population, frame. Population is the only control that adds people. Simple backgrounds only use palette, lighting and frame.
• ADVANCED: Long / Short text, Natural sentences or Danbooru Tags, and where the setting goes in the prompt.
• __wildcards__ in the prompt are resolved here if no earlier node did it.
• seed: same seed, same place."""


def _lib():
    data, err = load_workbook_dict(LIBRARY)
    O = {}
    for src, (w, sheet, cols) in SOURCES.items():
        O[w] = Options([(hier_label(r, *cols), r) for r in data.get(sheet, [])],
                       group_random=len(cols) > 1)
    for w, sheet, cols in LAYERS:
        O[w] = Options([(hier_label(r, *cols), r) for r in data.get(sheet, [])])
    pop = [r for r in data.get("Population", []) if r.get("Level", "").lower() != "none"]
    O["population"] = Options([(r.get("Level"), r) for r in pop], group_random=False)
    layouts = {r.get("Layout"): r.get("Prompt", "") for r in data.get("Frame_Layouts", [])}
    densities = {r.get("Density"): r.get("Prompt", "") for r in data.get("Frame_Densities", [])}
    return O, err, layouts, densities


class SettingAtlas:
    DESCRIPTION = HELP

    @classmethod
    def INPUT_TYPES(cls):
        O, _, _, _ = _lib()
        req = {
            "prompt": ("STRING", {"multiline": True, "default": "",
                                  "tooltip": "Your prompt. __name__ is replaced by a random line of wildcards/name.txt"}),
            "source": ([BYPASS] + list(SOURCES.keys()) + [RANDOM_ALL], {
                "default": BYPASS, "tooltip": "None (bypass) = prompt passes through unchanged (wildcards are still resolved)."}),
        }
        for src, (w, _, _) in SOURCES.items():
            req[w] = (O[w].values,)
        req["section_layers"] = section(False)
        for w in LAYER_ORDER:
            req[w] = (O[w].values,)
        req["section_advanced"] = section(False)
        req["prompt_length"] = (["Long", "Short"],)
        req["prompt_format"] = (["Natural", "Tags"], {"tooltip": "Tags uses the Danbooru_Tag columns when they exist."})
        req["setting_position"] = (["Prompt, Setting", "Setting, Prompt", "Prompt, in Setting"],)
        req["seed"] = seed_input("Drives every 🎲 Random choice and every __wildcard__. Fixed seed = same place.")
        register_thumbs(NODE, {k: o.ids() for k, o in O.items()})
        return {"required": req}

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("prompt", "setting", "info")
    OUTPUT_TOOLTIPS = ("Full prompt with the setting in it.", "Only the setting text.",
                       "Every choice with its ID, the seed and any warning.")
    FUNCTION = "build"
    CATEGORY = "Style Atlas/Prompt"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return f"{library_mtime(LIBRARY)}:{wildcard_signature()}"

    def build(self, prompt="", source=BYPASS, seed=0, **k):
        prompt, wc_log = expand_wildcards(prompt or "", seed, "setting_prompt")
        source = clean(source)
        if source in (BYPASS, NONE, ""):
            return (prompt, "", "\n".join(["Setting Atlas: bypassed"] + wc_log))
        O, err, layouts, densities = _lib()
        if err:
            return (prompt, "", f"⚠ {err}")
        info = []
        forced = {}
        if source == RANDOM_ALL:
            available = [s_ for s_, (w, _, _) in SOURCES.items() if O[w].map]
            source = random.Random(f"{seed}:source").choice(available) if available else ""
            forced[SOURCES.get(source, ("",))[0]] = RANDOM
            info.append(f"random source → {source}")
        if source not in SOURCES:
            return (prompt, "", "\n".join(info + ["⚠ unknown source"] + wc_log))
        L = clean(k.get("prompt_length", "Long"))
        tags = clean(k.get("prompt_format", "Natural")) == "Tags"
        info.insert(0, f"source {source} · seed {seed} · {L}{' · Tags' if tags else ''}")
        seg = {}

        def text(row):
            if tags and row.get("Danbooru_Tag"):
                return row["Danbooru_Tag"]
            return pick(row, L)

        w = SOURCES[source][0]
        label, row = O[w].resolve(forced.get(w, k.get(w, NONE)), seed, w)
        if not row:
            return (prompt, "", "\n".join(info + ["⚠ nothing selected"] + wc_log))
        info.append(f"{w}: {label} [{row.get('ID', '')}]")
        seg["setting"] = text(row)
        simple = source == "Simple Background"
        for lw in LAYER_ORDER:
            if simple and lw not in SIMPLE_LAYERS:
                continue  # simple backgrounds: palette, lighting, frame only
            lab, r = O[lw].resolve(k.get(lw, NONE), seed, lw)
            if not r:
                continue
            info.append(f"{lw}: {lab} [{r.get('ID', '')}]")
            t = pick(r, L)
            if lw == "frame":
                t = (t.replace("{layout}", layouts.get(FRAME_LAYOUT, "") or "")
                      .replace("{density}", densities.get(FRAME_DENSITY, "") or ""))
            seg[lw] = tidy(t)
        setting = tidy(", ".join(tidy(seg[x]).rstrip(".") for x in ORDER if seg.get(x)))
        setting, wc2 = expand_wildcards(setting, seed, "setting_text")
        user = prompt.strip().rstrip(" ,")
        pos = clean(k.get("setting_position", "Prompt, Setting"))
        if not user:
            final = setting
        elif pos == "Setting, Prompt":
            final = f"{setting}. {user}" if not tags else f"{setting}, {user}"
        elif pos == "Prompt, in Setting" and not simple and not tags:
            final = f"{user.rstrip('.')}, in {setting}"
        else:
            final = f"{user} {setting[0].upper() + setting[1:]}." if user.endswith(".") and not tags \
                else f"{user}, {setting}"
        return (final, setting, "\n".join(info + wc_log + wc2))


NODE_CLASS_MAPPINGS = {NODE: SettingAtlas}
NODE_DISPLAY_NAME_MAPPINGS = {NODE: "🏞️ Setting Atlas"}
