import { createSvgElement } from "../utils.js";
import { CONFIG } from "../config.js";

export function renderNode(node, pos, model, highlight) {

    const { nodeWidth, nodeHeight } = CONFIG.dimensions
    const isForeach = node.type === "foreach";

    // SVG <rect> element anchors at top-left corner
    const topLeft = pos;

    // Color of each node
    const fillColor = node.status
        ? (CONFIG.status[node.status])
        : (CONFIG.nodeTypes[node.type]);

    // We combine all the elements of the node into a group which becomes our final node
    const group = createSvgElement("g", {
        class: `node-group ${isForeach ? 'node-foreach' : ''}`,
        "data-step": node.id
    });

    // Add the box and label of the node
    group.appendChild(createNodeBox(topLeft, nodeWidth, nodeHeight, fillColor));
    group.appendChild(createNodeLabel(node.id, topLeft, nodeWidth, nodeHeight));

    // Add the type of the node
    const badgeY = topLeft.y + 10;
    const badgeLabel = (node.status || node.type).toUpperCase();
    group.appendChild(createBadgeElement(badgeLabel, topLeft.x + 6, badgeY));

    // Add the task count of the node and the click event for the foreach type node
    if (isForeach) {
        group.appendChild(createForeachCountBadge(node.foreach, node.status, topLeft.x + nodeWidth - 6, badgeY));
        setupForeachInteractions(group, node.id, model);
    }

    // Hover event on the node enables focus highlight
    group.onmouseenter = () => highlight(node.id);
    group.onmouseleave = () => highlight(null);

    return group;
}

// Creates Box For the Node
function createNodeBox(pos, width, height, fill) {
    return createSvgElement("rect", {
        x: pos.x, y: pos.y, rx: 8,
        width, height, fill,
        class: "dag-node-rect"
    });
}

// Displays Name of the Node
function createNodeLabel(label, pos, width, height) {
    const container = createSvgElement("foreignObject", {
        x: pos.x + 10, y: pos.y,
        width: width - 20, height: height
    });

    const div = document.createElement("div");
    div.setAttribute("xmlns", "http://www.w3.org/1999/xhtml");
    div.className = "dag-node-label";
    div.style.lineHeight = `${height}px`;
    div.textContent = label;
    div.title = label;

    container.appendChild(div);
    return container;
}

// Displays Type of the Node
function createBadgeElement(text, x, y, anchor = "start") {
    return createSvgElement("text", {
        x, y, class: "dag-node-badge",
        style: anchor === "end" ? "text-anchor: end" : ""
    }, text);
}

// If foreach type node, displays the task count
function createForeachCountBadge(data, nodeStatus, x, y) {
    const finished = !nodeStatus ? "---" : data.finished;
    const total = data.total === -1 ? "---" : data.total;
    return createBadgeElement(`${finished} / ${total}`, x, y, "end");
}

// Enables click event for foreach type node to toggle the dropdown menu
function setupForeachInteractions(group, id, model) {
    group.onclick = (e) => {
        e.stopPropagation();
        const active = model.get("activeDropMenus") || [];
        const isClosing = active.includes(id);

        const updatedActiveMenus = isClosing
            ? active.filter(i => i !== id)
            : [...active, id];

        model.set("activeDropMenus", updatedActiveMenus);
        model.save_changes();
    };
}

// Change the status of each node
export function changeNodeStatus(svg, nodes) {
    if (!svg) return;

    nodes.forEach(node => {
        const group = svg.querySelector(`.node-group[data-step="${node.id}"]`);
        if (!group) return;

        // Update rect fill color
        const rect = group.querySelector(".dag-node-rect");
        if (rect) {
            const fillColor = node.status
                ? CONFIG.status[node.status]
                : CONFIG.nodeTypes[node.type];
            rect.setAttribute("fill", fillColor);
        }

        // Update status badge text
        const badges = group.querySelectorAll(".dag-node-badge");
        if (badges[0]) {
            badges[0].textContent = (node.status || node.type).toUpperCase();
        }

        // Update foreach count
        if (node.type === "foreach" && badges[1]) {
            const finished = !node.status ? "---" : node.foreach.finished;
            const total = node.foreach.total === -1 ? "---" : node.foreach.total;
            badges[1].textContent = `${finished} / ${total}`;
        }
    });
}