import os, sys, json
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from IPython.display import display, HTML
from metaflow import Runner
from .registry import registry
from metaflow import Flow


@magics_class
class MetaflowMagics(Magics):
    def _extract_args(self, line, is_step=False):
        """
        Extract target (flow name and step(if is_step)) and tag from magic line
        """
        args = line.strip().split()
        if not args:
            return "MyFlow", "default"
        
        target = args[0]
        tag = args[1] if len(args) > 1 else "default"

        if target == "_":
            return "MyFlow", tag
            
        if is_step and "." not in target:
            return f"MyFlow.{target}", tag
            
        return target, tag

    @cell_magic
    def mf_step(self, line, cell):
        """
        %%mf_step [Step or Flow.Step] [tag] [--join]
        """
        target, tag = self._extract_args(line, is_step=True)
        is_join = "--join" in line.lower()
        
        flow_name, step_name = target.split(".", 1)
        registry.add_step(flow_name.strip(), step_name.strip(), tag, cell, is_join=is_join)

    @cell_magic
    def mf_global(self, line, cell):
        """
        %%mf_global [Flow or _] [tag]
        """
        flow, tag = self._extract_args(line)
        registry.set_global(flow, tag, cell)

    @cell_magic
    def mf_import(self, line, cell):
        """
        %%mf_import [Flow or _] [tag]
        """
        flow, tag = self._extract_args(line)
        registry.set_import(flow, tag, cell)

    @cell_magic
    def mf_decorator(self, line, cell):
        """
        %%mf_decorator [Step or Flow.Step or Flow or _] [tag]
        """
        target, tag = self._extract_args(line)
        decorators = [l.strip() for l in cell.split("\n") if l.strip()]
        for d in decorators:
            if not d.startswith("@"):
                raise ValueError(f"Invalid decorator: '{d}'. Must start with '@'.")
        
        if "." in target:
            flow_name, step_name = target.split(".", 1)
            registry.set_step_decorator(flow_name.strip(), step_name.strip(), decorators, tag)
        else:
            registry.set_flow_decorator(target, decorators, tag)

    @cell_magic
    def mf_local(self, line, cell):
        """
        %%mf_local [Flow or _] [tag]
        """
        flow, tag = self._extract_args(line)
        registry.set_local(flow, tag, cell)

    @line_magic
    def mf_clear(self, line):
        """
        %mf_clear [FlowName] or %mf_clear --all
        """
        arg = line.strip()
        if not arg:
            flow_name = "MyFlow"
            registry.clear(flow_name)
            print("Metaflow Registry: Cleared MyFlow.")
            return
            
        if "--all" in arg:
            registry.clear()
            print("Metaflow Registry: Cleared all flows.")
        else:
            flow_name = arg
            registry.clear(flow_name)
            print(f"Metaflow Registry: Cleared flow: {flow_name}")

    @line_magic
    def mf_run(self, line):
        """
        %mf_run [FlowName] [--export]
        """
        args = line.strip().split()
        
        # Resolve flow name (defaulting to MyFlow if first arg is empty or a flag)
        if not args or args[0].startswith("--"):
            flow_name = "MyFlow"
        else:
            flow_name = args[0]

        export = "--export" in [a.lower() for a in args]
        
        # convert the content of cell magics to a python script and run the script using Metaflow Runner
        source = registry.to_script(flow_name)

        filename = f"{flow_name}.py"
        with open(filename, "w") as f:
            f.write(source)

        try:
            result = Runner(filename, show_output=True).run()
            return result.run
        except Exception as e:
            # to remove the traceback of IPython
            ErrorName = type(e).__name__
            raise Exception(f"\n{ErrorName}: {e}") from None
        finally:
            # remove the python script after the script run completes if export flag is not present
            if not export and os.path.exists(filename):
                os.remove(filename)

    @line_magic
    def mf_show(self, line):
        """
        %mf_show [Pathspec] [ArtifactName]
        """

        args = line.strip().split()

        # Combine args into a single string for PathSpec parsing
        combined_args = " ".join(args)

        # If '.' is present in the combined args, it is either: step.artifact or flow step.artifact
        # In such case we split step from artifact
        if "." in combined_args:
            path, artifact = combined_args.rsplit(".", 1)

        # And if there is no '.' and was made from exactly two args, it is: flow/run/step artifact
        elif len(args) == 2:
            path, artifact = args
        else:
            return print("Usage: 'step.artifact' or 'flow step.artifact' or 'flow/run/step artifact or flow'")

        # For the splitted step, we first combine it with the PathSpec
        # Then we split the path into segments to check for flow, run_id and step
        path_segments = [segment for segment in path.replace(" ", "/").split("/") if segment]
        
        # Set default values Flow and run_id whereas step value will always be given 
        flow, run_id, step = "MyFlow", "latest", None

        if len(path_segments) == 3:
            # For: flow/run/step from flow/run/step artifact
            flow, run_id, step = path_segments
        elif len(path_segments) == 2:
            # For flow/step from flow step.artifact
            flow, step = path_segments
        elif len(path_segments) == 1:
            # For step from step.artifact
            step = path_segments[0]

        # Fetch and Render Artifact 
        try:
            
            flow_obj = Flow(flow)
            run_obj = flow_obj.latest_run if run_id == "latest" else flow_obj[run_id]
            step_obj = run_obj[step]
                
            tasks = list(step_obj.tasks())
            count = 0

            # A step can have multiple tasks (foreach). So rendering artifact of each
            for task in tasks:
                try:
                    # While unpickling a value, we need the corresponding library to reconstruct the object
                    # For eg: Pandas->Dataframe, Matplotlib->Figure, Numpy->ndarray
                    # So if any of the library corresponding to the artifact's type is missing, it will raise an error
                    val = getattr(task.data, artifact)
                    count += 1
                except AttributeError:
                    # If we dont find any artifact in the current task, we skip it
                    continue
            
                # Trace all the foreach parameters we have passed through to reach the current task 
                foreach_stack = task.metadata_dict.get('foreach-stack', [])
                foreach_label = ""
                if foreach_stack:
                    # Join all the foreach parameters into a comma seperate string 'param1 = value1, param2 = value2'
                    foreach_label = ', '.join(foreach_stack)

                # Extract flow_id and step_id from the pathspec (Muting run_id and task_id)
                flow_id, _ , step_id, _ = task.pathspec.split('/')

                # Display header for the artifact
                header = (
                    f"&nbsp; <b>Flow:</b> {flow_id} &nbsp;"
                    f"|&nbsp; <b>Step:</b> {step_id} &nbsp;"
                    f"|&nbsp; <b>Artifact:</b> {artifact} &nbsp;"
                )
                if foreach_label:
                    header += f"|&nbsp; <b>Foreach Stack:</b> ( {foreach_label} ) &nbsp;"
                display(HTML(f"<code>{header}</code>"))

                # Display the artifact considering it's type
                if "numpy" in str(type(val)):
                    print(f"numpy.ndarray: shape={val.shape}, dtype={val.dtype}")
                    display(val)
                elif isinstance(val, (dict, list)):
                    print(json.dumps(val, indent=2))
                else:
                    try:
                        display(val)
                    except Exception as e:
                        print(f"Error: {e}")

                # Close matplotlib figures after display to prevent double rendering
                mpl = sys.modules.get("matplotlib")
                if mpl and isinstance(val, mpl.figure.Figure):
                    try:
                        mpl.pyplot.close(val)
                    except Exception as e:
                        # The only error that can come from mpl.pyplot.close(val) is due to close() as mpl is not None 
                        # This means the figure was already closed in the flow. So we can't again call close on it
                        # This also signals that the figure we tried rendering before wasn't successfull (as it was already closed before rendering)
                        print("Note: This figure was closed with .close() before being saved.\n"
                                "      Remove .close() from your flow to display it here.\n"
                                "      (Memory is freed automatically when the step completes, so .close() isn't needed)")

            # If no artifact was found in any of the tasks, display that no such artifact was found in the given step
            if count == 0:
                print(f"Artifact '{artifact}' not found in step '{step_id}'")
        except Exception as e:
            # Printing the error message manually to avoid complex traceback and thus make the error message clear
            # Also as this line magic neither return nor affect anything, we can resume other cell execution (so we don't raise any error)
            print(f"Error: {e}")

def register_magics(ipython):
    ipython.register_magics(MetaflowMagics)
