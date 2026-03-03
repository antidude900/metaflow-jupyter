"""metaflow_jupyter.dag_widget — Unified DAG visualization for Metaflow.

Public API
----------
DagWidget(target)
    The only entry point for DAGs. Behehaves polymorphicly:
    - Pass FlowSpec class: returns a static graph widget.
    - Pass a Run: returns a widget with status colors (polls if active).
    - Pass a Runner: starts the run in background and shows live tracking.
    - await DagWidget(runner): runs, tracks, and returns the final Run object.
"""

from .widget import DagWidget

__all__ = ["DagWidget"]
