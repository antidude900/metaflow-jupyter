import { getLayout, createSvgElement, getNextSteps } from "./utils.js";
import { renderHeader, changeHeaderStatus } from "./components/header.js";
import { renderEdge, arrowHead } from "./components/edge.js";
import { renderNode, changeNodeStatus } from "./components/node.js";
import { renderForeachDropdown, changeDropdownStatus } from "./components/dropdown.js";

function render({ model, el }) {
    // Initializing the DOM with SVG and Overlay layers
    // SVG Layer: For Rendering the DAG structure (nodes, edges, headers)
    // Overlay Layer: For Rendering Dropdowns
    el.innerHTML = `
        <div class="dag-widget-container">
            <div id="svgLayer"></div>
            <div id="overlayLayer"></div>
        </div>
    `;

    const svgLayer = el.querySelector("#svgLayer");
    const overlayLayer = el.querySelector("#overlayLayer");
    let layout, nodePositions;


    // Render DAG
    const renderDag = () => {
        const state = {
            nodes: model.get("nodes"),
            edges: model.get("edges"),
            flowName: model.get("flow_name"),
            subtitle: model.get("subtitle"),
            globalStatus: model.get("executionStatus")
        };


        // Compute the layout of the DAG
        // (position of each node and the size of canvas for svg on which we put other svg elements)
        if (!layout) {
            layout = getLayout(state.nodes);
            nodePositions = layout.positions;
        }

        const svg = createSvgElement("svg", {
            width: layout.width,
            height: layout.height,
            viewBox: `0 0 ${layout.width} ${layout.height}`
        });

        // 4. Render Header Part
        svg.appendChild(renderHeader({
            flowName: state.flowName,
            subtitle: state.subtitle,
            status: state.globalStatus,
            canvasWidth: layout.width
        }));

        // Making arrowHead for the edge's line 
        svg.appendChild(arrowHead());

        // Render the edges
        state.edges.forEach(edge => {
            if (nodePositions[edge.from] && nodePositions[edge.to]) {
                svg.appendChild(renderEdge(edge, nodePositions));
            }
        });

        // Render the nodes
        state.nodes.forEach(node => {
            if (nodePositions[node.id]) {
                svg.appendChild(renderNode(node, nodePositions[node.id], model, renderFocusHighlight));
            }
        });

        // Insert our svg canvas in the svgLayer of our DOM
        svgLayer.innerHTML = "";
        svgLayer.appendChild(svg);

    };


    // Render the foreach dropdown
    const renderOverlay = () => {
        // Get list of all those nodes whose dropdown is active
        const activeIds = model.get("activeDropMenus") || [];
        const nodes = model.get("nodes");

        // Remove those dropdowns from the DOM who are no longer active
        overlayLayer.querySelectorAll('.dag-dropdown-container').forEach(el => {
            const step_id = el.getAttribute('data-step');
            if (!activeIds.includes(step_id)) {
                el.remove();
            }
        });

        // Add those dropdowns to the DOM who are active but not there
        activeIds.forEach(id => {
            const alreadyExists = overlayLayer.querySelector(`[data-step="${id}"]`);
            if (!alreadyExists) {
                const node = nodes.find(n => n.id === id);
                if (node?.foreach && nodePositions?.[id]) {
                    const dropdown = renderForeachDropdown(node, nodePositions[id], model);
                    overlayLayer.appendChild(dropdown);
                }
            }
        });
    };


    // Apply focus highlight to the nodes and edges when hovered
    const renderFocusHighlight = (focusedNodeId) => {
        const svg = svgLayer.querySelector("svg");
        if (!svg) return;

        // Get all steps for the focused highlight
        const nextSteps = focusedNodeId
            ? getNextSteps(focusedNodeId, model.get("edges"))
            : null;

        // Check every node if they are in the list of steps
        // If not, dim them
        svg.querySelectorAll(".node-group").forEach(group => {
            const stepId = group.getAttribute("data-step");
            const isVisible = !nextSteps || nextSteps.has(stepId);
            group.style.opacity = isVisible ? "1" : "0.25";
        });

        // Check every edge if they are in the list of steps
        // If not, dim them
        svg.querySelectorAll(".dag-edge-path").forEach(path => {
            const from = path.getAttribute("data-from");
            const to = path.getAttribute("data-to");
            const isVisible = !nextSteps || (nextSteps.has(from) && nextSteps.has(to));
            path.style.opacity = isVisible ? "1" : "0.25";
        });
    };


    // Set Change Listeners 
    const svg = () => svgLayer.querySelector("svg");
    model.on("change:nodes", () => changeNodeStatus(svg(), model.get("nodes")));
    model.on("change:executionStatus", () => changeHeaderStatus(svg(), model.get("executionStatus")));
    model.on("change:nodes", () => changeDropdownStatus(overlayLayer, model.get("nodes"), model.get("activeDropMenus") || [], renderOverlay));
    model.on("change:activeDropMenus", renderOverlay);

    // Initial Render
    renderDag();
    renderOverlay();
}

export default { render };