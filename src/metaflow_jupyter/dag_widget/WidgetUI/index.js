function render({ model, el }) {
    el.classList.add("dag-widget-el");

    const container = document.createElement("div");
    container.classList.add("dag-widget-container");
    el.appendChild(container);

    const svgLayer = document.createElement("div");
    const overlayLayer = document.createElement("div");
    container.appendChild(svgLayer);
    container.appendChild(overlayLayer);

    let positions = {};

    const drawSvg = () => {
        const nodes = model.get("nodes");
        const edges = model.get("edges");
        const layers = model.get("layers");
        const flowName = model.get("flow_name");
        const subtitle = model.get("subtitle");
        const executionStatus = model.get("executionStatus");

        const { nodeWidth } = CONFIG.dimensions;
        const headerParams = { flowName, subtitle };

        const tempSvg = createSvgElement("svg");
        const headerH = renderHeader(tempSvg, { ...headerParams, canvasWidth: 0 });

        const layoutParams = { ...CONFIG.dimensions, headerH };
        positions = computePositions(nodes, layers, layoutParams);
        const { width: canvasWidth, height: canvasHeight } = computeCanvasSize(nodes, layers, layoutParams);
        const graphWidth = canvasWidth - layoutParams.paddingL - layoutParams.paddingR;

        const svg = createSvgElement("svg", {
            width: canvasWidth,
            height: canvasHeight,
            viewBox: `0 0 ${canvasWidth} ${canvasHeight}`,
        });

        svg.appendChild(
            createSvgElement("defs", {},
                createSvgElement("marker", {
                    id: "arrowhead",
                    markerWidth: "10",
                    markerHeight: "7",
                    refX: "9",
                    refY: "3.5",
                    orient: "auto",
                }, createSvgElement("polygon", { points: "0 0, 10 3.5, 0 7", fill: "#94a3b8" }))
            )
        );

        renderHeader(svg, { ...headerParams, canvasWidth: layoutParams.paddingL * 2 + graphWidth });
        edges.forEach(edge => {
            if (positions[edge.from] && positions[edge.to])
                renderEdge(svg, edge, positions, { nodeWidth });
        });
        nodes.forEach(node => {
            const pos = positions[node.id];
            if (pos) renderNode(svg, node, pos, { ...CONFIG.dimensions, CONFIG, model });
        });

        svgLayer.innerHTML = "";
        svgLayer.appendChild(svg);

        if (executionStatus) {
            const loading = document.createElement("div");
            loading.classList.add("dag-loading");
            loading.textContent = executionStatus;
            svgLayer.appendChild(loading);
        }
    };

    // Full redraw of dropdowns — only triggered when menus open/close
    const drawOverlay = () => {
        const nodes = model.get("nodes");
        const activeDropMenus = model.get("activeDropMenus") || [];
        const { nodeWidth } = CONFIG.dimensions;

        overlayLayer.innerHTML = "";
        activeDropMenus.forEach(nodeId => {
            const activeNode = nodes.find(n => n.id === nodeId);
            if (activeNode?.foreach)
                overlayLayer.appendChild(renderForeachDropdown(activeNode, positions[nodeId], { nodeWidth, model }));
        });
    };

    // Patch task status classes in-place — preserves scroll position on every status poll.
    // Falls back to a full drawOverlay() if the rendered item count has changed
    // (e.g. empty-state dropdown just received its first real task list).
    const updateDropMenu = () => {
        const nodes = model.get("nodes");
        const activeDropMenus = model.get("activeDropMenus") || [];
        let needsFullRedraw = false;

        activeDropMenus.forEach(nodeId => {
            const activeNode = nodes.find(n => n.id === nodeId);
            if (!activeNode?.foreach?.tasks) return;

            const dropdown = overlayLayer.querySelector(`[data-step="${nodeId}"]`);
            if (!dropdown) return;

            const existingItems = dropdown.querySelectorAll(".dag-task-item");
            if (existingItems.length !== activeNode.foreach.tasks.length) {
                needsFullRedraw = true;
                return;
            }

            activeNode.foreach.tasks.forEach((task, i) => {
                if (existingItems[i]) existingItems[i].className = `dag-task-item status-${task.status}`;
            });
        });

        if (needsFullRedraw) drawOverlay();
    };

    model.on("change:nodes", () => { drawSvg(); updateDropMenu(); });
    model.on("change:edges", drawSvg);
    model.on("change:layers", drawSvg);
    model.on("change:flow_name", drawSvg);
    model.on("change:subtitle", drawSvg);
    model.on("change:executionStatus", drawSvg);
    model.on("change:activeDropMenus", drawOverlay);

    drawSvg();
    drawOverlay();
}

export default { render };
