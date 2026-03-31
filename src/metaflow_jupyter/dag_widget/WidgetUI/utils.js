import { CONFIG } from "./config.js";

export const getLayout = (nodes) => {
    // Calcuate the position of each nodes and the size of the svg canvas required
    // visualize the whole canvas as a grid made up of multiple cells
    const {
        nodeWidth, nodeHeight,
        horizontalGap, verticalGap,
        paddingL, paddingR, paddingY,
        headerHeight
    } = CONFIG.dimensions;

    let maxRow = 0;
    let maxCol = 0;
    const positions = {};

    // Each cell contains the node with padding around it (to space it from other nodes)
    const cellWidth = nodeWidth + horizontalGap;
    const cellHeight = nodeHeight + verticalGap;

    nodes.forEach(node => {
        // Get the row and column of the node
        const [row, col] = node.position || [0, 0];

        // Keep track of the row most below and column most right
        maxRow = Math.max(maxRow, row);
        maxCol = Math.max(maxCol, col);

        // To find our cell's horizontal position, we have to give space for other cells to its right + padding of the canvas
        const cellX = paddingL + (col * cellWidth);
        // To find our cell's vertical position, we have to give space for other cells above it + padding of the canvas + header height
        const cellY = paddingY + (row * cellHeight) + headerHeight;

        positions[node.id] = {
            x: cellX,
            y: cellY
        };
    });

    // The total width of the grid is the total no of columns times the width of each cell
    // and total height is the total no of rows times the height of each cell
    // we remove the gap to remove the unneccessary space at the end
    const totalGridWidth = (maxCol + 1) * cellWidth - horizontalGap;
    const totalGridHeight = (maxRow + 1) * cellHeight - verticalGap;

    // The total width of the canvas is the total width of the grid plus the padding on both sides
    // and total height is the total height of the grid plus the padding on both sides plus the header height
    const canvasWidth = paddingL + totalGridWidth + paddingR;
    const canvasHeight = paddingY + totalGridHeight + paddingY + headerHeight;

    return {
        positions,
        width: canvasWidth,
        height: canvasHeight
    };
};

export const createSvgElement = (tag, attrs = {}, ...children) => {
    // Helper function to create SVG Elements

    // Get the SVG element
    const element = document.createElementNS("http://www.w3.org/2000/svg", tag);

    // Set the attributes of the SVG element
    Object.entries(attrs).forEach(([k, v]) => {
        element.setAttribute(k, v);
    });

    // Append the nested elements of the SVG element
    children.forEach(child => {
        if (typeof child === "string") {
            element.textContent = child;
        } else if (child) {
            element.appendChild(child);
        }
    });

    return element;
};

export const getNextSteps = (curr_node, edges, steps = new Set([curr_node])) => {
    // Get all steps after a node including itself for the focus highlight
    // Iterate over the edges
    edges.forEach(edge => {
        // If the edge's from is the curr node and the to node is not included in the steps
        if (edge.from === curr_node && !steps.has(edge.to)) {
            // we add it to the steps list and go recursively to find next steps
            steps.add(edge.to);
            // But if the edge's from doesnt match the current node or we have already added that node to steps
            // We don't go further as we wont get any new result
            getNextSteps(edge.to, edges, steps);
        }
    });
    return steps;
};
