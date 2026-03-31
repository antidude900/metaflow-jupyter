import asyncio, os
from pathlib import Path
from metaflow import FlowSpec, NBRunner
from metaflow.exception import MetaflowException
from .bundle_ui import bundle_js, bundle_css
from .utils import extract_graph, update_status
import anywidget
from traitlets import List,Unicode

class DagWidget(anywidget.AnyWidget):
    """
    Jupyter widget for interactive DAG visualization of Metaflow Flows for:
    1. The static structure of a Metaflow Flow
    2. Live execution progress

    """

    _active_task = None
    
    # Load the Javascript Budle and CSS file to the widget
    _esm = bundle_js()
    _css = bundle_css()

    # Initialize the widget states using Traitlets 
    # Automatically syncs Widget Class state to the UI state (Python to JS bi-directional sync))
    nodes = List([]).tag(sync=True)
    edges = List([]).tag(sync=True)
    flow_name = Unicode("").tag(sync=True)
    subtitle = Unicode("").tag(sync=True)
    executionStatus = Unicode("").tag(sync=True)

    def __init__(self, flow_cls, runner=None, run=False, showLogs=True, filename=None,**kwargs):
        """
        Initialize the DagWidget.
        For Static View: run = False 
        For Live View: run = True or pass a pre-configured runner.
        
        """
        # Cancel previous run if still active
        if DagWidget._active_task and not DagWidget._active_task.done():
            DagWidget._active_task.cancel()

        super().__init__()
        # Ensure flow_cls is a subclass of FlowSpec   
        if not (isinstance(flow_cls, type) and issubclass(flow_cls, FlowSpec)):
            raise ValueError("DagWidget requires a Metaflow Flow class.")

        # If a runner is passed, we are definitely in Live View
        if runner:
            run = True

        self.flow_name = flow_cls.__name__
        self.subtitle = "(Live View)" if run else "(Static View)"
        if run: self.executionStatus = "Starting..."

        # Extract graph structure of the flow class for flow visualization
        try:
            self.nodes, self.edges = extract_graph(flow_cls)
        except MetaflowException as e:
            # Display validation errors cleanly without long traceback
            raise ValueError(f"Flow validation failed: {str(e)}") from None

        # Initialize node status to pending if Live View
        if run:
            self.nodes = [{**node, "status": "pending"} for node in self.nodes]
        
        # If Live View, we start the tracking task
        if run:
            # If no runner provided, fall back to default NBRunner (standard Jupyter behavior)
            if not runner:
                runner = NBRunner(flow_cls, **kwargs)
            
            # Run the flow and track the execution asynchronously
            # And record that as a active task to later cancel it manually if needed
            DagWidget._active_task = asyncio.create_task(self._run_and_track(runner, flow_cls, showLogs))


    async def _run_and_track(self, runner, flow_cls, showLogs):
        """
        Run the Flow execution while updating the widget UI in real-time (coordinates both processes)

        """
        try:
            # Start the Flow execution asynchronously
            executing = await runner.async_run()

            self.executionStatus = "Running..."
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
        except asyncio.CancelledError:
            pass
        except Exception as e:
            # Catch early errors (that occurs before the run) and print them to the cell
            print(str(e),flush=True)
        
        # After the Flow execution is complete, clean up
        finally:
            self.executionStatus = "Ended"
            runner.cleanup()

            # For the ClientAPI Runner
            if runner:
                path = getattr(runner, 'flow_file', None)
                if path and os.path.exists(path):
                    os.remove(path)
    

