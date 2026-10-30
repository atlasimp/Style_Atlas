import { app } from "../../scripts/app.js";

// Collapsible sections + progressive reveal for 🧑 Character Atlas.
// Hidden widgets keep their values. Without this file the node still works, fully expanded.

const NODE = "CharacterAtlas";
const NONE = "None";

const SLOTS = ["top_1", "top_2", "bottom_1", "bottom_2", "full_body", "outerwear", "footwear"];
const SLOT_MODS = ["color", "fabric", "pattern", "finish"];
const ACC = [1, 2, 3, 4, 5, 6];
const FACE = ["face_shape", "jaw", "cheekbones", "eyebrows", "eye_shape", "eye_color", "eyelashes",
              "nose", "lips", "complexion", "facial_hair", "distinctive_1", "distinctive_2"];

const SECTIONS = {
    section_identity: { label: "IDENTITY", members: ["archetype", "gender", "age", "character_type", "height", "body_shape"] },
    section_face: { label: "FACE", members: FACE },
    section_expression: { label: "EXPRESSION", members: ["expression_1", "expression_2"] },
    section_hair: { label: "HAIR", members: ["hair_style", "hair_color"] },
    section_outfit: { label: "OUTFIT", members: SLOTS.flatMap(s => [s, ...SLOT_MODS.map(m => `${s}_${m}`)]) },
    section_accessories: { label: "ACCESSORIES", members: ACC.flatMap(i => [`accessory_${i}`, `accessory_${i}_color`, `accessory_${i}_material`]) },
    section_pose: { label: "POSE", members: ["pose"] },
};
const COUNTED = {
    section_identity: SECTIONS.section_identity.members,
    section_face: FACE,
    section_expression: SECTIONS.section_expression.members,
    section_hair: SECTIONS.section_hair.members,
    section_outfit: SLOTS,
    section_accessories: ACC.map(i => `accessory_${i}`),
    section_pose: ["pose"],
};

const W = (node, name) => node.widgets?.find(w => w.name === name);
const V = (node, name) => W(node, name)?.value;
const isSet = (node, name) => { const v = V(node, name); return v !== undefined && v !== NONE; };

function setVisible(w, show) {
    if (!w) return;
    if (w._caOrigType === undefined) { w._caOrigType = w.type; w._caOrigSize = w.computeSize; }
    if (show) { w.type = w._caOrigType; w.computeSize = w._caOrigSize; w.hidden = false; }
    else { w.type = "ca_hidden"; w.computeSize = () => [0, -4]; w.hidden = true; }
}

function extraRule(node, name) {
    for (const s of SLOTS) {
        if (SLOT_MODS.some(m => name === `${s}_${m}`) && !isSet(node, s)) return false;
    }
    if (/^(top|bottom)_[12]/.test(name) && isSet(node, "full_body")) return false;
    if (/^top_2/.test(name) && !isSet(node, "top_1")) return false;
    if (/^bottom_2/.test(name) && !isSet(node, "bottom_1")) return false;
    if (name === "expression_2" && !isSet(node, "expression_1")) return false;
    if (name === "facial_hair" && V(node, "gender") === "Female") return false;
    const m = name.match(/^accessory_(\d+)(_.*)?$/);
    if (m) {
        const i = +m[1];
        if (m[2] && !isSet(node, `accessory_${i}`)) return false;
        if (i > 1 && !isSet(node, `accessory_${i - 1}`)) return false;
    }
    return true;
}

function refresh(node) {
    const mode = V(node, "mode");
    setVisible(W(node, "known_character"), mode === "Known Character");
    setVisible(W(node, "preset"), mode === "Preset (Actor)");
    setVisible(W(node, "recognition"), mode !== "Custom");

    for (const [key, sec] of Object.entries(SECTIONS)) {
        const toggle = W(node, key);
        if (!toggle) continue;
        const open = !!toggle.value;
        const n = COUNTED[key].filter(x => isSet(node, x)).length;
        toggle.label = `${open ? "▼" : "▶"} ${sec.label}${n ? `  (${n} set)` : ""}`;
        for (const name of sec.members) setVisible(W(node, name), open && extraRule(node, name));
    }
    node.setSize([node.size[0], node.computeSize()[1]]);
    node.setDirtyCanvas?.(true, true);
    app.graph?.setDirtyCanvas(true, true);
}

function collapseFor(node, mode) {
    const custom = mode === "Custom";
    for (const key of Object.keys(SECTIONS)) {
        const t = W(node, key);
        if (t) t.value = custom ? ["section_identity", "section_hair"].includes(key) : false;
    }
}

app.registerExtension({
    name: "CharacterAtlas.Collapse",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE) return;

        const onCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onCreated?.apply(this, arguments);
            const node = this;
            for (const w of node.widgets || []) {
                if (w.name === "prompt" || w.name === "seed") continue;
                const cb = w.callback;
                w.callback = function (value) {
                    const out = cb?.apply(this, arguments);
                    if (w.name === "mode") collapseFor(node, value);
                    refresh(node);
                    return out;
                };
            }
            setTimeout(() => refresh(node), 0);
            return r;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const r = onConfigure?.apply(this, arguments);
            setTimeout(() => refresh(this), 0);
            return r;
        };
    },
});
