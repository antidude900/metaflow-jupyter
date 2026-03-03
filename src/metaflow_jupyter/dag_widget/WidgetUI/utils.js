function computePositions(nodes, layers, { nodeWidth, nodeHeight, horizontalGap, verticalGap, paddingL, paddingR, paddingY, headerH }) {
    const positions = {};
    const nodeMap = nodes.reduce((acc, n) => ({ ...acc, [n.id]: n }), {});

    layers.forEach((layer, lIndex) => {
        const x = paddingL + lIndex * (nodeWidth + horizontalGap) + nodeWidth / 2;
        layer.forEach((id) => {
            const row = nodeMap[id].row || 0;
            positions[id] = {
                x,
                y: paddingY + row * (nodeHeight + verticalGap) + nodeHeight / 2 + headerH,
            };
        });
    });
    return positions;
}

function computeCanvasSize(nodes, layers, { nodeWidth, nodeHeight, horizontalGap, verticalGap, paddingL, paddingR, paddingY, headerH }) {
    const graphWidth = layers.length * (nodeWidth + horizontalGap) - horizontalGap;
    const canvasWidth = paddingL + graphWidth + paddingR;
    const maxRow = Math.max(...nodes.map((n) => n.row || 0));
    const canvasHeight = paddingY * 2 + (maxRow + 1) * (nodeHeight + verticalGap) - verticalGap + headerH;
    return { width: canvasWidth, height: canvasHeight };
}

function createSvgElement(tag, attributes = {}, ...children) {
    const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [key, value] of Object.entries(attributes)) {
        element.setAttribute(key, value);
    }
    for (const child of children) {
        if (typeof child === "string") {
            element.textContent = child;
        } else if (child) {
            element.appendChild(child);
        }
    }
    return element;
}