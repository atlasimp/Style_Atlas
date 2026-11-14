"""
Atlas core - shared helpers for Style Atlas, Character Atlas and Setting Atlas.

* XLSX reading (cached, reloads automatically when the file changes on disk)
* Grouped dropdown lists: "Group | Item" entries + "Group | 🎲 Random" entries
* Seeded random resolution inside a group
* Wildcards: __name__ in a prompt is replaced by a random line of wildcards/name.txt
* Thumbnails: every selectable row has a unique ID; thumbnails/<ID>.jpg shows on hover
"""
import os
import re
import glob
import random
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
THUMB_DIR = os.path.join(HERE, "thumbnails")
WILDCARD_DIR = os.path.join(HERE, "wildcards")
THUMB_EXT = (".jpg", ".jpeg", ".png", ".webp")

NONE = "None"
BYPASS = "None (bypass)"
RANDOM = "🎲 Random"
RANDOM_ALL = "🎲 Random (all sources)"
SEP = " | "
COUNT_RE = re.compile(r"\s*\(\d+\)\s*$")
SEED_MAX = 0xFFFFFFFFFFFFFFFF

# node class -> widget name -> {label: ID}   (filled by each node module)
THUMB_MAP = {}


def clean(value):
    """Remove the ' (123)' count suffix added by the JS for display."""
    return COUNT_RE.sub("", str(value if value is not None else "")).strip()


def s(v):
    return "" if v is None else str(v).strip()


def seed_input(tooltip="Drives every 🎲 Random choice and every __wildcard__. Same seed = same result."):
    return ("INT", {"default": 0, "min": 0, "max": SEED_MAX, "tooltip": tooltip})


def section(default=False, tooltip="Show or hide this group of settings. Hidden settings keep their values."):
    return ("BOOLEAN", {"default": default, "label_on": "▼ shown", "label_off": "▶ hidden", "tooltip": tooltip})


# ---------------------------------------------------------------- xlsx
_cache = {}


def find_library(name):
    p = os.path.join(HERE, name)
    if os.path.isfile(p):
        return p
    stem = os.path.splitext(name)[0]
    found = sorted(f for f in glob.glob(os.path.join(HERE, stem + "*.xlsx"))
                   if not os.path.basename(f).startswith("~$"))
    return found[-1] if found else None


def library_mtime(name):
    p = find_library(name)
    return os.path.getmtime(p) if p else 0


def load_workbook_dict(name):
    """Return ({sheet: [row dicts]}, error). Rows with Enabled = No are dropped."""
    path = find_library(name)
    if not path:
        return {}, f"{name} not found in {HERE}"
    mtime = os.path.getmtime(path)
    c = _cache.get(name)
    if c and c["path"] == path and c["mtime"] == mtime:
        return c["data"], c["error"]
    try:
        import openpyxl
    except ImportError:
        return {}, "openpyxl is not installed (pip install openpyxl)"
    data, error = {}, None
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for ws in wb.worksheets:
            it = ws.iter_rows(values_only=True)
            try:
                header = [s(h) for h in next(it)]
            except StopIteration:
                continue
            rows = []
            for r in it:
                if r is None or all(v is None for v in r):
                    continue
                d = {header[i]: s(v) for i, v in enumerate(r) if i < len(header) and header[i]}
                if d.get("Enabled", "Yes").lower() in ("no", "false", "0"):
                    continue
                rows.append(d)
            data[ws.title] = rows
        wb.close()
    except Exception as e:  # never crash ComfyUI because of a spreadsheet
        data, error = {}, f"Could not read {os.path.basename(path)}: {e}"
    _cache[name] = dict(path=path, mtime=mtime, data=data, error=error)
    return data, error


# ---------------------------------------------------------------- grouped options
class Options:
    """An ordered {label: row} map plus the dropdown list built from it."""

    def __init__(self, entries, head=(NONE,), randomizable=True, group_random=True):
        self.map = {}
        for label, row in entries:
            if not label:
                continue
            base, n = label, 2
            while label in self.map:          # keep labels unique
                label = f"{base} ({row.get('ID') or n})"
                n += 1
            self.map[label] = row
        keys = list(self.map.keys())
        if group_random:                      # keep each group together even if rows were appended later
            order = {}
            for k in keys:
                order.setdefault(k.split(SEP)[0], len(order))
            keys.sort(key=lambda k: order[k.split(SEP)[0]])
            self.map = {k: self.map[k] for k in keys}
        out = list(head)
        if randomizable and keys:
            out.append(RANDOM)
        seen = set()
        for k in keys:
            if group_random:
                parts = k.split(SEP)
                for depth in range(1, len(parts)):
                    prefix = SEP.join(parts[:depth])
                    if prefix in seen:
                        continue
                    seen.add(prefix)
                    if sum(1 for x in keys if x.startswith(prefix + SEP)) > 1:
                        out.append(f"{prefix}{SEP}{RANDOM}")
            out.append(k)
        self.values = out

    def ids(self):
        return {k: r.get("ID", "") for k, r in self.map.items() if r.get("ID")}

    def resolve(self, value, seed, salt, keep=None):
        """Turn a value (possibly a random token) into (label, row) or (None, None)."""
        v = clean(value)
        if not v or v in (NONE, BYPASS):
            return None, None
        if RANDOM in v:
            keys = list(self.map.keys())
            if v not in (RANDOM, RANDOM_ALL):
                prefix = v[: -len(SEP + RANDOM)]
                keys = [k for k in keys if k.startswith(prefix + SEP)]
            if keep:
                keys = [k for k in keys if keep(self.map[k])]
            leaves = [k for k in keys if self.map[k].get("Level", "Variant") not in ("Umbrella", "Item")]
            keys = leaves or keys
            if not keys:
                return None, None
            v = random.Random(f"{seed}:{salt}").choice(keys)
        row = self.map.get(v)
        if row is None:
            row = self.map.get(value)
        return (v, row) if row is not None else (None, None)


def hier_label(row, *cols):
    """'Umbrella | Item | Variant' from the non-empty columns (duplicates collapsed)."""
    parts = []
    for c in cols:
        v = row.get(c, "")
        if v and v.lower() != "none" and (not parts or parts[-1] != v):
            parts.append(v)
    return SEP.join(parts)


def pick(row, length):
    if not row:
        return ""
    sh, lo = row.get("Short_Prompt", ""), row.get("Long_Prompt", "")
    return (lo or sh) if length == "Long" else (sh or lo)


def tidy(text):
    text = re.sub(r"[ \t]+", " ", text or "")
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",\s*,+", ",", text)
    text = re.sub(r"\.\s*\.", ".", text)
    text = re.sub(r",\s*\.", ".", text)
    return text.strip(" ,")


def sentence(text):
    """'blonde hair' -> 'Blonde hair.'  (keeps existing punctuation)."""
    t = tidy(text).strip()
    if not t:
        return ""
    t = t[0].upper() + t[1:]
    return t if t[-1] in ".!?" else t + "."


def join_prompt(first, second):
    """Join two prompt parts: a space after a full sentence, a comma otherwise."""
    a, b = (first or "").strip(), (second or "").strip()
    if not a or not b:
        return a or b
    if a[-1] in ".!?\n":
        return f"{a} {b[0].upper() + b[1:]}"
    return f"{a.rstrip(' ,')}, {b}"


# ---------------------------------------------------------------- pronouns
PRONOUNS = {"Female": ("her", "Her"), "Male": ("his", "His")}


def pronoun(text, gender):
    low, cap = PRONOUNS.get(gender or "", ("their", "Their"))
    return (text or "").replace("{their}", low).replace("{Their}", cap)


# ---------------------------------------------------------------- wildcards
WILDCARD_RE = re.compile(r"__([A-Za-z0-9_\-/\\. ]+?)__")
_wc_cache = {}


def _wildcard_files():
    out = {}
    if not os.path.isdir(WILDCARD_DIR):
        return out
    for root, _, files in os.walk(WILDCARD_DIR):
        for f in files:
            if f.lower().endswith(".txt"):
                full = os.path.join(root, f)
                key = os.path.relpath(full, WILDCARD_DIR)[:-4].replace("\\", "/").lower()
                out[key] = full
    return out


def wildcard_lines(name):
    files = _wildcard_files()
    key = name.replace("\\", "/").strip().lower()
    path = files.get(key)
    if path is None:                      # __adjective__ also finds wildcards/any/folder/adjective.txt
        tails = [p for k, p in files.items() if k.split("/")[-1] == key]
        path = tails[0] if tails else None
    if path is None:
        return None
    mtime = os.path.getmtime(path)
    c = _wc_cache.get(path)
    if c and c[0] == mtime:
        return c[1]
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        lines = [ln.strip() for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]
    _wc_cache[path] = (mtime, lines)
    return lines


def expand_wildcards(text, seed, salt="wc", depth=6):
    """Replace every __name__ with a random line of wildcards/name.txt.

    Each occurrence is drawn separately (two __color__ can differ), driven by the seed.
    A line may contain other __wildcards__ (resolved up to `depth` levels).
    Unknown names are left untouched so another tool can still use them.
    Returns (text, [log lines]).
    """
    if not text or "__" not in text:
        return text, []
    rng = random.Random(f"{seed}:{salt}")
    log = []

    def one(m):
        name = m.group(1)
        lines = wildcard_lines(name)
        if not lines:
            if lines is None:
                log.append(f"⚠ wildcard __{name}__: no file wildcards/{name}.txt")
            return m.group(0)
        pick_ = rng.choice(lines)
        log.append(f"__{name}__ → {pick_}")
        return pick_

    for _ in range(depth):
        new = WILDCARD_RE.sub(one, text)
        if new == text:
            break
        text = new
    return text, log


def wildcard_signature():
    """Changes whenever a wildcard file is edited (used by IS_CHANGED)."""
    h = hashlib.md5()
    for k, p in sorted(_wildcard_files().items()):
        try:
            h.update(f"{k}:{os.path.getmtime(p)}".encode())
        except OSError:
            pass
    return h.hexdigest()


def wildcard_names():
    return sorted(_wildcard_files().keys())


# ---------------------------------------------------------------- thumbnails
def register_thumbs(node_class, mapping):
    THUMB_MAP[node_class] = mapping


def thumb_file(tid):
    if not re.fullmatch(r"[A-Za-z]{1,4}\d{1,6}", tid or ""):
        return None
    for ext in THUMB_EXT:
        for name in (tid, tid.upper(), tid.lower()):
            p = os.path.join(THUMB_DIR, name + ext)
            if os.path.isfile(p):
                return p
    return None


def thumb_list():
    try:
        return sorted({os.path.splitext(f)[0].upper() for f in os.listdir(THUMB_DIR)
                       if f.lower().endswith(THUMB_EXT)})
    except OSError:
        return []


# ---------------------------------------------------------------- routes
try:
    from server import PromptServer
    from aiohttp import web

    _routes = PromptServer.instance.routes

    @_routes.get("/atlas/thumbmap")
    async def _atlas_thumbmap(request):
        return web.json_response(THUMB_MAP)

    @_routes.get("/atlas/thumblist")
    async def _atlas_thumblist(request):
        return web.json_response({"ids": thumb_list()})

    @_routes.get("/atlas/thumb/{tid}")
    async def _atlas_thumb(request):
        p = thumb_file(request.match_info.get("tid", ""))
        if not p:
            return web.Response(status=404)
        return web.FileResponse(p, headers={"Cache-Control": "no-cache"})

    @_routes.get("/atlas/wildcards")
    async def _atlas_wildcards(request):
        return web.json_response({"names": wildcard_names()})
except Exception:
    pass
