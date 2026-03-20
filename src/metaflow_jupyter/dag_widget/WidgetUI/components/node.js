import { createSvgElement } from "../utils.js";
import { CONFIG } from "../config.js";

export function renderNode(node, pos, model, onHover) {

    const { nodeWidth, nodeHeight } = CONFIG.dimensions
    const isForeach = node.type === "foreach";

    // 1. Resolve Layout Geometry
    const topLeft = { x: pos.x - nodeWidth / 2, y: pos.y - nodeHeight / 2 };

    // Determine Color (Live view overrides static type color)
    const fillColor = node.status
        ? (CONFIG.status[node.status] || "#cbd5e1")
        : (CONFIG.nodeTypes[node.type] || "#94a3b8");

    // 2. Initialize the Node Group
    const group = createSvgElement("g", {
        class: `node-group ${isForeach ? 'node-foreach' : ''}`,
        "data-step": node.id
    });

    // 3. Build Node Visuals Layer-by-Layer
    group.appendChild(createNodeBox(topLeft, nodeWidth, nodeHeight, fillColor));
    group.appendChild(createNodeLabel(node.id, topLeft, nodeWidth, nodeHeight));

    // 4. Primary Metadata Badge (Status / Type)
    const badgeY = topLeft.y + 10;
    const badgeLabel = (node.status || node.type).toUpperCase();
    group.appendChild(createBadgeElement(badgeLabel, topLeft.x + 6, badgeY));

    // 5. Foreach Extensions (Secondary Progress Badge + Hover Toggle)
    if (isForeach) {
        group.appendChild(createForeachCountBadge(node.foreach, node.status, topLeft.x + nodeWidth - 6, badgeY));
        setupForeachInteractions(group, node.id, model);
    }

    // 6. Global Node Events
    group.onmouseenter = () => onHover?.(node.id);
    group.onmouseleave = () => onHover?.(null);

    return group;
}

// --- Internal Visual Components (Helpers) ---

function createNodeBox(pos, width, height, fill) {
    return createSvgElement("rect", {
        x: pos.x, y: pos.y, rx: 8,
        width, height, fill,
        class: "dag-node-rect"
    });
}

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

function createBadgeElement(text, x, y, anchor = "start") {
    return createSvgElement("text", {
        x, y, class: "dag-node-badge",
        style: anchor === "end" ? "text-anchor: end" : ""
    }, text);
}

function createForeachCountBadge(data, nodeStatus, x, y) {
    const finished = !nodeStatus ? "---" : data.finished;
    const total = data.total === -1 ? "---" : data.total;
    return createBadgeElement(`${finished} / ${total}`, x, y, "end");
}

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