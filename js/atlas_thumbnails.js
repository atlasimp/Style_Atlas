// Atlas thumbnails - shows thumbnails/<ID>.jpg when hovering an entry of an Atlas dropdown.
// Works for 🎨 Style Atlas, 🧑 Character Atlas and 🏞️ Setting Atlas.
// Drop small images named after the row ID (e.g. ST0025.jpg, KC120.png, LOC0042.webp)
// into the thumbnails/ folder: no restart needed (the list refreshes every few seconds).
import { app } from "../../scripts/app.js";

const CLASSES = ["StyleAtlasNode", "CharacterAtlas", "SettingAtlas"];
const SHOW_ID_WHEN_MISSING = true;   // small ID badge when no image exists yet (handy to name files)
const SIZE = 192;                    // preview size in px

let MAP = null, mapTime = 0, AVAIL = new Set(), availTime = 0;
let lastNode = null;
const strip = (v) => String(v ?? "").replace(/\s*\(\d+\)\s*$/, "").trim();

async function refreshData() {
    const now = Date.now();
    try {
        if (!MAP || now - mapTime > 60000) {
            MAP = await (await fetch("/atlas/thumbmap")).json();
            mapTime = now;
        }
        if (now - availTime > 5000) {
            AVAIL = new Set(((await (await fetch("/atlas/thumblist")).json()).ids || []).map((x) => x.toUpperCase()));
            availTime = now;
        }
    } catch (e) {
        console.warn("[Atlas thumbnails] data not loaded", e);
    }
}

// ---------------------------------------------------------------- preview box
let box = null;
function getBox() {
    if (box) return box;
    box = document.createElement("div");
    Object.assign(box.style, {
        position: "fixed", zIndex: 100000, pointerEvents: "none", display: "none",
        background: "#1e1e1e", border: "1px solid #555", borderRadius: "6px", padding: "4px",
        boxShadow: "0 4px 14px rgba(0,0,0,.5)", font: "11px sans-serif", color: "#ccc", textAlign: "center",
    });
    const img = document.createElement("img");
    Object.assign(img.style, { maxWidth: SIZE + "px", maxHeight: SIZE + "px", display: "block", borderRadius: "4px" });
    const cap = document.createElement("div");
    cap.style.marginTop = "2px";
    box.append(img, cap);
    document.body.appendChild(box);
    return box;
}
function show(entry, id) {
    const b = getBox();
    const [img, cap] = b.children;
    const has = AVAIL.has(id.toUpperCase());
    if (!has && !SHOW_ID_WHEN_MISSING) return hide();
    img.style.display = has ? "block" : "none";
    if (has) img.src = `/atlas/thumb/${encodeURIComponent(id)}?t=${availTime}`;
    cap.textContent = has ? id : `${id} · no thumbnail`;
    b.style.display = "block";
    const r = entry.getBoundingClientRect();
    const w = has ? SIZE + 10 : 140;
    let left = r.right + 8;
    if (left + w > window.innerWidth) left = Math.max(4, r.left - w - 8);
    let top = r.top;
    const h = has ? SIZE + 26 : 24;
    if (top + h > window.innerHeight) top = Math.max(4, window.innerHeight - h - 4);
    b.style.left = left + "px";
    b.style.top = top + "px";
}
function hide() { if (box) box.style.display = "none"; }

// ---------------------------------------------------------------- menu detection
function widgetMapFor(node, texts) {
    const byClass = MAP?.[node.comfyClass];
    if (!byClass) return null;
    let best = null, bestScore = 0;
    for (const w of node.widgets || []) {
        const vals = w.options?.values;
        if (!Array.isArray(vals) || !byClass[w.name]) continue;
        const set = new Set(vals.map(strip));
        let score = 0;
        for (const t of texts) if (set.has(t)) score++;
        if (score > bestScore) { bestScore = score; best = byClass[w.name]; }
    }
    return best;
}

async function onMenu(menu) {
    const cur = app.canvas?.current_node;
    const node = cur ? cur : lastNode;
    if (!node || !CLASSES.includes(node.comfyClass)) return;
    await refreshData();
    const entries = [...menu.querySelectorAll(".litemenu-entry")];
    if (!entries.length) return;
    const texts = entries.slice(0, 40).map((e) => strip(e.textContent));
    const map = widgetMapFor(node, texts);
    if (!map) return;
    for (const e of entries) {
        if (e.__atlasThumb) continue;
        e.__atlasThumb = true;
        e.addEventListener("mouseenter", () => {
            const raw = e.textContent?.trim() ?? "";
            const id = map[raw] || map[strip(raw)];
            if (id) show(e, id); else hide();
        });
        e.addEventListener("mouseleave", hide);
    }
}

const observer = new MutationObserver((muts) => {
    for (const m of muts) {
        for (const n of m.addedNodes) {
            if (!(n instanceof HTMLElement)) continue;
            if (n.classList?.contains("litecontextmenu") || n.querySelector?.(".litemenu-entry")) {
                setTimeout(() => onMenu(n.classList.contains("litecontextmenu") ? n : n.closest(".litecontextmenu") || n), 0);
            }
        }
        for (const n of m.removedNodes) {
            if (n instanceof HTMLElement && n.classList?.contains("litecontextmenu")) hide();
        }
    }
});

app.registerExtension({
    name: "Atlas.Thumbnails",
    setup() {
        observer.observe(document.body, { childList: true, subtree: true });
        refreshData();
    },
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!CLASSES.includes(nodeData.name)) return;
        const down = nodeType.prototype.onMouseDown;
        nodeType.prototype.onMouseDown = function () {
            lastNode = this;
            return down?.apply(this, arguments);
        };
    },
});
