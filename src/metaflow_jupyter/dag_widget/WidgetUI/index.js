import { getLayout, createSvgElement, getNextSteps } from "./utils.js";
import { renderHeader } from "./components/header.js";
import { renderEdge, arrowHead } from "./components/edge.js";
import { renderNode } from "./components/node.js";
import { renderForeachDropdown } from "./components/dropdown.js";

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
    let layout;

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
        if (!layout) layout = getLayout(state.nodes);
        const nodePositions = layout.positions;

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
                svg.appendChild(renderNode(node, nodePositions[node.id], model, applyFocusHighlight));
            }
        });

        // Insert our svg canvas in the svgLayer of our DOM
        svgLayer.innerHTML = "";
        svgLayer.appendChild(svg);

    };

    // Apply focus highlight to the nodes and edges when hovered
    const applyFocusHighlight = (focusedNodeId) => {
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
            group.style.opacity = isVisible ? "1" : "0.15";
        });

        // Check every edge if they are in the list of steps
        // If not, dim them
        svg.querySelectorAll(".dag-edge-path").forEach(path => {
            const from = path.getAttribute("data-from");
            const to = path.getAttribute("data-to");
            const isVisible = !nextSteps || (nextSteps.has(from) && nextSteps.has(to));
            path.style.opacity = isVisible ? "1" : "0.1";
        });
    };


    // Render the foreach dropdown
    const renderOverlay = () => {
        // Clear the old overlays and render fresh ones (if not, then duplicates will appear)
        overlayLayer.innerHTML = "";

        // Get list of all those nodes whose dropdown is active
        const activeIds = model.get("activeDropMenus") || [];
        const nodes = model.get("nodes");

        // For each of the active nodes, render the dropdown
        activeIds.forEach(id => {
            const node = nodes.find(n => n.id === id);
            if (node?.foreach && nodePositions[id]) {
                const dropdown = renderForeachDropdown(node, nodePositions[id], model);
                overlayLayer.appendChild(dropdown);
            }
        });
    };

    // Sync the items in the dropdown with the new status of the node's tasks
    const syncDropdownStatus = () => {
        // Get list of all those nodes whose dropdown is active
        const activeIds = model.get("activeDropMenus") || [];
        const nodes = model.get("nodes");

        // We access each dropdown's DOM element with the custom attribute we set to it: data-step=node_id
        activeIds.forEach(id => {
            const nodeState = nodes.find(n => n.id === id);
            const existingDropdown = overlayLayer.querySelector(`[data-step="${id}"]`);

            if (!existingDropdown || !nodeState?.foreach?.tasks) return;

            // Get all the task items of  the dropdown
            const listItems = existingDropdown.querySelectorAll(".dag-task-item");

            // Check if the tasks count in the node state is equal to task count in the dropdown
            // The task count may change if task fetch before failed and then later was successfull
            const isQuantitySynced = nodeState.foreach.tasks.length === listItems.length;

            if (isQuantitySynced) {
                // Update the status of each task 
                // Simply changing the status- classname which changes its color CSS
                nodeState.foreach.tasks.forEach((task, index) => {
                    listItems[index].className = `dag-task-item status-${task.status}`;
                });
            } else {
                // if the task count changed, trigger full overlay re-render of that node to display the new tasks
                // else just the status change only requires changing the classname of the task item 
                renderOverlay();
            }
        });
    };

    // Set Change Listeners to each of the given states and re-render DAG on change
    const listenForChange = ["nodes", "edges", "flow_name", "subtitle", "executionStatus"];
    listenForChange.forEach(key => model.on(`change:${key}`, renderDag));

    // When node changes, sync the item in the dropdown with the node's status
    model.on("change:nodes", syncDropdownStatus);

    // Check for dropdown open/close actios and render the active ones
    model.on("change:activeDropMenus", renderOverlay);

    // Intiail Render
    renderDag();
    renderOverlay();
}

export default { render };
