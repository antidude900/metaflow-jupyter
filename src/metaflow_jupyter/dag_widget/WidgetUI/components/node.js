function renderNode(svg, node, pos, { CONFIG, model }) {
    const { nodeWidth, nodeHeight } = CONFIG.dimensions;
    const isForeach = node.type === "foreach";

    let fillColor = "#94a3b8";
    if (node.status) {
        // Live View: Strictly show status colors 
        fillColor = CONFIG.status[node.status] || "#cbd5e1";
    } else {
        // Static View: Show type colors 
        fillColor = CONFIG.nodeTypes[node.type]
    }

    const nodeGroup = createSvgElement("g");
    nodeGroup.setAttribute("class", `node-group ${isForeach ? 'node-foreach' : ''}`);
    nodeGroup.setAttribute("data-step", node.id);

    // Box
    nodeGroup.appendChild(createSvgElement("rect", {
        x: pos.x - nodeWidth / 2,
        y: pos.y - nodeHeight / 2,
        width: nodeWidth,
        height: nodeHeight,
        rx: "8",
        fill: fillColor,
        class: "dag-node-rect",
    }));

    // Label
    const labelContainer = createSvgElement("foreignObject", {
        x: pos.x - nodeWidth / 2 + 10,
        y: pos.y - nodeHeight / 2,
        width: nodeWidth - 20,
        height: nodeHeight,
    });

    const labelDiv = document.createElement("div");
    labelDiv.setAttribute("xmlns", "http://www.w3.org/1999/xhtml");
    labelDiv.classList.add("dag-node-label");
    labelDiv.style.lineHeight = `${nodeHeight}px`;
    labelDiv.textContent = node.id;
    labelDiv.title = node.id;

    labelContainer.appendChild(labelDiv);
    nodeGroup.appendChild(labelContainer);

    // Badge (Type or Foreach Count)
    let badgeText = (node.status || node.type).toUpperCase();
    nodeGroup.appendChild(createSvgElement("text", {
        x: pos.x - nodeWidth / 2 + 6,
        y: pos.y - nodeHeight / 2 + 10,
        class: "dag-node-badge",
    }, badgeText));


    if (isForeach) {
        let done = !node.status ? "---" : node.foreach.finished;
        let total = node.foreach.total === -1 ? "---" : node.foreach.total;

        nodeGroup.appendChild(createSvgElement("text", {
            x: pos.x + nodeWidth / 2 - 6,
            y: pos.y - nodeHeight / 2 + 10,
            class: "dag-node-badge",
            style: "text-anchor: end"
        }, `${done} / ${total}`));
    }

    // Click handler for foreach dropdown
    nodeGroup.onclick = (e) => {
        e.stopPropagation();
        if (isForeach) {
            // Clone the current state to avoid direct mutation
            const current = [...(model.get("activeDropMenus") || [])];
            const index = current.indexOf(node.id);

            if (index > -1) {
                // If present, remove (toggle off)
                current.splice(index, 1);
            } else {
                // If not present, add (toggle on)
                current.push(node.id);
            }

            model.set("activeDropMenus", current);
            model.save_changes();
        }
    };

    svg.appendChild(nodeGroup);
}