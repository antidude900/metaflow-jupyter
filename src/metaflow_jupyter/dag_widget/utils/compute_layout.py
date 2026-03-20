def compute_layout(graph):
    """
    Compute row (vertical) and column (horizontal) assignments for each node in the graph
    """
    rows = {}
    cols = {}
    occupied_in_col = {}

    for node_id in graph.sorted_nodes:
        node = graph.nodes[node_id]

        # Column calculation: One col more than the closest parent
        parents_cols = [cols[p] for p in node.in_funcs]
        node_col = max(parents_cols) + 1 if parents_cols else 0
        cols[node_id] = node_col

        # Row calculation: Try to align in middle of all parents
        parents_rows = [rows[p] for p in node.in_funcs]
        row = ((min(parents_rows) + max(parents_rows)) / 2) if parents_rows else 0

        # Multiple node may overlap in same column
        # For that we shift the later coming node to next col until we find a empty one
        occupied_in_col.setdefault(node_col, set())
        while row in occupied_in_col[node_col]:
            row += 1
        occupied_in_col[node_col].add(row)
        rows[node_id] = row

    return rows, cols
