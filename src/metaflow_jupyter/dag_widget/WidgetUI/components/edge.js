function renderEdge(svg, { from, to }, positions, { nodeWidth }) {
  const start = positions[from];
  const end = positions[to];
  if (!start || !end) return;

  const midX = (start.x + nodeWidth / 2 + end.x - nodeWidth / 2) / 2;
  const pathData = `M ${start.x + nodeWidth / 2} ${start.y} C ${midX} ${start.y}, ${midX} ${end.y}, ${end.x - nodeWidth / 2} ${end.y}`;

  svg.appendChild(createSvgElement("path", {
    d: pathData,
    class: "dag-edge-path",
    "marker-end": "url(#arrowhead)",
  }));
}