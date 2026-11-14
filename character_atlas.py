"""
🧑 Character Atlas - decides WHO is in the image, from character_atlas_library.xlsx.
Sources: None (bypass) / Known Character / Known Role / Preset / Custom / 🎲 Random (all sources).

Output is written the way Krea 2 reads best: short sentences, one idea each
(identity, hair style, hair colour, outfit, makeup, expression, hand pose, gaze, pose).
"""
import random

try:
    from .atlas_core import (NONE, BYPASS, RANDOM, RANDOM_ALL, SEP, Options, clean, hier_label, pick, tidy,
                             sentence, join_prompt, pronoun, load_workbook_dict, library_mtime, register_thumbs,
                             expand_wildcards, wildcard_signature, seed_input, section)
except ImportError:
    from atlas_core import (NONE, BYPASS, RANDOM, RANDOM_ALL, SEP, Options, clean, hier_label, pick, tidy,
                            sentence, join_prompt, pronoun, load_workbook_dict, library_mtime, register_thumbs,
                            expand_wildcards, wildcard_signature, seed_input, section)

LIBRARY = "character_atlas_library.xlsx"
NODE = "CharacterAtlas"
LIST_SOURCES = {"Known Character": "known_character", "Known Role": "known_role", "Preset": "preset"}
SOURCES = [BYPASS, "Known Character", "Known Role", "Preset", "Custom", RANDOM_ALL]
SLOTS = [("top_1", "Top"), ("top_2", "Top"), ("bottom_1", "Bottom"), ("bottom_2", "Bottom"),
         ("full_body", "Full Body"), ("outerwear", "Outerwear"), ("footwear", "Footwear")]
ACC_COUNT = 6
FACE_FIELDS = [("face_shape", "Face Shape"), ("jaw", "Jaw"), ("cheekbones", "Cheekbones"),
               ("eyebrows", "Eyebrows"), ("eye_shape", "Eye Shape"), ("eye_color", "Eye Color"),
               ("eyelashes", "Eyelashes"), ("nose", "Nose"), ("lips", "Lips"),
               ("complexion", "Complexion"), ("facial_hair", "Facial Hair"),
               ("distinctive_1", "Distinctive"), ("distinctive_2", "Distinctive")]
GENDERS = ["Female", "Male", "Androgynous"]
INTENSITY = ["Default", "slight", "clear", "intense"]
YOUNG = ("Child", "Teen")

HELP = """🧑 Character Atlas decides who is in the image.

• source: a Known Character (franchise › character › variant), a Known Role (actor in a role), a Preset, your own Custom character, or 🎲 Random (all sources). None (bypass) does nothing.
• Every source can add makeup, expression, hand pose, gaze and pose. Custom also opens identity, face, hair, outfit and accessories.
• Sections fold with ▶ / ▼; the header shows how many settings are in use.
• Expressions are written as brows / eyes / mouth / head sentences, which Krea 2 follows far better than names. Intensity changes the wording.
• Teen and child characters never receive Adult-only rows (skipped, listed in info).
• __wildcards__ in the prompt are resolved here if no earlier node did it.
• seed: same seed, same character."""


# --------------------------------------------------------------------------- library
def _lib():
    data, err = load_workbook_dict(LIBRARY)
    O = {}
    O["known_character"] = Options([(hier_label(r, "Franchise", "Character", "Variant"), r)
                                    for r in data.get("Known_Characters", [])])
    O["known_role"] = Options([(r.get("Name"), r) for r in data.get("Known_Roles", [])], group_random=False)
    O["preset"] = Options([(r.get("Name"), r) for r in data.get("Presets", [])], group_random=False)
    O["archetype"] = Options([(hier_label(r, "Umbrella", "Variant"), r) for r in data.get("Archetypes", [])])
    O["ethnicity"] = Options([(hier_label(r, "Umbrella", "Variant"), r) for r in data.get("Ethnicity", [])])
    attrs = {}
    for r in data.get("Attributes", []):
        attrs.setdefault(r.get("Attribute_Type"), []).append(r)
    A = {}
    for t, rows in attrs.items():
        grouped = t in ("Body Shape", "Hair Style", "Hair Color")
        A[t] = Options([(hier_label(r, "Category", "Name") if grouped else r.get("Name"), r) for r in rows],
                       group_random=grouped)
    O["gender"] = Options([(g, {"Name": g}) for g in GENDERS], group_random=False)
    for w, t in (("age", "Age"), ("character_type", "Character Type"), ("height", "Height"),
                 ("body_shape", "Body Shape"), ("hair_style", "Hair Style"), ("hair_color", "Hair Color")):
        O[w] = A.get(t) or Options([])
    for w, t in FACE_FIELDS:
        O[w] = A.get(t) or Options([])
    O["makeup"] = Options([(hier_label(r, "Umbrella", "Variant"), r) for r in data.get("Makeup", [])])
    ex = Options([(hier_label(r, "Umbrella", "Variant"), r) for r in data.get("Expressions", [])])
    O["expression_1"] = O["expression_2"] = ex
    O["hand_pose"] = Options([(hier_label(r, "Category", "Name"), r) for r in data.get("Hand_Poses", [])])
    O["gaze"] = Options([(r.get("Variant"), r) for r in data.get("Gaze", [])], group_random=False)
    outfits = {}
    for r in data.get("Outfits", []):
        outfits.setdefault(r.get("Slot"), []).append(r)
    colors = Options([(hier_label(r, "Category", "Name"), r) for r in data.get("Colors", [])])
    fabrics_all = data.get("Fabrics", [])
    patterns = Options([(r.get("Name"), r) for r in data.get("Patterns", [])], group_random=False)
    finishes = Options([(r.get("Name"), r) for r in data.get("Finishes", [])], group_random=False)

    def fabrics_for(slot):
        return Options([(hier_label(r, "Category", "Name"), r) for r in fabrics_all
                        if slot in [x.strip() for x in r.get("Applies_To", "").split(";")]])
    for w, slot in SLOTS:
        O[w] = Options([(hier_label(r, "Category", "Name"), r) for r in outfits.get(slot, [])])
        O[f"{w}_color"], O[f"{w}_fabric"] = colors, fabrics_for(slot)
        O[f"{w}_pattern"], O[f"{w}_finish"] = patterns, finishes
    acc = Options([(hier_label(r, "Category", "Name"), r) for r in data.get("Accessories", [])])
    acc_mat = fabrics_for("Accessory")
    for i in range(1, ACC_COUNT + 1):
        O[f"accessory_{i}"], O[f"accessory_{i}_color"], O[f"accessory_{i}_material"] = acc, colors, acc_mat
    O["pose"] = Options([(hier_label(r, "Category", "Subcategory", "Pose"), r) for r in data.get("Poses", [])])
    full_body_by_name = {r.get("Name"): r for r in outfits.get("Full Body", [])}
    return O, err, full_body_by_name


def _and_list(items):
    items = [i for i in items if i]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _dedupe_join(parts):
    seen, out = set(), []
    for p in parts:
        for frag in [f.strip() for f in tidy(p).rstrip(".").split(",")]:
            if frag and frag.lower() not in seen:
                seen.add(frag.lower())
                out.append(frag)
    return ", ".join(out)


def _adult_ok(row, young):
    return not (young and row and row.get("Age_Filter", "All") == "Adult only")


# --------------------------------------------------------------------------- node
class CharacterAtlas:
    DESCRIPTION = HELP

    @classmethod
    def INPUT_TYPES(cls):
        O, _, _ = _lib()
        v = lambda name: (O[name].values,)
        req = {
            "prompt": ("STRING", {"multiline": True, "default": "",
                                  "tooltip": "Your prompt. __name__ is replaced by a random line of wildcards/name.txt"}),
            "source": (SOURCES, {"default": BYPASS,
                                 "tooltip": "None (bypass) = prompt passes through unchanged (wildcards are still resolved)."}),
            "known_character": v("known_character"),
            "known_role": v("known_role"),
            "preset": v("preset"),
            "section_identity": section(True),
            "archetype": v("archetype"), "gender": v("gender"), "age": v("age"),
            "ethnicity": v("ethnicity"), "character_type": v("character_type"),
            "height": v("height"), "body_shape": v("body_shape"),
            "section_face": section(False),
        }
        for w, _ in FACE_FIELDS:
            req[w] = v(w)
        req["makeup"] = v("makeup")
        req["section_hair"] = section(False)
        req["hair_style"], req["hair_color"] = v("hair_style"), v("hair_color")
        req["section_expression"] = section(False)
        req["expression_1"], req["expression_2"] = v("expression_1"), v("expression_2")
        req["expression_intensity"] = (INTENSITY, {"tooltip": "Changes the wording of the expression, not just a prefix."})
        req["hand_pose"] = (O["hand_pose"].values, {"tooltip": "Written in its own sentence, after the face."})
        req["gaze"] = v("gaze")
        req["section_outfit"] = section(False)
        for w, _ in SLOTS:
            for k in (w, f"{w}_color", f"{w}_fabric", f"{w}_pattern", f"{w}_finish"):
                req[k] = v(k)
        req["section_accessories"] = section(False)
        for i in range(1, ACC_COUNT + 1):
            for k in (f"accessory_{i}", f"accessory_{i}_color", f"accessory_{i}_material"):
                req[k] = v(k)
        req["section_pose"] = section(False)
        req["pose"] = v("pose")
        req["section_advanced"] = section(False)
        req["prompt_length"] = (["Long", "Short"], {"tooltip": "Long = described sentences (best for Krea 2)."})
        req["recognition"] = (["Name + Description", "Name Only", "Description Only"],)
        req["character_position"] = (["Character, Prompt", "Prompt, Character"],)
        req["seed"] = seed_input("Drives every 🎲 Random choice and every __wildcard__. Fixed seed = same character.")
        register_thumbs(NODE, {k: o.ids() for k, o in O.items()})
        return {"required": req}

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("prompt", "character", "info")
    OUTPUT_TOOLTIPS = ("Full prompt with the character in it.", "Only the character text.",
                       "Every choice with its ID, the seed and any warning.")
    FUNCTION = "build"
    CATEGORY = "Style Atlas/Prompt"

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return f"{library_mtime(LIBRARY)}:{wildcard_signature()}"

    # ------------------------------------------------------------ pieces
    def _subject(self, R, L):
        gender = (R.get("gender") or {}).get("Name", "")
        age = (R.get("age") or {}).get("Name", "")
        ctype = (R.get("character_type") or {}).get("Name", "")
        noun = {"Female": "woman", "Male": "man", "Androgynous": "androgynous person"}.get(gender, "")
        age_word = pick(R.get("age"), L) if age else ""
        if age in YOUNG and gender in ("Female", "Male"):
            noun = {"Female": "girl", "Male": "boy"}[gender]
            age_word = "teenage" if age == "Teen" else ""
        type_word = pick(R.get("character_type"), L) if ctype and ctype != "Human" else ""
        eth = pick(R.get("ethnicity"), L)
        if not noun and (age_word or eth) and not type_word:
            noun = "person"
        if age_word and " " in age_word:          # 'adult in their thirties' reads better after the noun
            return ", ".join(x for x in (" ".join(y for y in (eth, type_word, noun) if y), age_word) if x)
        return " ".join(x for x in (age_word, eth, type_word, noun) if x)

    def _garment(self, R, w, L):
        row = R.get(w)
        if not row:
            return ""
        term = row.get("Garment_Term") or row.get("Short_Prompt") or row.get("Name", "").lower()
        fabric = pick(R.get(f"{w}_fabric"), L) if R.get(f"{w}_fabric") else row.get("Default_Fabric", "")
        pattern = (R.get(f"{w}_pattern") or {}).get("Prompt", "") or ("" if R.get(f"{w}_pattern") else row.get("Default_Pattern", ""))
        color = (R.get(f"{w}_color") or {}).get("Prompt", "")
        fin = (R.get(f"{w}_finish") or {}).get("Prompt", "")
        sp, lp = row.get("Short_Prompt", ""), row.get("Long_Prompt", "")
        # descriptive detail that follows the garment noun in the Short prompt ('hoodie' + ' with cat ears…')
        detail = sp[len(term):].strip() if term and sp.lower().startswith(term.lower()) else ""
        phrase = " ".join(x for x in (fin, color, pattern, fabric, term, detail) if x)
        if L == "Long" and sp and lp.startswith(sp):
            construction = lp[len(sp):].strip()
            if construction:
                phrase = f"{phrase}{'' if construction[0] == ',' else ' '}{construction}"
        return phrase

    def _accessory(self, R, i, L):
        row = R.get(f"accessory_{i}")
        if not row:
            return ""
        color = (R.get(f"accessory_{i}_color") or {}).get("Prompt", "")
        material = pick(R.get(f"accessory_{i}_material"), L)
        base = (row.get("Long_Prompt") if L == "Long" and not (color or material) else None) \
            or row.get("Short_Prompt") or row.get("Name", "").lower()
        return " ".join(x for x in (color, material, base) if x)

    @staticmethod
    def _expression(row, L, intensity):
        """Long rows are described sentences: intensity leads them with a short naming sentence."""
        if intensity != "Default":
            col = {"slight": "Slight_Prompt", "intense": "Intense_Prompt"}.get(intensity)
            if col and row.get(col):
                return row[col]
        text = pick(row, L)
        if intensity == "Default":
            return text
        name = row.get("Short_Prompt") or row.get("Variant", "").lower()
        if L == "Short":
            return f"{intensity} {name}"
        if "," in name:                      # multi-part short prompts read badly after an article
            name = "expression"
        art = "an" if intensity[0] in "aeiou" else "a"
        return f"{art.capitalize()} {intensity} {name}. {text}"

    # ------------------------------------------------------------ main
    def build(self, prompt="", source=BYPASS, seed=0, **k):
        prompt, wc_log = expand_wildcards(prompt or "", seed, "character_prompt")
        source = clean(source)
        if source in (BYPASS, NONE, ""):
            return (prompt, "", "\n".join(["Character Atlas: bypassed"] + wc_log))
        O, err, full_body_by_name = _lib()
        if err:
            return (prompt, "", f"⚠ {err}")
        L = clean(k.get("prompt_length", "Long"))
        info, warn = [], []
        forced = {}
        if source == RANDOM_ALL:
            rng = random.Random(f"{seed}:source")
            available = [s_ for s_, w in LIST_SOURCES.items() if O[w].map]
            source = rng.choice(available) if available else "Custom"
            forced[LIST_SOURCES.get(source, "")] = RANDOM
            info.append(f"random source → {source}")
        info.insert(0, f"source {source} · seed {seed} · {L}")

        def res(name, keep=None):
            label, row = O[name].resolve(forced.get(name, k.get(name, NONE)), seed, name, keep)
            if row is not None:
                info.append(f"{name}: {label}" + (f" [{row['ID']}]" if row.get("ID") else ""))
            return row

        blocks, young, gender = [], False, ""
        if source in LIST_SOURCES:
            row = res(LIST_SOURCES[source])
            if not row:
                return (prompt, "", "\n".join(info + ["⚠ nothing selected"] + wc_log))
            young = row.get("Age_Group") in YOUNG
            gender = row.get("Gender", "")
            text = tidy(pick(row, L)).rstrip(".")
            rec = clean(k.get("recognition", "Name + Description"))
            head = ""
            if source == "Known Character":
                head = f"{row.get('Character')} from {row.get('Franchise')}"
            elif source == "Known Role":
                head = text.split(",")[0]
            if head and rec == "Name Only":
                text = head
            elif head and rec == "Description Only" and text.startswith(head):
                text = text[len(head):].lstrip(", ")
            blocks.append(text)
        else:  # Custom
            R = {}
            for name in ("gender", "age", "ethnicity", "character_type"):
                R[name] = res(name)
            young = (R.get("age") or {}).get("Name") in YOUNG
            gender = (R.get("gender") or {}).get("Name", "")
            keep = lambda r: _adult_ok(r, young) and (not gender or r.get("Gender", "All") in ("All", "Any", "", gender)
                                                      or (r.get("Gender") == "Androgynous"))
            R["archetype"] = res("archetype", lambda r: keep(r) and not (young and r.get("Age_Group") == "Adult"))
            ident = [self._subject(R, L)]
            if R.get("archetype"):
                if young and R["archetype"].get("Age_Group") == "Adult":
                    warn.append("archetype skipped (adult archetype on a young character)")
                    R["archetype"] = None
                else:
                    ident.append(pick(R["archetype"], L))
            for name in ("height", "body_shape"):
                r = res(name, keep)
                if r and not _adult_ok(r, young):
                    warn.append(f"{name} skipped (Adult only)")
                    r = None
                ident.append(pick(r, L))
            face_detail = False
            for w, _ in FACE_FIELDS:
                if w == "facial_hair" and gender == "Female":
                    continue
                t = pick(res(w, keep), L)
                if t.endswith(", clearly defined"):
                    t, face_detail = t[: -len(", clearly defined")], True
                ident.append(t)
            if face_detail:
                ident.append("clearly defined facial features")
            blocks.append(_dedupe_join([p for p in ident if p]))
            # Krea 2: hair style and hair colour each get their own sentence
            blocks.append(pick(res("hair_style"), L))
            blocks.append(pick(res("hair_color"), L))
            # outfit
            for w, _ in SLOTS:
                for suf in ("", "_color", "_fabric", "_pattern", "_finish"):
                    R[w + suf] = res(w + suf, keep if suf == "" else None)
                if R[w] and not _adult_ok(R[w], young):
                    warn.append(f"{w} skipped (Adult only)")
                    R[w] = None
            full = bool(R.get("full_body"))
            garments = [g for g in (self._garment(R, w, L) for w, slot in SLOTS
                                    if not (full and slot in ("Top", "Bottom"))) if g]
            if not garments and R.get("archetype"):
                linked = full_body_by_name.get(R["archetype"].get("Linked_Outfit", ""))
                if linked:
                    garments.append(pick(linked, L))
                    info.append(f"linked outfit: {linked.get('Name')} [{linked.get('ID', '')}]")
            for i in range(1, ACC_COUNT + 1):
                for suf in ("", "_color", "_material"):
                    R[f"accessory_{i}{suf}"] = res(f"accessory_{i}{suf}", keep if suf == "" else None)
                if R[f"accessory_{i}"] and not _adult_ok(R[f"accessory_{i}"], young):
                    warn.append(f"accessory_{i} skipped (Adult only)")
                    R[f"accessory_{i}"] = None
            accs = [a for a in (self._accessory(R, i, L) for i in range(1, ACC_COUNT + 1)) if a]
            wear = ("wearing " + _and_list(garments)) if garments else ""
            if accs:
                wear = f"{wear}, with {_and_list(accs)}" if wear else "with " + _and_list(accs)
            blocks.append(wear)

        # layers available for every source
        keep = lambda r: _adult_ok(r, young)
        mk = res("makeup", keep)
        if mk and _adult_ok(mk, young):
            blocks.append(pick(mk, L))
        elif mk:
            warn.append("makeup skipped (Adult only)")
        intensity = clean(k.get("expression_intensity", "Default"))
        for e in ("expression_1", "expression_2"):
            r = res(e, keep)
            if r and _adult_ok(r, young):
                blocks.append(self._expression(r, L, intensity))
            elif r:
                warn.append(f"{e} skipped (Adult only)")
        hp = res("hand_pose", keep)
        if hp and _adult_ok(hp, young):
            blocks.append(pronoun(pick(hp, L), gender))
        elif hp:
            warn.append("hand_pose skipped (Adult only)")
        g = res("gaze")
        if g:
            blocks.append(pick(g, L))
        p = res("pose", keep)
        if p and _adult_ok(p, young):
            blocks.append(pick(p, L))
        elif p:
            warn.append("pose skipped (Adult only)")

        character = " ".join(sentence(b) for b in blocks if b and b.strip())
        character, wc2 = expand_wildcards(character, seed, "character_text")
        user = prompt.strip()
        if clean(k.get("character_position")) == "Prompt, Character":
            final = join_prompt(user, character)
        else:
            final = join_prompt(character, user)
        info += [f"⚠ {w}" for w in warn] + wc_log + wc2
        return (final, character, "\n".join(info))


NODE_CLASS_MAPPINGS = {NODE: CharacterAtlas}
NODE_DISPLAY_NAME_MAPPINGS = {NODE: "🧑 Character Atlas"}
