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

            # Find the variable name passed to foreach= in self.next()
            foreach_param = node.foreach_param

            # pulls the raw python source and parses into the ast
            src = textwrap.dedent(inspect.getsource(getattr(flow_cls, nid)))
            tree = ast.parse(src)

            # Find the value of the variable
            if foreach_param:
                for statement in ast.walk(tree):
                    # check if the statement is an assignment statement
                    if isinstance(statement, ast.Assign):
                        # as python supports multi-assignment, statement.targets returns a list
                        for target in statement.targets:
                            # it should have a attribute(self.) and check if the attribute name matches with the variable name
                            if (isinstance(target, ast.Attribute) and target.attr == foreach_param):
                                # we extract the values and save it to labels
                                labels = [str(i) for i in ast.literal_eval(statement.value)]
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
