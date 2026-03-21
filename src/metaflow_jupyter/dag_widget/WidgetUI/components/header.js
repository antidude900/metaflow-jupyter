import { createSvgElement } from "../utils.js";

export function renderHeader({ flowName, subtitle, status, canvasWidth }) {
    if (!flowName) return null;

    // Create a contianer for all the header elements
    const headerGroup = createSvgElement("g", { class: "dag-header" });

    // Vertical Positioning for our header elements
    const TITLE_Y = 24;
    const SUBTITLE_Y = 44;
    const STATUS_X = 75;

    // Title
    headerGroup.appendChild(createSvgElement("text", {
        x: canvasWidth / 2,
        y: TITLE_Y,
        class: "dag-title"
    }, flowName));

    // Subtitle
    if (subtitle) {
        headerGroup.appendChild(createSvgElement("text", {
            x: canvasWidth / 2,
            y: SUBTITLE_Y,
            class: "dag-subtitle"
        }, subtitle));
    }

    // Execution Status
    if (status) {
        headerGroup.appendChild(createSvgElement("text", {
            x: STATUS_X,
            y: TITLE_Y,
            class: "dag-header-status",
            style: "text-anchor: end"
        }, status.toUpperCase()));
    }

    return headerGroup;
}