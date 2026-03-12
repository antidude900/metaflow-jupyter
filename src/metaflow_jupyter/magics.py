import os
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic
from metaflow import Runner
from .registry import registry
import sys


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
        %%mf_step [.Step or Flow.Step] [tag] [--join]
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
        %%mf_decorator [.Step or Flow.Step or Flow or _] [tag]
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


def register_magics(ipython):
    ipython.register_magics(MetaflowMagics)
