from .compute_layout import compute_layout
from .extract_foreach_labels import extract_static_foreach_labels
from metaflow.lint import linter


def extract_graph(flow_cls):
    """
    Parse FlowSpec graph into nodes, edges, and position for UI
    """
    graph = flow_cls._graph

    # Validate the flow structure before extracting
    linter.run_checks(graph)
    """
    We calibrate the graph to match the widget UI design:

    1. If the node is of type 'split' or 'foreach', we are renaming it to type 'linear' for initializtion 
    If later found to be of type foreach, then will be changed to that type
    We are removing the type 'split' as the arrows already show the splitting 
    So the classification becomes simple of whether a node is linear, foreach or join

    2. If the node is of type 'foreach', we are renaming it to type 'linear' and giving the type 'foreach' to the child node

    3. We explicitly override the types for the 'start' and 'end' nodes to their respective names
    """
    calibrate = {}
    for node_id, node in graph.nodes.items():
        if node_id not in calibrate:
            calibrate[node_id] = "linear" if node.type in ("split", "foreach") else node.type
        for child_id in node.out_funcs:
            if node.type == "foreach":
                calibrate[child_id] = "foreach"
        if node_id in ("start", "end"):
            calibrate[node_id] = node_id

    # Calculate the position of each node in the graph
    rows, columns = compute_layout(graph)

    # extract the labels for the tasks of foreach node
    foreach_child = extract_static_foreach_labels(flow_cls, graph)

    # Store the name, type, position and tasks of each node
    nodes = [
        {"id": nid, "type": calibrate[nid], "position": [rows[nid], columns[nid]], **({
            "foreach": {
                "total": len(foreach_child[nid]) if foreach_child[nid] is not None else -1,
                "finished": 0,
                "tasks": [{"label": l, "status": "pending"} for l in foreach_child[nid]] if foreach_child[nid] else [],
            }
        } if nid in foreach_child else {})}
        for nid in graph.sorted_nodes
    ]

    # Store the connection info between nodes
    edges = [
        {"from": node_id, "to": next_id}
        for node_id in graph.sorted_nodes
        for next_id in graph.nodes[node_id].out_funcs
        if next_id in rows
    ]

    return nodes, edges