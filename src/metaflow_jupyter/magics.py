import os
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from metaflow import Runner
from .registry import registry
import sys


@magics_class
class MetaflowMagics(Magics):
    @cell_magic
    def mf_step(self, line, cell):
        """
        %%mf_step <FlowName>.<StepName> [join]
        """
        args = line.strip().split()
        if not args or "." not in args[0]:
            raise ValueError("Explicit naming required: %%mf_step <FlowName>.<StepName> [join]")
        
        #the first argument has the name of the step of the specified Flow(FlowName.StepName)
        #and there maybe a second argument which has a flag to make the step function's parameter include 'inputs' 
        target = args[0]
        is_join = "join" in [arg.lower() for arg in args[1:]]
        
        flow_name, step_name = target.split(".", 1)
        registry.add_step(flow_name.strip(), step_name.strip(), cell, is_join=is_join)

    @cell_magic
    def mf_global(self, line, cell):
        """
        %%mf_global <FlowName> [tag]
        """
        args = line.strip().split()
        if not args:
            raise ValueError("Flow name required: %%mf_global <FlowName> [tag]")
            
        flow_name = args[0]
        tag = args[1] if len(args) > 1 else "default"
            
        registry.set_global(flow_name, tag, cell)

    @cell_magic
    def mf_import(self, line, cell):
        """
        %%mf_import <FlowName> [tag]
        """
        args = line.strip().split()
        if not args:
            raise ValueError("Flow name required: %%mf_import <FlowName> [tag]")
        
        flow_name = args[0]
        tag = args[1] if len(args) > 1 else "default"
            
        registry.set_import(flow_name, tag, cell)

    @cell_magic
    def mf_decorator(self, line, cell):
        """
        %%mf_decorator <FlowName> or <FlowName>.<StepName> [tag]
        """
        args = line.strip().split()
        if not args:
            raise ValueError("Target required: %%mf_decorator <FlowName>[.<StepName>] [tag]")
            
        target = args[0]
        tag = args[1] if len(args) > 1 else "default"

        # Extract all the decorators and check if all are valid or not(starts with @)
        decorators = [l.strip() for l in cell.split("\n") if l.strip()]
        for d in decorators:
            if not d.startswith("@"):
                raise ValueError(f"Invalid decorator syntax: '{d}'. Every line must start with '@'.")
        
        # if the target has a dot, it means it's a step decorator else it's a flow decorator
        if "." in target:
            flow_name, step_name = target.split(".", 1)
            registry.set_step_decorator(flow_name.strip(), step_name.strip(), decorators, tag)
        else:
            registry.set_flow_decorator(target, decorators, tag)

    @cell_magic
    def mf_local(self, line, cell):
        """
        %%mf_local <FlowName> [tag]
        """
        args = line.strip().split()
        if not args:
            raise ValueError("Flow name required: %%mf_local <FlowName> [tag]")
            
        flow_name = args[0]
        tag = args[1] if len(args) > 1 else "default"
            
        registry.set_local(flow_name, tag, cell)

    @line_magic
    def mf_clear(self, line):
        """%mf_clear <FlowName> or %mf_clear -all"""
        arg = line.strip()
        if not arg:
            print("Flow name or flag '-all' required: %mf_clear <FlowName> or %mf_clear -all")
            return
            
        # If the arg is flag '-all', we clear registry of all flows else we only clear registry of the flow name passed
        if "-all" in arg:
            registry.clear()
            print("Metaflow Registry: Cleared all flows.")
        else:
            flow_name = arg
            registry.clear(flow_name)
            print(f"Metaflow Registry: Cleared flow: {flow_name}")

    @line_magic
    def mf_run(self, line):
        """
        %mf_run <FlowName>
        """
        flow_name = line.strip()
        if not flow_name:
            raise ValueError("Flow name required: %mf_run <FlowName>")
        
        # conver the content of cell magics to a python script and run the script using Metaflow Runner
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
            # remove the python script after the script run completes
            if os.path.exists(filename):
                os.remove(filename)


def register_magics(ipython):
    ipython.register_magics(MetaflowMagics)
