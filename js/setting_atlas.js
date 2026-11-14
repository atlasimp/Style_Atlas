// 🏞️ Setting Atlas - shows only the list of the chosen source; layers and advanced options fold away.
import { app } from "../../scripts/app.js";
import { BYPASS, W, V, isSet, setVisible, fit, sectionLabel, hookNode } from "./atlas_common.js";

const NODE = "SettingAtlas";
const SOURCE_WIDGET = {
    "Preset": "preset", "Location": "location", "Simple Background": "simple_background",
    "Studio": "studio", "Known Location": "known_location", "Anime Setting": "anime_setting",
};
const LAYERS = ["weather", "lighting", "condition", "decor", "palette", "population", "frame"];
const SIMPLE_ONLY = ["lighting", "palette", "frame"];
const ADV = ["prompt_length", "prompt_format", "setting_position"];

function refresh(node) {
    const source = V(node, "source");
    const off = source === BYPASS || source === "";
    const simple = source === "Simple Background";
    for (const [src, wn] of Object.entries(SOURCE_WIDGET)) setVisible(W(node, wn), source === src);

    const lT = W(node, "section_layers");
    setVisible(lT, !off);
    const allowed = LAYERS.filter((l) => !simple || SIMPLE_ONLY.includes(l));
    const lOpen = !off && sectionLabel(lT, "LAYERS", allowed.filter((l) => isSet(node, l)).length);
    for (const l of LAYERS) setVisible(W(node, l), lOpen && allowed.includes(l));

    const aT = W(node, "section_advanced");
    setVisible(aT, !off);
    const aOpen = !off && sectionLabel(aT, "ADVANCED", 0);
    for (const a of ADV) setVisible(W(node, a), aOpen);
    fit(node);
}

app.registerExtension({
    name: "SettingAtlas.UI",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name === NODE) hookNode(nodeType, refresh);
    },
});
