function renderForeachDropdown(node, pos, { nodeWidth, model }) {
    const tasks = node.foreach.tasks || [];
    const dropdownWidth = 220;
    const maxDropdownHeight = 160;

    const itemHeight = 36;
    const padding = 48;
    const totalHeight = (tasks.length > 0 ? tasks.length * itemHeight : itemHeight) + padding;
    const actualHeight = Math.min(totalHeight, maxDropdownHeight);

    const top = pos.y - actualHeight / 2;
    const left = pos.x - nodeWidth / 2 - dropdownWidth - 10;

    const div = document.createElement("div");
    div.classList.add("dag-dropdown-container");
    div.dataset.step = node.id;
    div.style.position = "absolute";
    div.style.left = `${left}px`;
    div.style.top = `${top}px`;
    div.style.width = `${dropdownWidth}px`;
    div.style.maxHeight = `${maxDropdownHeight}px`;
    div.style.height = `${actualHeight}px`;
    div.style.zIndex = "1000";

    const closeBtn = document.createElement("button");
    closeBtn.classList.add("dag-dropdown-close");
    closeBtn.innerHTML = "&times;";
    closeBtn.onclick = () => {
        const current = model.get("activeDropMenus") || [];
        const updated = current.filter(id => id !== node.id);
        model.set("activeDropMenus", updated);
        model.save_changes();
    };
    div.appendChild(closeBtn);


    const title = document.createElement("div");
    title.classList.add("dag-dropdown-title");
    title.textContent = node.id;
    title.title = `Step: ${node.id}`;
    div.appendChild(title);

    const listContainer = document.createElement("div");
    listContainer.classList.add("dag-dropdown-list");
    if (node.foreach.total === -1) {
        const empty = document.createElement("div");
        empty.classList.add("dag-dropdown-empty");
        empty.textContent = node.status ? "Items Loading..." : "Items available in Live View";
        listContainer.appendChild(empty);
    } else if (node.foreach.total === 0) {
        const empty = document.createElement("div");
        empty.classList.add("dag-dropdown-empty");
        empty.textContent = "No Items";
        listContainer.appendChild(empty);
    } else {
        tasks.forEach((task) => {
            const item = document.createElement("div");
            item.classList.add("dag-task-item", `status-${task.status}`);
            item.title = task.label;
            const span = document.createElement("span");
            span.textContent = task.label;
            item.appendChild(span);
            listContainer.appendChild(item);
        });
    }
    div.appendChild(listContainer);

    div.onclick = (e) => e.stopPropagation();

    return div;
}
