// 🧑 Character Atlas - source switch, collapsible sections with "(n set)" counters, progressive slots.
// Hidden widgets keep their values. Without this file the node still works, fully expanded.
import { app } from "../../scripts/app.js";
import { BYPASS, RANDOM_ALL, W, V, isSet, setVisible, fit, sectionLabel, hookNode } from "./atlas_common.js";

const NODE = "CharacterAtlas";
const SLOTS = ["top_1", "top_2", "bottom_1", "bottom_2", "full_body", "outerwear", "footwear"];
const SLOT_MODS = ["color", "fabric", "pattern", "finish"];
const ACC = [1, 2, 3, 4, 5, 6];
const FACE = ["face_shape", "jaw", "cheekbones", "eyebrows", "eye_shape", "eye_color", "eyelashes",
              "nose", "lips", "complexion", "facial_hair", "distinctive_1", "distinctive_2", "makeup"];

// custom: true = only for the Custom source
const SECTIONS = {
    section_identity: { label: "IDENTITY", custom: true, members: ["archetype", "gender", "age", "ethnicity", "character_type", "height", "body_shape"] },
    section_face: { label: "FACE & MAKEUP", custom: false, members: FACE },
    section_hair: { label: "HAIR", custom: true, members: ["hair_style", "hair_color"] },
    section_expression: { label: "EXPRESSION & HANDS", custom: false, members: ["expression_1", "expression_2", "expression_intensity", "hand_pose", "gaze"] },
    section_outfit: { label: "OUTFIT", custom: true, members: SLOTS.flatMap((s) => [s, ...SLOT_MODS.map((m) => `${s}_${m}`)]) },
    section_accessories: { label: "ACCESSORIES", custom: true, members: ACC.flatMap((i) => [`accessory_${i}`, `accessory_${i}_color`, `accessory_${i}_material`]) },
    section_pose: { label: "POSE", custom: false, members: ["pose"] },
    section_advanced: { label: "ADVANCED", custom: false, members: ["prompt_length", "recognition", "character_position"], noCount: true },
};
const COUNTED = {
    section_identity: SECTIONS.section_identity.members,
    section_face: FACE,
    section_hair: SECTIONS.section_hair.members,
    section_expression: ["expression_1", "expression_2", "hand_pose", "gaze"],
    section_outfit: SLOTS,
    section_accessories: ACC.map((i) => `accessory_${i}`),
    section_pose: ["pose"],
    section_advanced: [],
};
const SOURCE_WIDGET = { "Known Character": "known_character", "Known Role": "known_role", "Preset": "preset" };

function extraRule(node, name, custom, source) {
    if (!custom && FACE.includes(name) && name !== "makeup") return false;
    for (const s of SLOTS) if (SLOT_MODS.some((m) => name === `${s}_${m}`) && !isSet(node, s)) return false;
    if (/^(top|bottom)_[12]/.test(name) && isSet(node, "full_body")) return false;
    if (/^top_2/.test(name) && !isSet(node, "top_1")) return false;
    if (/^bottom_2/.test(name) && !isSet(node, "bottom_1")) return false;
    if (name === "expression_2" && !isSet(node, "expression_1")) return false;
    if (name === "expression_intensity" && !isSet(node, "expression_1")) return false;
    if (name === "facial_hair" && V(node, "gender") === "Female") return false;
    if (name === "recognition" && !["Known Character", "Known Role", RANDOM_ALL].includes(source)) return false;
    const m = name.match(/^accessory_(\d+)(_.*)?$/);
    if (m) {
        const i = +m[1];
        if (m[2] && !isSet(node, `accessory_${i}`)) return false;
        if (i > 1 && !isSet(node, `accessory_${i - 1}`)) return false;
    }
    return true;
}

function refresh(node) {
    const source = V(node, "source");
    const off = source === BYPASS || source === "";
    const custom = source === "Custom";
    for (const [src, wn] of Object.entries(SOURCE_WIDGET)) setVisible(W(node, wn), source === src);
    for (const [key, sec] of Object.entries(SECTIONS)) {
        const toggle = W(node, key);
        if (!toggle) continue;
        const allowed = !off && (custom || !sec.custom);
        setVisible(toggle, allowed);
        const open = allowed && sectionLabel(toggle, sec.label, sec.noCount ? 0 : COUNTED[key].filter((x) => isSet(node, x)).length);
        for (const name of sec.members) setVisible(W(node, name), open && extraRule(node, name, custom, source));
    }
    fit(node);
}

app.registerExtension({
    name: "CharacterAtlas.UI",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === NODE) hookNode(nodeType, refresh);
    },
});
