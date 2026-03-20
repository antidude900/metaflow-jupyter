import { CONFIG } from "../config.js";

export function renderForeachDropdown(node, pos, model) {
    const tasks = node.foreach.tasks || [];
    const nodeWidth = CONFIG.dimensions.nodeWidth

    // Dimension Configuration of the dropdown
    const dropdownConfig = {
        width: 220,
        maxHeight: 160,
        itemHeight: 36,
        padding: 48,
        gapFromNode: 10
    };

    // Calculate Dimensions taking the items in the dropdown and the padding in account
    const DropdownHeight = (tasks.length > 0 ? tasks.length * dropdownConfig.itemHeight : dropdownConfig.itemHeight) + dropdownConfig.padding;
    const finalDropdownHeight = Math.min(DropdownHeight, dropdownConfig.maxHeight);

    // Align to the left top of the target node
    const containerLeft = pos.x - (nodeWidth / 2) - dropdownConfig.width - dropdownConfig.gapFromNode;
    const containerTop = pos.y - (finalDropdownHeight / 2);

    // Build the container for the dropdown and position it 
    const container = document.createElement("div");
    container.className = "dag-dropdown-container";
    container.dataset.step = node.id;

    Object.assign(container.style, {
        position: "absolute",
        left: `${containerLeft}px`,
        top: `${containerTop}px`,
        width: `${dropdownConfig.width}px`,
        height: `${finalDropdownHeight}px`,
        maxHeight: `${dropdownConfig.maxHeight}px`,
        zIndex: "1000"
    });

    // Close button for the dropdown
    const closeBtn = document.createElement("button");
    closeBtn.className = "dag-dropdown-close";
    closeBtn.innerHTML = "&times;";
    closeBtn.onclick = () => {
        const currentActive = model.get("activeDropMenus") || [];
        model.set("activeDropMenus", currentActive.filter(id => id !== node.id));
        model.save_changes();
    };
    container.appendChild(closeBtn);

    // Title for the dropdown
    const title = document.createElement("div");
    title.className = "dag-dropdown-title";
    title.textContent = node.id;
    title.title = `Step: ${node.id}`;
    container.appendChild(title);

    // Task List
    const listContainer = document.createElement("div");
    listContainer.className = "dag-dropdown-list";

    // If the list of tasks is empty or pending, display a message
    const isPending = node.foreach.total === -1;
    const isEmpty = node.foreach.total === 0;

    if (isPending) {
        const placeholderText = node.status ? "Loading tasks..." : "Requires live execution";
        listContainer.appendChild(createDropdownMessage(placeholderText));
    } else if (isEmpty) {
        listContainer.appendChild(createDropdownMessage("No tasks found"));
    } else {
        // Else render the tasks with each having a classname defining their status
        tasks.forEach((task) => {
            const item = document.createElement("div");
            item.className = `dag-task-item status-${task.status}`;
            item.title = task.label;

            const taskLabel = document.createElement("span");
            taskLabel.textContent = task.label;

            item.appendChild(taskLabel);
            listContainer.appendChild(item);
        });
    }

    container.appendChild(listScrollContainer);
    container.onclick = (e) => e.stopPropagation();

    return container;
}

// Helper function to create message element for the empty/pending states
function createDropdownMessage(text) {
    const msgElement = document.createElement("div");
    msgElement.className = "dag-dropdown-empty";
    msgElement.textContent = text;
    return msgElement;
}
