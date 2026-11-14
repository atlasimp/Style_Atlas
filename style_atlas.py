"""
🎨 Style Atlas - decides HOW the image looks: a rendering style (or a ★ preset) plus optional
modifiers (quality, genre, palette, composition x3), lighting and mood, from style_atlas_library.xlsx.

The node works on its own (Python only). js/style_atlas.js adds the linked filters, live counts and
collapsible sections; js/atlas_common.js adds the ❔ help; if any JS fails, the node still runs.
"""
import re
import random

try:
    from .atlas_core import (NONE, BYPASS, RANDOM, RANDOM_ALL, SEP, Options, clean, hier_label, pick,
                             load_workbook_dict, library_mtime, register_thumbs, expand_wildcards,
                             wildcard_signature, seed_input, section)
except ImportError:  # standalone tests
    from atlas_core import (NONE, BYPASS, RANDOM, RANDOM_ALL, SEP, Options, clean, hier_label, pick,
                            load_workbook_dict, library_mtime, register_thumbs, expand_wildcards,
                            wildcard_signature, seed_input, section)

LIBRARY = "style_atlas_library.xlsx"
NODE = "StyleAtlasNode"
ALL = "All"
STAR = "★ "
MODE_STYLE, MODE_PRESET, MODE_MODS = "Style", "★ Preset", "Modifiers only"
MODES = [BYPASS, MODE_STYLE, MODE_PRESET, MODE_MODS, RANDOM_ALL]
MODIFIER_CATEGORIES = ["Quality", "Genre", "Palette", "Composition"]
COMPOSITION_SLOTS = 3
VERSIONS = ["Short (fallback Long)", "Long (fallback Short)", "Short only", "Long only"]
REALISM = [ALL, "1", "2", "3", "4", "5"]
REALISM_MODE = ["Exact", "±1"]
SUBJECT_PREFIX = "subject: "
DEFAULT_SUBJECTS = ("Main",)
DEFAULT_POSITIONS = {
    "Prompt, style": "{prompt}, {style}",
    "Style, prompt": "{style}, {prompt}",
    "Style: style. Subject: prompt": "Style: {style} Subject: {prompt}",
    "Subject: prompt. Style: style": "Subject: {prompt}. Style: {style}",
    "Prompt. Style": "{prompt}. {style}",
    "Prompt, in the style of style": "{prompt}, in the style of {style}",
    "Prompt, rendered as style": "{prompt}, rendered as {style}",
    "Prompt + new line + style": "{prompt}\n{style}",
    "Style only": "{style}",
    "Custom template": None,
}

HELP = """🎨 Style Atlas decides how the image looks.

• mode: None (bypass) does nothing, Style picks a style, ★ Preset picks a ready-made combo, Modifiers only keeps just the quality / genre / palette / composition / lighting / mood layers, 🎲 Random (all sources) rolls a style or a preset.
• version: Short is lighter, Long is richer. Long suits Krea 2 well.
• FILTERS: tick one or more subjects (Main, Portrait & Character…), then narrow by era, realism, category. The counts show what is left.
• MODIFIERS / LOOK: optional layers on top of the style. "Group | 🎲 Random" rolls inside a group.
• ADVANCED: where the style goes in the prompt and whether style names are kept.
• Wildcards: __adjective__ in the prompt becomes a random line of wildcards/adjective.txt.
• seed: same seed, same result. info shows every choice with its ID."""


# --------------------------------------------------------------------------- library
def library():
    data, err = load_workbook_dict(LIBRARY)
    styles, mods = [], {c: [] for c in MODIFIER_CATEGORIES}
    for r in data.get("Styles", []):
        name = r.get("Style Name")
        short, long_ = r.get("Short Version", ""), r.get("Long Version", "")
        if not name or not (short or long_):
            continue
        try:
            real = int(float(r.get("Realism (1-5)") or r.get("Realism") or 3))
        except ValueError:
            real = 3
        d = dict(id=r.get("ID", ""), name=name, cat=r.get("Category", ""), sub=r.get("Subcategory", ""),
                 era=r.get("Era") or "Any", real=real, short=short, long=long_,
                 subject=r.get("Subject") or "Main", layer=r.get("Layer") or "Base Style")
        if d["layer"] == "Modifier":
            if d["cat"] in mods:
                mods[d["cat"]].append(d)
        else:
            styles.append(d)
    presets = [dict(id=r.get("ID", ""), name=r.get("Name", ""), short=r.get("Short_Prompt", ""),
                    long=r.get("Long_Prompt", "")) for r in data.get("Presets", []) if r.get("Name")]
    positions = {}
    for r in data.get("Style_Positions", []):
        p, t = r.get("Position"), r.get("Template", "")
        if p:
            positions[p] = None if p.lower().startswith("custom") else t.replace("\\n", "\n")
    subjects = sorted({r["subject"] for r in styles}, key=lambda x: (x != "Main", x))
    return dict(error=err, styles=styles, mods=mods, presets=presets, subjects=subjects,
                lighting=data.get("Lighting", []), moods=data.get("Moods", []),
                positions=positions or DEFAULT_POSITIONS)


def build_options(lib):
    """Modifier dropdowns: 'Subcategory | Name' (grouped random), plus Lighting and Mood."""
    opts = {}
    for c in MODIFIER_CATEGORIES:
        rows = sorted(lib["mods"][c], key=lambda d: d["sub"])
        entries = [(f"{d['sub']}{SEP}{d['name']}" if d["sub"] else d["name"], dict(d, ID=d["id"])) for d in rows]
        opts[c] = Options(entries)
    for key, rows in (("Lighting", lib["lighting"]), ("Mood", lib["moods"])):
        entries = [(hier_label(r, "Umbrella", "Variant"), r) for r in rows]
        opts[key] = Options(entries)
    return opts


def mod_key(cat):
    return re.sub(r"[^a-z0-9]+", "_", cat.lower()).strip("_")


def comp_keys():
    return [f"composition_{i}" for i in range(1, COMPOSITION_SLOTS + 1)]


def public_data():
    lib = library()
    return {
        "error": lib["error"],
        "subjects": lib["subjects"],
        "presets": [STAR + p["name"] for p in lib["presets"]],
        "rows": [dict(n=r["name"], c=r["cat"], s=r["sub"], j=r["subject"], e=r["era"], r=r["real"],
                      hs=1 if r["short"] else 0, hl=1 if r["long"] else 0) for r in lib["styles"]],
    }


# --------------------------------------------------------------------------- helpers
def version_ok(r, version):
    if version == "Short only":
        return bool(r["short"])
    if version == "Long only":
        return bool(r["long"])
    return True


def pick_text(r, version):
    if version.startswith("Long"):
        return r["long"] or ("" if version == "Long only" else r["short"])
    return r["short"] or ("" if version == "Short only" else r["long"])


def realism_ok(r, realism, mode):
    if realism == ALL:
        return True
    t = int(realism)
    return r["real"] == t if mode == "Exact" else abs(r["real"] - t) <= 1


def strip_name(text):
    head, sep, tail = text.partition(":")
    return tail.strip() if sep and len(head) <= 80 else text


def finish(text):
    text = (text or "").strip()
    return text if not text or text[-1] in ".!?" else text + "."


def ticked_subjects(lib, kw):
    """Subjects whose checkbox is on. Nothing ticked = every subject (never an empty pool)."""
    on = [s for s in lib["subjects"] if kw.get(SUBJECT_PREFIX + s, s in DEFAULT_SUBJECTS)]
    return on or list(lib["subjects"])


# --------------------------------------------------------------------------- node
class StyleAtlasNode:
    DESCRIPTION = HELP

    @classmethod
    def INPUT_TYPES(cls):
        lib = library()
        base = lib["styles"]
        opts = build_options(lib)
        cats = [ALL] + list(dict.fromkeys(r["cat"] for r in base))
        subs = [ALL] + sorted({r["sub"] for r in base if r["sub"]})
        eras = [ALL] + sorted({r["era"] for r in base if r["era"]})
        presets = [RANDOM] + [STAR + p["name"] for p in lib["presets"]]
        styles = [RANDOM] + sorted(r["name"] for r in base)
        req = {
            "prompt": ("STRING", {"multiline": True, "default": "",
                                  "tooltip": "Your prompt. __name__ is replaced by a random line of wildcards/name.txt"}),
            "mode": (MODES, {"default": BYPASS,
                             "tooltip": "None (bypass) = prompt passes through unchanged (wildcards are still resolved)."}),
            "style": (styles, {"tooltip": "Filtered by the FILTERS section. 🎲 Random = random style from the filtered list."}),
            "preset": (presets, {"tooltip": "★ ready-made style combos from the Presets sheet."}),
            "version": (VERSIONS, {"default": VERSIONS[1]}),
            "section_filters": section(False),
        }
        for s_ in lib["subjects"]:
            req[SUBJECT_PREFIX + s_] = ("BOOLEAN", {"default": s_ in DEFAULT_SUBJECTS,
                                                    "tooltip": f"Include '{s_}' styles. Tick several to mix them."})
        req.update({
            "era": (eras,),
            "realism": (REALISM,),
            "realism_mode": (REALISM_MODE,),
            "category": (cats,),
            "subcategory": (subs,),
            "section_modifiers": section(False),
        })
        for c in MODIFIER_CATEGORIES:
            if c == "Composition":
                for k in comp_keys():
                    req[k] = (opts[c].values,)
            else:
                req[mod_key(c)] = (opts[c].values,)
        req["section_look"] = section(False)
        req["lighting"] = (opts["Lighting"].values,)
        req["mood"] = (opts["Mood"].values,)
        req["section_advanced"] = section(False)
        req["style_position"] = (list(lib["positions"].keys()),)
        req["include_style_names"] = ("BOOLEAN", {"default": True,
                                                  "tooltip": "Keep the 'Style Name:' prefix of each entry."})
        req["custom_template"] = ("STRING", {
            "multiline": False, "default": "{prompt}, {style}",
            "tooltip": "Used when style_position = Custom template. Placeholders: {prompt} {style} {modifiers} {lighting} {mood}"})
        req["seed"] = seed_input()

        # thumbnails: widget -> {label: ID}
        tm = {"style": {r["name"]: r["id"] for r in base if r["id"]},
              "preset": {STAR + p["name"]: p["id"] for p in lib["presets"] if p["id"]}}
        for c in MODIFIER_CATEGORIES:
            keys = comp_keys() if c == "Composition" else [mod_key(c)]
            for k in keys:
                tm[k] = opts[c].ids()
        tm["lighting"] = opts["Lighting"].ids()
        tm["mood"] = opts["Mood"].ids()
        register_thumbs(NODE, tm)
        return {"required": req}

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("prompt", "style_text", "info")
    OUTPUT_TOOLTIPS = ("Full prompt with the style placed in it.", "Only the style text this node added.",
                       "Every choice with its ID, the seed and any warning.")
    FUNCTION = "build"
    CATEGORY = "Style Atlas/Prompt"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        # Dropdown labels carry live counts from the JS; values are cleaned in build().
        return True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return f"{library_mtime(LIBRARY)}:{wildcard_signature()}"

    def build(self, prompt="", mode=BYPASS, seed=0, version=VERSIONS[1], style=RANDOM, preset=RANDOM,
              era=ALL, realism=ALL, realism_mode="Exact", category=ALL, subcategory=ALL,
              style_position="Prompt, style", include_style_names=True, custom_template="{prompt}, {style}", **kw):
        prompt, wc_log = expand_wildcards(prompt or "", seed, "style_prompt")
        mode = clean(mode)
        if mode in (BYPASS, NONE, ""):
            return (prompt, "", "\n".join(["Style Atlas: bypassed"] + wc_log))
        lib = library()
        if lib["error"] and not lib["styles"]:
            return (prompt, "", f"⚠ {lib['error']}")
        version = clean(version)
        realism, era = clean(realism), clean(era)
        category, subcategory = clean(category), clean(subcategory)
        style, preset = clean(style), clean(preset)
        rng = random.Random(seed)
        info, parts = [], []
        L = "Long" if version.startswith("Long") else "Short"
        subjects = ticked_subjects(lib, kw)

        pool = [r for r in lib["styles"]
                if r["subject"] in subjects
                and realism_ok(r, realism, realism_mode)
                and (era == ALL or r["era"] == era)
                and (category == ALL or r["cat"] == category)
                and (subcategory == ALL or r["sub"] == subcategory)
                and version_ok(r, version)]

        # ---- 🎲 Random (all sources): one draw over the filtered styles + every preset
        if mode == RANDOM_ALL:
            n_styles = len(pool)
            k = rng.randrange(n_styles + len(lib["presets"])) if (n_styles + len(lib["presets"])) else -1
            if 0 <= k < n_styles:
                mode, style = MODE_STYLE, pool[k]["name"]
            elif k >= n_styles:
                mode, preset = MODE_PRESET, STAR + lib["presets"][k - n_styles]["name"]
            info.append(f"random source → {mode}")

        # ---- base style / preset
        if mode == MODE_PRESET:
            presets = lib["presets"]
            p = (rng.choice(presets) if presets else None) if preset == RANDOM else \
                next((p for p in presets if STAR + p["name"] == preset), None)
            if p:
                parts.append(finish(pick({"Short_Prompt": p["short"], "Long_Prompt": p["long"]}, L)))
                info.append(f"Preset: {p['name']} [{p['id']}]")
            else:
                info.append("⚠ Preset: nothing selected")
        elif mode == MODE_STYLE:
            if style == RANDOM:
                chosen = rng.choice(pool) if pool else None
            else:
                chosen = next((r for r in lib["styles"] if r["name"] == style), None)
            if chosen:
                t = pick_text(chosen, version)
                parts.append(finish(t if include_style_names else strip_name(t)))
                info.append(f"Style: {chosen['name']} [{chosen['id']}] ({chosen['cat']} / {chosen['sub']}, "
                            f"pool {len(pool)} in {', '.join(subjects)})")
            else:
                info.append("⚠ Style: none matched the current filters")

        # ---- modifiers
        opts = build_options(lib)
        mod_parts = []
        for c in MODIFIER_CATEGORIES:
            keys = comp_keys() if c == "Composition" else [mod_key(c)]
            for k in keys:
                label, row = opts[c].resolve(kw.get(k, NONE), seed, k)
                if row:
                    t = pick_text(row, version)
                    mod_parts.append(finish(t if include_style_names else strip_name(t)))
                    info.append(f"{c}: {label} [{row['id']}]")
        extra = {}
        for key, okey in (("lighting", "Lighting"), ("mood", "Mood")):
            label, row = opts[okey].resolve(kw.get(key, NONE), seed, key)
            extra[key] = finish(pick(row, L)) if row else ""
            if row:
                info.append(f"{okey}: {label} [{row.get('ID', '')}]")
        modifiers = " ".join(mod_parts)
        style_main = " ".join(parts)
        style_text = " ".join(x for x in (style_main, modifiers, extra["lighting"], extra["mood"]) if x)
        style_text, wc2 = expand_wildcards(style_text, seed, "style_text")  # libraries may hold wildcards too
        wc_log += wc2

        # ---- assemble
        p = prompt.strip()
        pos = clean(style_position)
        tpl = lib["positions"].get(pos, "{prompt}, {style}")
        if tpl is None:  # custom
            tpl = custom_template or "{prompt}, {style}"
            if any(x in tpl for x in ("{modifiers}", "{lighting}", "{mood}")):
                out = (tpl.replace("{prompt}", p).replace("{style}", style_main)
                       .replace("{modifiers}", modifiers).replace("{lighting}", extra["lighting"])
                       .replace("{mood}", extra["mood"]))
            else:
                out = tpl.replace("{prompt}", p).replace("{style}", style_text)
        elif not p:
            out = style_text
        elif not style_text:
            out = p
        else:
            pp = p.rstrip(" .,") if ("{prompt}," in tpl or "{prompt}." in tpl) else p
            out = tpl.replace("{prompt}", pp).replace("{style}", style_text)
        out = "\n".join(re.sub(r"[ \t]+", " ", line).replace(" ,", ",").replace("..", ".").strip()
                        for line in out.split("\n")).strip()
        info.insert(0, f"seed {seed} · {version} · {mode}")
        return (out, style_text, "\n".join(info + wc_log))


# --------------------------------------------------------------------------- API for the JS
try:
    from server import PromptServer
    from aiohttp import web

    @PromptServer.instance.routes.get("/style_atlas/data")
    async def _style_atlas_data(request):
        return web.json_response(public_data())
except Exception:
    pass

NODE_CLASS_MAPPINGS = {NODE: StyleAtlasNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE: "🎨 Style Atlas"}
