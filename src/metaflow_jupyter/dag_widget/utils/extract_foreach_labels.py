import inspect, ast, textwrap


def extract_static_foreach_labels(flow_cls, graph):
    """
    Parse each foreach step's source to AST tree to extract item labels statically.
    """
    foreach_tasks = {}
    for nid, node in graph.nodes.items():
        if node.type != "foreach":
            continue
        labels = None
        try:

            # Get the variable name passed to foreach_param in self.next()
            varname = node.foreach_param

            # pulls the raw python source and parses into the ast
            src = textwrap.dedent(inspect.getsource(getattr(flow_cls, nid)))
            tree = ast.parse(src)

            # Find the value of the variable
            if varname:
                # Get the function definition (the first body element)
                func_def = tree.body[0]

                # Iterate through top-level statements
                for statement in func_def.body:
                    # Check if the statement is a top-level assignment
                    if isinstance(statement, ast.Assign):
                        for target in statement.targets:
                            if isinstance(target, ast.Attribute) and target.attr == varname:
                                labels = [str(i) for i in ast.literal_eval(statement.value)]

                    # Check for ANY nested assignments to the same variable
                    for ast_node in ast.walk(statement):
                        # Skip the statement itself (only check nested nodes)
                        if ast_node is statement:
                            continue
                        if isinstance(ast_node, ast.Assign):
                            for target in ast_node.targets:
                                if isinstance(target, ast.Attribute) and target.attr == varname:
                                    # Found nested assignment - can't be certain, fall back to dynamic
                                    labels = None
                                    break
        except Exception:
            pass
        foreach_tasks[node.out_funcs[0]] = labels
    return foreach_tasks


def extract_live_foreach_labels(foreach_labels, run, graph):
    """
    For dynamic foreach nodes not yet in foreach_labels, attempt to read their
    item list from live task data. Mutates foreach_labels in-place.
    Called only when there are still unresolved foreach nodes.
    """
    for nid, node in graph.nodes.items():
        if node.type != "foreach" or node.out_funcs[0] in foreach_labels:
            continue
        try:
            items = getattr(list(run[nid].tasks())[0].data, node.foreach_param)
            foreach_labels[node.out_funcs[0]] = [str(i) for i in items]
        except Exception:
            pass
