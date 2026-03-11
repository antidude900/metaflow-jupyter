function renderHeader(svg, { flowName, subtitle, canvasWidth }) {
    if (!flowName) return 0;

    svg.appendChild(createSvgElement("text", {
        x: canvasWidth / 2,
        y: 20,
        class: "dag-title"
    }, flowName));

    if (subtitle) {
        svg.appendChild(createSvgElement("text", {
            x: canvasWidth / 2,
            y: 38,
            class: "dag-subtitle"
        }, subtitle));
        return 50;
    }

    return 32;
}