import asyncio
from pathlib import Path
from metaflow import FlowSpec, NBRunner
from .bundle_ui import bundle_js, bundle_css
from .utils import extract_graph, update_status
import anywidget
import traitlets

class DagWidget(anywidget.AnyWidget):
    """
    Jupyter widget for interactive DAG visualization of Metaflow Flows for:
    1. The static structure of a Metaflow Flow
    2. Live execution progress

    """
    
    # Load the Javascript Budle and CSS file to the widget
    _esm = bundle_js()
    _css = bundle_css()

    # Initialize the widget states using Traitlets 
    # Automatically syncs Widget Class state to the UI state (Python to JS bi-directional sync))

    nodes = traitlets.List([]).tag(sync=True)
    edges = traitlets.List([]).tag(sync=True)
    layers = traitlets.List([]).tag(sync=True)
    flow_name = traitlets.Unicode("").tag(sync=True)
    subtitle = traitlets.Unicode("").tag(sync=True)
    executionStatus = traitlets.Unicode("").tag(sync=True)
    activeDropMenus = traitlets.List([]).tag(sync=True)

    def __init__(self, flow_cls, run=False, showLogs=True, **kwargs):
        """
        Initialize the DagWidget.
        For Static View: run = False which uses the graph structure of the Flow
        For Live View: run = True which runs the Flow execution, tracks the changes and updates the graph structure
        
        """

        super().__init__()

        # Ensure flow_cls is a subclass of FlowSpec   
        if not (isinstance(flow_cls, type) and issubclass(flow_cls, FlowSpec)):
            raise ValueError("DagWidget requires a Metaflow Flow class.")

        # Populate widget state with flow metadata and graph structure
       
        self.flow_name = flow_cls.__name__
        self.subtitle = "(Execution)" if run else "(Structure)"
        if run: self.executionStatus = "Starting the Run"

        # Extract graph structure of the flow class for flow visualization
        self.nodes, self.edges, self.layers = extract_graph(flow_cls)

        # Initialize node status to pending if Live View (so that the node types don't get rendered intitally in Live View)
        if run:
            self.nodes = [{**node, "status": "pending"} for node in self.nodes]
        
        # If Live View, we track the running instance (check every 0.5 second) which is used to update the node status
        # Make the instance run in background without blocking the Jupyter cell
        asyncio.create_task(self._run_and_track(NBRunner(flow_cls, **kwargs), flow_cls, showLogs)) if run else None


    async def _run_and_track(self, runner, flow_cls, showLogs):
        """
        Run the Flow execution while updating the widget UI in real-time (coordinates both processes)

        """
        try:
            # Start the Flow execution asynchronously 
            executing = await runner.async_run()
            
            self.executionStatus = "Running"
            self.nodes = [{**node, "status": "running"} if node["id"] == "start" else node for node in self.nodes]

            runningInstance = executing.run

            # Run another background process to stream logs (standard output) from Metaflow to the notebook
            async def _stream():
            
                async for _, line in executing.stream_log("stdout"):
                    print(line, end="\n", flush=True)
                
            if showLogs: asyncio.create_task(_stream())

            # Seed foreach_labels once from statically extracted labels (from extract_graph AST)
            # This dict persists across all polls — dynamic nodes are resolved lazily and cached
            foreach_labels = {
                node["id"]: [t["label"] for t in node["foreach"]["tasks"]]
                for node in self.nodes
                if node.get("foreach") and node["foreach"].get("tasks")
            }

            # Check for changes every 0.5 seconds while the Flow is running
            while executing.status == "running":
                # Update the node status in the widget
                self.nodes = update_status(self.nodes, runningInstance, flow_cls, foreach_labels)
                await asyncio.sleep(0.5)

            # Final update at the end to ensure we didn't miss any update
            self.nodes = update_status(self.nodes, runningInstance, flow_cls, foreach_labels)

        except Exception as e:
            # Catch early errors (like validation failures) and print them to the cell
            print(f"{e}", flush=True)

        # After the Flow execution is complete, clean up the temp file created By NBRunner
        finally:
            self.executionStatus = "Ended"
            runner.cleanup()
    

