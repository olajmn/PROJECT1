/**
 * Copy the project map as ordinary text (classic ASCII tree).
 * Built from mapFamily — same who-under-who as the live map.
 */
import { asciiStem, layoutFamily, } from "./mapFamily.js";
function branch(isLast) {
    return isLast ? "└── " : "├── ";
}
function fullStem(node, underName) {
    return underName ? `    ${asciiStem(node)}` : asciiStem(node);
}
function pushAir(lines, stem) {
    lines.push(`${stem}│`);
    lines.push(`${stem}│`);
}
function parentOf(layout, node) {
    if (!node.parentId)
        return null;
    return layout.find((n) => n.id === node.parentId) ?? null;
}
/** Full map as a monospace tree string (identity + name + middle). */
export function copyAsText(name, middle, identityLabel, options) {
    const air = options?.airBetweenSiblings !== false;
    const lines = [];
    const identity = (identityLabel || "").trim();
    const underName = Boolean(identity);
    const layout = layoutFamily(middle);
    if (identity) {
        lines.push(identity);
        lines.push(`${branch(true)}${name}`);
    }
    else {
        lines.push(name);
    }
    for (let i = 0; i < layout.length; i++) {
        const n = layout[i];
        const stem = fullStem(n, underName);
        lines.push(`${stem}${branch(n.isLastSibling)}${n.label}`);
        if (!air)
            continue;
        const nextDepth = i + 1 < layout.length ? layout[i + 1].depth : -1;
        // Leaf with a following sibling: air before that sibling.
        if (!n.hasChildren && !n.isLastSibling) {
            pushAir(lines, stem);
            continue;
        }
        // Leaving a subtree: air for each finished parent that continues.
        if (n.depth > nextDepth) {
            let cur = n;
            while (cur && cur.depth > nextDepth) {
                if (cur.isLastSibling) {
                    const parent = parentOf(layout, cur);
                    if (parent && !parent.isLastSibling) {
                        pushAir(lines, fullStem(parent, underName));
                    }
                    cur = parent;
                }
                else {
                    break;
                }
            }
        }
    }
    return lines.join("\n");
}
