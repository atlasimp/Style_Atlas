// 🎨 Style Atlas - mode switch, subject checkboxes with counts, linked filters, collapsible sections.
// If anything fails, the node keeps working with its plain (unfiltered) Python widgets.
import { app } from "../../scripts/app.js";
import { BYPASS, NONE, RANDOM, RANDOM_ALL, strip, W, V, isSet, setVisible, fit, sectionLabel, hookNode } from "./atlas_common.js";

const NODE = "StyleAtlasNode";
const ALL = "All";
const MODE_STYLE = "Style", MODE_PRESET = "★ Preset", MODE_MODS = "Modifiers only";
const SUBJ = "subject: ";
const FILTERS = ["era", "realism", "realism_mode", "category", "subcategory"];
const MODS = ["quality", "genre", "palette", "composition_1", "composition_2", "composition_3"];
const LOOK = ["lighting", "mood"];
const ADV = ["style_position", "include_style_names", "custom_template"];

let DATA = null, loading = null;
function loadData() {
    if (DATA) return Promise.resolve(DATA);
    loading ??= fetch("/style_atlas/data").then((r) => r.json()).then((d) => (DATA = d))
        .catch((e) => { console.warn("[Style Atlas] data not loaded, filters disabled", e); return null; });
    return loading;
}

const versionOk = (r, v) => (v === "Short only" ? !!r.hs : v === "Long only" ? !!r.hl : true);
function realismOk(r, real, mode) {
    if (real === ALL || real === "") return true;
    const t = parseInt(real, 10);
    return mode === "Exact" ? r.r === t : Math.abs(r.r - t) <= 1;
}
function setOptions(w, items, fallback) {
    if (!w) return;
    const current = strip(w.value);
    const values = items.map(([n, c]) => (c === null ? n : `${n} (${c})`));
    w.options = w.options || {};
    w.options.values = values;
    const hit = items.findIndex(([n]) => n === current);
    w.value = hit >= 0 ? values[hit] : values[Math.max(0, items.findIndex(([n]) => n === fallback))];
}
const subjectWidgets = (node) => (node.widgets || []).filter((w) => w.name.startsWith(SUBJ));

function refresh(node) {
    const mode = V(node, "mode");
    const off = mode === BYPASS || mode === "";
    const useFilters = mode === MODE_STYLE || mode === RANDOM_ALL;

    // ---- linked filters with live counts
    if (DATA?.rows?.length) {
        const base = DATA.rows.filter((r) => versionOk(r, V(node, "version")) && realismOk(r, V(node, "realism"), V(node, "realism_mode")));
        let ticked = subjectWidgets(node).filter((w) => w.value).map((w) => w.name.slice(SUBJ.length));
        for (const w of subjectWidgets(node)) {
            const subj = w.name.slice(SUBJ.length);
            w.label = `${w.value ? "✓" : "·"} ${subj} (${base.filter((r) => r.j === subj).length})`;
        }
        if (!ticked.length) ticked = DATA.subjects || [];
        const bySubj = base.filter((r) => ticked.includes(r.j));
        const eras = [...new Set(bySubj.map((r) => r.e))].sort();
        setOptions(W(node, "era"), [[ALL, bySubj.length], ...eras.map((e) => [e, bySubj.filter((r) => r.e === e).length])], ALL);
        const era = V(node, "era");
        const byEra = bySubj.filter((r) => era === ALL || r.e === era);
        const cats = [...new Set(byEra.map((r) => r.c))];
        setOptions(W(node, "category"), [[ALL, byEra.length], ...cats.map((c) => [c, byEra.filter((r) => r.c === c).length])], ALL);
        const cat = V(node, "category");
        const byCat = byEra.filter((r) => cat === ALL || r.c === cat);
        const subs = [...new Set(byCat.map((r) => r.s))].sort();
        setOptions(W(node, "subcategory"), [[ALL, byCat.length], ...subs.map((s) => [s, byCat.filter((r) => r.s === s).length])], ALL);
        const sub = V(node, "subcategory");
        const pool = byCat.filter((r) => sub === ALL || r.s === sub);
        setOptions(W(node, "style"), [[RANDOM, pool.length], ...pool.map((r) => r.n).sort().map((n) => [n, null])], RANDOM);
        node.__styleFilterCount = ticked.length + ["era", "realism", "category", "subcategory"].filter((f) => V(node, f) !== ALL).length;
        node.__stylePool = pool.length;
    }

    // ---- what is visible
    setVisible(W(node, "style"), mode === MODE_STYLE);
    setVisible(W(node, "preset"), mode === MODE_PRESET);
    setVisible(W(node, "version"), !off);

    const fT = W(node, "section_filters");
    setVisible(fT, useFilters);
    const fOpen = useFilters && sectionLabel(fT, "FILTERS", 0,
        node.__stylePool !== undefined ? `  · ${node.__stylePool} styles` : "");
    for (const w of subjectWidgets(node)) setVisible(w, fOpen);
    for (const f of FILTERS) setVisible(W(node, f), fOpen);
    setVisible(W(node, "realism_mode"), fOpen && V(node, "realism") !== ALL);

    const mT = W(node, "section_modifiers");
    setVisible(mT, !off);
    const mOpen = !off && sectionLabel(mT, "MODIFIERS", MODS.filter((m) => isSet(node, m)).length);
    for (const m of MODS) setVisible(W(node, m), mOpen);
    if (mOpen) {
        setVisible(W(node, "composition_2"), isSet(node, "composition_1"));
        setVisible(W(node, "composition_3"), isSet(node, "composition_1") && isSet(node, "composition_2"));
    }

    const lT = W(node, "section_look");
    setVisible(lT, !off);
    const lOpen = !off && sectionLabel(lT, "LIGHTING & MOOD", LOOK.filter((m) => isSet(node, m)).length);
    for (const m of LOOK) setVisible(W(node, m), lOpen);

    const aT = W(node, "section_advanced");
    setVisible(aT, !off);
    const aOpen = !off && sectionLabel(aT, "ADVANCED", 0);
    for (const a of ADV) setVisible(W(node, a), aOpen);
    setVisible(W(node, "custom_template"), aOpen && V(node, "style_position").toLowerCase().startsWith("custom"));
    fit(node);
}

app.registerExtension({
    name: "StyleAtlas.UI",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE) return;
        hookNode(nodeType, (node) => { refresh(node); loadData().then(() => { try { refresh(node); } catch (e) { console.warn(e); } }); });
    },
});
