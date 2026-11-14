// Atlas common - shared UI helpers for 🎨 Style Atlas, 🧑 Character Atlas and 🏞️ Setting Atlas.
// * setVisible(): hide / show a widget while keeping its value
// * hookNode(): run a refresh function whenever a widget changes, when the node is created and loaded
// * ❔ help: a small "?" in the title bar (and "❔ Atlas help" in the right-click menu) opens the node help
// Everything is wrapped in try/catch: if the UI layer fails, the nodes keep working.
import { app } from "../../scripts/app.js";

export const NONE = "None", BYPASS = "None (bypass)", RANDOM = "🎲 Random", RANDOM_ALL = "🎲 Random (all sources)";
export const ATLAS_CLASSES = ["StyleAtlasNode", "CharacterAtlas", "SettingAtlas"];
export const strip = (v) => String(v ?? "").replace(/\s*\(\d+\)\s*$/, "").trim();
export const W = (node, name) => node.widgets?.find((w) => w.name === name);
export const V = (node, name) => strip(W(node, name)?.value);
export const isSet = (node, name) => {
    const v = V(node, name);
    return v !== "" && v !== NONE && v !== "Default" && v !== "undefined";
};

export function setVisible(w, show) {
    if (!w) return;
    if (w._atlasOrigType === undefined) { w._atlasOrigType = w.type; w._atlasOrigSize = w.computeSize; }
    if (show) { w.type = w._atlasOrigType; w.computeSize = w._atlasOrigSize; w.hidden = false; }
    else { w.type = "atlas_hidden"; w.computeSize = () => [0, -4]; w.hidden = true; }
}

export function fit(node) {
    try {
        node.setSize?.([node.size[0], node.computeSize()[1]]);
        node.setDirtyCanvas?.(true, true);
        app.graph?.setDirtyCanvas?.(true, true);
    } catch (e) { /* ignore */ }
}

/** Section header: "▼ FILTERS  (3 set)". */
export function sectionLabel(toggle, title, n, extra = "") {
    if (!toggle) return false;
    const open = !!toggle.value;
    toggle.label = `${open ? "▼" : "▶"} ${title}${n ? `  (${n} set)` : ""}${extra}`;
    return open;
}

/** Call refresh(node) on every widget change, on creation and after a workflow is loaded. */
export function hookNode(nodeType, refresh) {
    const wire = (node) => {
        for (const w of node.widgets || []) {
            if (w.__atlasHooked || w.name === "prompt") continue;
            const cb = w.callback;
            w.callback = function () {
                const out = cb?.apply(this, arguments);
                try { refresh(node); } catch (e) { console.warn("[Atlas] refresh failed", e); }
                return out;
            };
            w.__atlasHooked = true;
        }
    };
    const onCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        const r = onCreated?.apply(this, arguments);
        wire(this);
        setTimeout(() => { try { refresh(this); } catch (e) { console.warn(e); } }, 0);
        return r;
    };
    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function () {
        const r = onConfigure?.apply(this, arguments);
        wire(this);
        setTimeout(() => { try { refresh(this); } catch (e) { console.warn(e); } }, 0);
        return r;
    };
}

// ------------------------------------------------------------------ ❔ help popup
let pop = null;
function closeHelp() { if (pop) { pop.remove(); pop = null; } }

function openHelp(title, text, x, y) {
    closeHelp();
    pop = document.createElement("div");
    Object.assign(pop.style, {
        position: "fixed", zIndex: 100001, maxWidth: "420px", padding: "12px 14px 10px",
        background: "#1f2124", color: "#ddd", border: "1px solid #4a4f57", borderRadius: "8px",
        boxShadow: "0 8px 24px rgba(0,0,0,.55)", font: "12.5px/1.45 system-ui, sans-serif",
        whiteSpace: "pre-wrap",
    });
    const head = document.createElement("div");
    Object.assign(head.style, { display: "flex", justifyContent: "space-between", alignItems: "center",
                                marginBottom: "6px", fontWeight: "600", color: "#fff" });
    head.textContent = title;
    const x_ = document.createElement("span");
    x_.textContent = "✕";
    Object.assign(x_.style, { cursor: "pointer", marginLeft: "12px", opacity: ".7" });
    x_.onclick = closeHelp;
    head.appendChild(x_);
    const body = document.createElement("div");
    body.textContent = text.split("\n").slice(1).join("\n").trim();   // first line = title
    pop.append(head, body);
    document.body.appendChild(pop);
    const r = pop.getBoundingClientRect();
    pop.style.left = Math.max(6, Math.min(x, window.innerWidth - r.width - 6)) + "px";
    pop.style.top = Math.max(6, Math.min(y, window.innerHeight - r.height - 6)) + "px";
    setTimeout(() => document.addEventListener("pointerdown", outside, { capture: true }), 0);
}
function outside(e) {
    if (pop && !pop.contains(e.target)) { closeHelp(); document.removeEventListener("pointerdown", outside, { capture: true }); }
}
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeHelp(); });

function helpFor(nodeData) {
    const text = nodeData?.description || "";
    const title = (text.split("\n")[0] || nodeData?.display_name || "Atlas").trim();
    return { title, text };
}

function lastPointer() {
    const e = app.canvas?.last_mouse_event || window.event;
    return [e?.clientX ?? window.innerWidth / 2, e?.clientY ?? 120];
}

app.registerExtension({
    name: "Atlas.Help",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!ATLAS_CLASSES.includes(nodeData.name)) return;
        const { title, text } = helpFor(nodeData);
        const H = () => (globalThis.LiteGraph?.NODE_TITLE_HEIGHT ?? 30);

        const draw = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            const r = draw?.apply(this, arguments);
            try {
                if (this.flags?.collapsed) return r;
                const h = H(), cx = this.size[0] - h / 2, cy = -h / 2;
                ctx.save();
                ctx.beginPath();
                ctx.arc(cx, cy, 8, 0, Math.PI * 2);
                ctx.fillStyle = this.__atlasHelpHover ? "#6a8cff" : "#3b3f46";
                ctx.fill();
                ctx.fillStyle = "#fff";
                ctx.font = "bold 11px sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText("?", cx, cy + 0.5);
                ctx.restore();
            } catch (e) { /* ignore */ }
            return r;
        };

        const down = nodeType.prototype.onMouseDown;
        nodeType.prototype.onMouseDown = function (e, pos) {
            try {
                const h = H();
                if (pos && pos[1] < 0 && pos[1] > -h && pos[0] > this.size[0] - h) {
                    openHelp(title, text, (e?.clientX ?? 200) + 12, (e?.clientY ?? 120) + 12);
                    return true;
                }
            } catch (err) { /* ignore */ }
            return down?.apply(this, arguments);
        };

        const menu = nodeType.prototype.getExtraMenuOptions;
        nodeType.prototype.getExtraMenuOptions = function (_, options) {
            const r = menu?.apply(this, arguments);
            options?.unshift?.({ content: "❔ Atlas help", callback: () => { const [x, y] = lastPointer(); openHelp(title, text, x, y); } }, null);
            return r;
        };
    },
});
