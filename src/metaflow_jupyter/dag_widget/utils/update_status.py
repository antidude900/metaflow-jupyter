from .extract_foreach_labels import extract_live_foreach_labels


def update_status(nodes, run, flow_cls, foreach_labels):
    """
    Check the live run and return nodes updated with their current execution status
    """
    graph = flow_cls._graph


    # Find nodes currently marked as running
    running = [node for node in nodes if node.get("status") == "running"]

    # we only check those nodes which are running for status update 
    if not running:
        return nodes

    updates = {}

    # Status lookup to make the next node running (If join node, then has to rely on multiple nodes to get started)
    node_status = {node["id"]: node["status"] for node in nodes}

    for node in running:
        nid = node["id"]

        #extract all its tasks for the node's status check
        try:
            tasks = list(run[nid].tasks())
        except Exception:
            continue
        if not tasks:
            continue

        # if any task fails, the step fails
        def _failed(t):
            return (t.finished and not t.successful) or bool(t.exception)
        if any(_failed(t) for t in tasks):
            status = "failed"
        
        # if all tasks are completed and succuessfull, the step is completed
        elif all(t.finished and t.successful for t in tasks):
            status = "completed"

        # otherwise it is still running
        else:
            status = "running"

        # If this is a foreach node and its labels aren't resolved yet, try to resolve from live task data
        if node["type"] == "foreach" and nid not in foreach_labels:
            extract_live_foreach_labels(foreach_labels, run, graph)

        # we need to check status of each label of foreach node 
        # (cant use task in tasks as they might not still be loaded for execution)
        labels = foreach_labels.get(nid)
        foreach_status = None
        if labels:
            # sort the tasks by their id to ensure they are in the same order as labels
            # (Note: each task in step.tasks() only gets recorded after creation, so we sort numerically to align with labels)
            sorted_tasks = sorted(tasks, key=lambda t: int(t.id))

            def _task_status(index, _sorted=sorted_tasks):
                # the index of the item is greater or equal to the total number of tasks of step.tasks()
                # which means its execution is not completed yet and thus not loaded in step.tasks()
                if index >= len(_sorted):
                    return "pending"
                t = _sorted[index]
                return "completed" if t.successful else "failed" if _failed(t) else "running"
            
            # store the total number of tasks, how many are completed and the status of each task
            foreach_status = {
                "total": len(labels),
                "finished": sum(1 for t in tasks if t.finished or _failed(t)),
                "tasks": [{"label": labels[i], "status": _task_status(i)} for i in range(len(labels))],
            }

        # store the new updated status and also change the statsu of Status lookup for next nodde status decision 
        updates[nid] = {"status": status, **({"foreach": foreach_status} if foreach_status else {})}
        node_status[nid] = status

        # When a node completes, mark its children as running only if all their parents are now completed
        if status == "completed":
            for child_id in graph.nodes[nid].out_funcs:
                parents = graph.nodes[child_id].in_funcs
                if all(node_status.get(p) == "completed" for p in parents):
                    updates[child_id] = {"status": "running"}

    # update the nodes with their new status
    return [{**node, **updates[node["id"]]} if node["id"] in updates else node for node in nodes]

