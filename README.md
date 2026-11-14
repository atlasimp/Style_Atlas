<img width="960" height="1280" alt="image" src="https://github.com/user-attachments/assets/f9c0b38d-cba9-4fad-9b63-a4f336472f34" />
# 🎨 Style Atlas · 🧑 Character Atlas · 🏞️ Setting Atlas

*Three ComfyUI nodes that turn an Excel library into well-written prompts, so you can spend your time choosing instead of typing.*

---

## Why this exists

Writing a good prompt takes three different decisions: **who** is in the picture, **where** they are, and **how** the image is rendered. Mixing all three by hand in one text box means retyping the same descriptions again and again, forgetting the wording that worked last week, and getting styles that quietly add objects, people or backgrounds you never asked for.

Style Atlas gives each of those decisions its own node. Each node reads a spreadsheet you can open, edit and grow in Excel. You get a library of tested descriptions instead of a pile of notes. You pick from a dropdown, the node writes the sentence, and the prompt stays readable.

The libraries are written with **Krea 2** in mind, and they work with any model that reads natural language:

* **Styles describe how the image is rendered, not what is in it.** No stray subjects, outfits or backgrounds leak in.
* **Expressions and hair are described, not named.** Krea 2 rarely understands *"scowl"* or *"hime cut"*. It does understand *"brows pulled hard down and together, eyes narrowed, mouth flat with the corners turned down"*.
* **Short sentences, one idea each.** Hair colour gets its own sentence, and so do the face and the hands. Krea 2 runs at CFG 1 with no negative prompt, so weights like `(tag:1.2)` do nothing. The nodes never write them.

## The three nodes

```text
[ your prompt ] → 🧑 Character Atlas → 🏞️ Setting Atlas → 🎨 Style Atlas → CLIP Text Encode
                     who                  where               how
```

All three live under **Add Node › Style Atlas › Prompt**. Every node starts on **None (bypass)**, so the prompt passes through unchanged until you choose something. Each node folds down to a couple of lines, so a full pipeline doesn't take over your workflow.

Click the small **?** in a node's title bar (or right-click › **❔ Atlas help**) to read a short help.

### 🧑 Character Atlas: who
<img width="316" height="365" alt="image" src="https://github.com/user-attachments/assets/818586e6-4ec4-4b04-9e33-6e0de4378211" />

Pick a **Known Character** (franchise › character › variant, with masked/unmasked and costume variants), a **Known Role** (an actor in a role), a **Preset**, or build your own **Custom** character from identity, face, hair, outfit and accessories. Not sure? **🎲 Random (all sources)** picks the source for you.

Whatever the source, you can add makeup, up to two expressions with an intensity, a **hand pose**, a gaze and a body pose. Each section opens with ▶ / ▼ and shows how many settings are in use, so you can tell at a glance what is active even when it's folded.

Teen and child characters never receive rows marked *Adult only*. They are skipped and reported in `info`.

### 🏞️ Setting Atlas: where
<img width="341" height="383" alt="image" src="https://github.com/user-attachments/assets/7c0f4833-aaa1-4469-b648-e5771715da26" />

Choose a **Preset**, **Location**, **Simple Background**, **Studio**, **Known Location** or **Anime Setting**, or let 🎲 decide. Optional layers add weather, lighting, condition, décor, palette, a frame and population. Population is the only layer that adds people, on purpose. Output can be natural sentences or Danbooru tags.

### 🎨 Style Atlas: how
<img width="309" height="597" alt="image" src="https://github.com/user-attachments/assets/0da4fc1a-0411-4efb-b753-e58ab6335dd6" />

The first dropdown is the **mode**:

| mode | what it does |
|---|---|
| None (bypass) | nothing (wildcards are still resolved) |
| Style | one rendering style, chosen from the filtered list |
| ★ Preset | a ready-made combination |
| Modifiers only | no style, just quality / genre / palette / composition / lighting / mood |
| 🎲 Random (all sources) | a random style or preset |

**Subjects are checkboxes.** Tick *Main* and *Portrait & Character* to mix them while leaving Landscape, Architecture, Automotive and Product out. Era, realism, category and subcategory narrow the list further, with live counts at every step.

## Wildcards

Drop `.txt` files into the `wildcards/` folder, one entry per line, then write `__name__` anywhere in a prompt:

```text
a __adjective__ __character/profession__ wearing __color__
→ a weathered violinist wearing cobalt blue
```

The first Atlas node that receives the text resolves it, using that node's seed, so the result can be reproduced. Sub-folders work (`__character/profession__`), lines can contain other wildcards, and unknown names are left as they are for any other tool further down. A few example files are included; see `wildcards/README.md`.

## Your libraries

Every list comes from the `.xlsx` next to its node:

* `style_atlas_library.xlsx`
* `character_atlas_library.xlsx`
* `setting_atlas_library.xlsx`

Edit rows, add rows, or set **Enabled = No** to hide one, then refresh the browser. Each workbook has a **Settings** sheet with its rules and a **Changelog** sheet listing every change.

Every selectable row has a unique 4-digit **ID** (`ST0599`, `KC0021`, `HP0003`…). The ID shows up in `info`, and it is also the thumbnail filename.

## Thumbnails

Save a small image as `thumbnails/<ID>.jpg` (or `.png` / `.webp`) and it appears when you hover that entry in a dropdown. Entries without an image show their ID, so you know what to name the file. `thumbnails/convert.ps1` batch-converts a folder to medium-quality JPG.

## Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/atlasimp/Style_Atlas.git
pip install openpyxl          # portable build: python_embeded\python.exe -m pip install openpyxl
```

Restart ComfyUI, then hard-refresh the browser (**Ctrl+F5**).

```text
Style_Atlas/
├── __init__.py
├── atlas_core.py                  shared: xlsx loading, dropdowns, random, wildcards, thumbnails
├── style_atlas.py      + style_atlas_library.xlsx
├── character_atlas.py  + character_atlas_library.xlsx
├── setting_atlas.py    + setting_atlas_library.xlsx
├── wildcards/                     your __wildcard__ .txt files
├── thumbnails/                    <ID>.jpg previews
└── js/
    ├── atlas_common.js            ❔ help, show / hide helpers
    ├── style_atlas.js             mode switch, subject checkboxes, linked filters
    ├── character_atlas.js         source switch, collapsible sections
    ├── setting_atlas.js           source switch, collapsible layers
    └── atlas_thumbnails.js        hover previews
```

> **Upgrading from v2:** the order of the inputs changed (mode first, seed last), so nodes saved in older workflows may load with shifted values. Re-add the Atlas nodes in those workflows.

## Outputs

Each node returns:

* `prompt`: the full text
* the part it added on its own (`character`, `setting` or `style_text`)
* `info`: every choice with its ID, the seed, the wildcard picks and any warning

## Credits

The Krea 2 wording rules for expressions and hair come from community testing published on Civitai: *Facial Expression Vocabulary* and *Hairstyle Vocabulary* by **Azimondious**, and the *Character, Clothing & Outfit Taglist* by **Hellfreeze**. Thank you for doing the slow, careful work.
