
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
        fill: "#898989"
    })));

    return defs
}


export function renderEdge({ from, to }, positions) {
    const { nodeWidth, nodeHeight } = CONFIG.dimensions;
    const start = positions[from];
    const end = positions[to];

    if (!start || !end) return;

    const start_x = start.x + nodeWidth;  // Source node's right edge
    const end_x = end.x;                // Target node's left edge
    const start_y = start.y + (nodeHeight / 2); // Source's middle of edge 
    const end_y = end.y + (nodeHeight / 2); //Target's middle of edge 

    // Midpoint between the two nodes as the control point for the line's curve
    const midX = (start_x + end_x) / 2;

    // Bezier curve path format: 
    // M [START_X] [START_Y] C [CP1_X] [CP1_Y], [CP2_X] [CP2_Y], [END_X] [END_Y]
    const pathData = `M ${start_x} ${start_y} C ${midX} ${start_y}, ${midX} ${end_y}, ${end_x} ${end_y}`;

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


