def compute_layout(graph):
    """
    Compute depth (in which layer) and row assignments for each node in the graph

    """
    depths = {}
    rows = {}
    layers = []
    occupied_in_layer = {}

    for node_id in graph.sorted_nodes:
        node = graph.nodes[node_id]

        # We find the deepest parent node (in layers) and set the depth of the curernt node to one more than deepest parent
        parents_depths = [depths[p] for p in node.in_funcs]
        node_depth = max(parents_depths) + 1 if parents_depths else 0
        depths[node_id] = node_depth

        # We find the topmost parent (vertically) and set it to the same row of that parent
        parents_rows = [rows[p] for p in node.in_funcs]
        row = min(parents_rows) if parents_rows else 0

        # if the row is alrady occupied, then we go below
        occupied_in_layer.setdefault(node_depth, set())
        while row in occupied_in_layer[node_depth]:
            row += 1
        occupied_in_layer[node_depth].add(row)

        # now we add the node in that layer corresponding to the node's depth in the specified row
        while node_depth >= len(layers):
            layers.append([])
        layers[node_depth].append(node_id)
        rows[node_id] = row

    return rows, layers
