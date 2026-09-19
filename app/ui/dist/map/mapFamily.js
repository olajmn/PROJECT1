/**
 * Who-under-who for the project map (parent / sibling / depth).
 * mapLines and copyAsText consume this; they don't re-derive hierarchy.
 */
/** Flat, pre-order walk of the progression middle tree. */
export function layoutFamily(middle, parentId = null, depth = 0, ancestorContinues = []) {
    const out = [];
    const count = middle.length;
    middle.forEach((node, i) => {
        const isLast = i === count - 1;
        const hasChildren = node.children.length > 0;
        const entry = {
            id: node.id,
            label: node.label,
            status: node.status,
            depth,
            parentId,
            siblingIndex: i,
            siblingCount: count,
            isLastSibling: isLast,
            hasChildren,
            isParent: hasChildren,
            isChild: depth > 0,
            ancestorContinues: ancestorContinues.slice(),
        };
        out.push(entry);
        if (hasChildren) {
            out.push(...layoutFamily(node.children, node.id, depth + 1, [
                ...ancestorContinues,
                !isLast,
            ]));
        }
    });
    return out;
}
/** Index by id for DOM / SVG lookups. */
export function familyById(layout) {
    return new Map(layout.map((n) => [n.id, n]));
}
/** Stamp structural attrs on a map row element. */
export function applyFamilyAttrs(row, node) {
    row.dataset.stepId = node.id;
    row.dataset.depth = String(node.depth);
    row.dataset.parentId = node.parentId ?? "";
    row.dataset.siblingIndex = String(node.siblingIndex);
    row.dataset.isLast = node.isLastSibling ? "1" : "0";
    row.dataset.hasChildren = node.hasChildren ? "1" : "0";
    row.dataset.isParent = node.isParent ? "1" : "0";
    row.dataset.isChild = node.isChild ? "1" : "0";
}
/** Classic ASCII stem before ├── / └── for this family node. */
export function asciiStem(node) {
    return node.ancestorContinues
        .map((continues) => (continues ? "│   " : "    "))
        .join("");
}
