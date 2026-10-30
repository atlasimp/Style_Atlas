# 🎨 Style Atlas & 🧑 Character Atlas for ComfyUI

Two prompt-building nodes driven by editable Excel libraries:

| Node | Purpose |
|---|---|
| **🎨 Style Atlas** | Controls **how** the image is rendered: medium, style, era, realism, modifiers. |
| **🧑 Character Atlas** | Controls **who** is in the image: known characters, actor presets, or a custom character with face, hair, outfit, accessories and pose. |

Both live under **Add Node › Style Atlas › Prompt** and can be chained:

```text
[ your scene prompt ] → 🧑 Character Atlas → 🎨 Style Atlas → CLIP Text Encode
```

---

## Installation

1. Copy this repository into `ComfyUI/custom_nodes/`:
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/atlasimp/Style_Atlas.git
   ```
   Or download the ZIP and extract it there.
2. Install the only dependency:
   ```bash
   pip install openpyxl
   ```
   On portable ComfyUI, run this from the ComfyUI root:
   ```bash
   python_embeded\python.exe -m pip install openpyxl
   ```
3. Restart ComfyUI completely, then hard-refresh the browser (**Ctrl+F5**).
4. Right-click on the canvas › **Add Node › Style Atlas › Prompt**.

### Repository structure

```text
Style_Atlas/
├── __init__.py
├── style_atlas.py
├── style_atlas_library.xlsx
├── character_atlas.py
├── character_atlas_library.xlsx
├── requirements.txt
└── js/
    ├── (Style Atlas interface script)
    └── character_atlas.js
```

Keep each `.xlsx` next to its `.py` file and keep these file names.

---

## 🎨 Style Atlas

Adds a rendering style to your prompt.

### Controls

| Control | What it does |
|---|---|
| **Subject › Era › Category › Subcategory › Style** | Linked dropdowns. Each choice filters the next one, and the counts show how many styles are left. |
| **Version** / **Realism** | Filter every list. |
| **Architectural Style / Vehicle Design / Product Design** | Extra modifiers. They only appear when the matching Subject (or All) is selected. |
| **Custom template** | Free layout using the placeholders `{prompt}`, `{style}` and `{modifiers}`. |

### Example

```text
prompt:  a lighthouse on a cliff
style:   Gouache Illustration
output:  a lighthouse on a cliff, gouache illustration, opaque layered pigment, ...
```

### Editing the library

`style_atlas_library.xlsx` holds every style. You can edit or add rows in Excel:
- Edited prompt text is used on the **next run**.
- Restart ComfyUI to update the **dropdown lists**.

---

## 🧑 Character Atlas

Builds a character description and **adds it to the start of your prompt**.

### Inputs and outputs

| | |
|---|---|
| **prompt** (input) | Your scene, e.g. `standing in a rainy neon street`. |
| **prompt** (output) | Character description + your prompt. |
| **character** (output) | The character description only. |

### Modes

| Mode | Use it for |
|---|---|
| **Custom** | Building your own character, attribute by attribute. |
| **Known Character** | 330 characters from games, anime, comics and films (Mario, Chun-Li, 2B, Sailor Moon, Batman...). |
| **Preset (Actor)** | 55 actor roles (Neo by Keanu Reeves, Trinity by Carrie-Anne Moss, Leeloo by Milla Jovovich...). |

Known characters start with **`<Character> from <Franchise>`**. Presets add **`, played by <Actor>`**.

**Recognition** (Known and Preset modes only):
- **Name + Description**: default and most reliable across models.
- **Name Only**: for models that already know the character well.
- **Description Only**: the look without the name.

### Collapsible sections

To keep the node small, attributes are grouped into sections. Click a header to fold or unfold it. The header shows how many entries are set, e.g. `▶ OUTFIT (3 set)`.

| Section | Contents |
|---|---|
| **IDENTITY** | Gender, age, character type (human, elf, android, kitsune...), height, body shape. |
| **FACE** | Face shape, jaw, cheekbones, eyebrows, eye shape, eye color, eyelashes, nose, lips, skin, facial hair, 2 distinctive features. |
| **HAIR** | Hairstyle (133 styles in 9 groups) and hair color. |
| **OUTFIT** | Top 1 and 2, Bottom 1 and 2, Full Body, Outerwear, Footwear. |
| **ACCESSORIES** | Up to 6 accessories. |
| **POSE** | 228 poses, including anime sitting poses (wariza, seiza, yokozuwari...) and gestures. |

**Selecting a Known Character or Preset collapses every section.** You can still unfold any section to add things on top, for example Mario + a pose, or Trinity + different shoes.

Fields only appear when they're useful:
- **Color, fabric, pattern and finish** appear once a garment is chosen.
- **Top 2 and Bottom 2** appear after Top 1 and Bottom 1.
- **Full Body** (dress, armor, uniform...) hides and ignores the top and bottom slots.
- **The next accessory slot** appears when the previous one is filled. Each accessory has its own color and material.

Every dropdown accepts typing to search, e.g. type `wariza` or `chun`.

### Outfit modifiers

Each garment can take a **color** (141), **fabric** (88), **pattern** (44) and **finish** (36). They're combined in this order:

```text
[finish] [color] [pattern] [fabric] [garment]
distressed black leather biker jacket
forest green plaid wool skirt
```

The fabric list only shows materials that make sense for that slot. Choosing a fabric replaces the garment's built-in one, so you get "silk pants", never "silk leather pants".

### Other options

| Option | Effect |
|---|---|
| **prompt_length** | **Short** for compact prompts. **Long** adds construction and material detail. |
| **character_position** | `Character, Prompt` (default) or `Prompt, Character`. |

### Examples

**Known character + pose**
```text
mode: Known Character   known_character: Super Mario | Mario
pose: Jumping | Platformer Jump      prompt: inside a castle
→ Mario from Super Mario, short stocky build, large rounded nose, thick dark mustache,
  red cap with red M emblem, red shirt, blue overalls with yellow buttons,
  jumping with one fist raised, inside a castle
```

**Custom character**
```text
→ young adult elf woman, tall stature, hourglass figure, balanced bust and hips,
  narrow waist, thick arched eyebrows, green eyes, straight nose, auburn hair,
  long wavy hairstyle, wearing burgundy velvet corset top, forest green plaid skirt,
  distressed black leather biker jacket and knee-high boots,
  with gold hoop earrings and katana, wariza, in a forest
```

### The library (`character_atlas_library.xlsx`)

| Sheet | Contents |
|---|---|
| Known_Characters | 330 characters with short and long prompts |
| Presets | 55 actor roles |
| Attributes | Body shapes, hairstyles, face features, skin, hair color, age, character types... |
| Outfits | Garments by slot (Top / Bottom / Full Body / Outerwear / Footwear) |
| Colors / Fabrics / Patterns / Finishes | Outfit modifiers |
| Poses | 228 poses |
| Accessories | 359 accessories |
| Settings | Rules used by the node |

To add an entry, add a row with the same columns. Set **Enabled** to `No` to hide a row without deleting it. If a Short or Long prompt is empty, the node uses the other one. **Restart ComfyUI** after editing.

---

## Recommended workflow

```text
Character Atlas (prompt output) → Style Atlas (prompt input) → CLIP Text Encode
```

Keep the jobs separate:
- **Character Atlas:** who the character is and how they look.
- **Your prompt:** what they are doing and where.
- **Style Atlas:** how the image is rendered.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Node missing from the menu | Python problem. Look for `IMPORT FAILED` or `[Style Atlas] ... failed to load` in the console. |
| `No module named openpyxl` | Install it (see Installation). |
| `character_atlas_library.xlsx not found` | Put the file next to `character_atlas.py` with that exact name. |
| Sections don't collapse / dropdowns aren't linked | JavaScript problem. Press Ctrl+F5, then check the browser console (F12). The nodes still work, just fully expanded. |
| New xlsx entries not in the dropdowns | Restart ComfyUI. |
| Node appears twice / conflicts | Remove any old separate `ComfyUI-Character-Atlas` folder from `custom_nodes`. |
| Changes to `__init__.py` ignored | Delete the `__pycache__` folder and restart. |

---

## Requirements

- ComfyUI
- Python package: `openpyxl`
