
import { createSvgElement } from "../utils.js";
import { CONFIG } from "../config.js";

export function arrowHead() {
    // Reference: https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Element/marker#drawing_arrowheads
    const defs = createSvgElement("defs");
    defs.appendChild(createSvgElement("marker", {
        id: "arrowhead",
        viewBox: "0 0 10 10",
        refX: 9,
        refY: 5,
        markerWidth: 6,
        markerHeight: 6,
        orient: "auto-start-reverse"
    }, createSvgElement("path", {
        d: "M 0 0 L 10 5 L 0 10 z",
        fill: "#94a3b8"
    })));

    return defs
}


export function renderEdge({ from, to }, positions) {
    const nodeWidth = CONFIG.dimensions.nodeWidth
    const start = positions[from];
    const end = positions[to];

    if (!start || !end) return;

    const halfWidth = nodeWidth / 2;

    // To make the arrow touch the side of the node rather than the center,
    // we account for the halfWidth
    const exitX = start.x + halfWidth;  // Source node's right edge
    const entryX = end.x - halfWidth;   // Target node's left edge

    // Midpoint between the two nodes as the control point for the line's curve
    const midX = (exitX + entryX) / 2;

    // Bezier curve path format: 
    // M [START_X] [START_Y] C [CP1_X] [CP1_Y], [CP2_X] [CP2_Y], [END_X] [END_Y]
    // where C is the curve command and CP means control points
    const pathData = `M ${exitX} ${start.y} C ${midX} ${start.y}, ${midX} ${end.y}, ${entryX} ${end.y}`;

    return (createSvgElement("path", {
        d: pathData,
        class: "dag-edge-path",
        "marker-end": "url(#arrowhead)",
        // data attributes to record the start and end nodes of the edge
        // later needed for edge traversal to find steps for focus highlight
        "data-from": from,
        "data-to": to,
    }));
}


