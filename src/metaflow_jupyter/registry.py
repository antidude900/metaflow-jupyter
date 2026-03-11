import ast
import textwrap
from collections import defaultdict
import re

class FlowStructure:
    """
    Defines the structure of a flow
    """
    def __init__(self):
        self.import_code = {}
        self.global_code = {}
        self.flow_decorators = {}
        self.local_code = {}
        self.step_decorators = {}
        self.steps = {}

class FlowRegistry:
    """
    Stores the created Flows in the Registry 
    """
    def __init__(self):
        self.flows = defaultdict(FlowStructure)
    
    def set_import(self, flow_name, tag, code):
        # flow_registry -> flow_name -> tag -> code
        self.flows[flow_name].import_code[tag] = code

    def set_global(self, flow_name, tag, code):
        # flow_registry -> flow_name -> tag -> code
        self.flows[flow_name].global_code[tag] = code
    
    def set_flow_decorator(self, flow_name, decorators, tag):
        # flow_registry -> flow_name -> tag -> decorators
        self.flows[flow_name].flow_decorators[tag] = decorators

    def set_local(self, flow_name, tag, code):
        # flow_registry -> flow_name -> tag -> code
        self.flows[flow_name].local_code[tag] = code

    def set_step_decorator(self, flow_name, step_name, decorators, tag):
        # flow_registry -> flow_name -> step_name -> tag -> decorators
        if step_name not in self.flows[flow_name].step_decorators:
            self.flows[flow_name].step_decorators[step_name] = {}
        self.flows[flow_name].step_decorators[step_name][tag] = decorators

    def add_step(self, flow_name, step_name, code, is_join=False):
        # flow_registry -> flow_name -> step_name -> (code, is_join)
        self.flows[flow_name].steps[step_name] = (code, is_join)

    def clear(self, flow_name=None):
        """
        Clear a specific flow or all flows from the registry
        """
        if flow_name:
            if flow_name in self.flows:
                del self.flows[flow_name]
        else:
            self.flows.clear()

    def to_script(self, flow_name):
        """
        Assembles the code content of all cell magics to a script file
        """
        if flow_name not in self.flows:
            raise ValueError(f"No code registered for flow: {flow_name}")
            
        flow = self.flows[flow_name]
        
        # Metaflow Base Imports
        mf_imports = {"FlowSpec", "step"}
        
        # Put Import of Decorators to Metaflow Base Imports

        # tag_grouped_decorators = List(List(str))
        tag_grouped_decorators = list(flow.flow_decorators.values()) 
        for step_tags in flow.step_decorators.values():
            tag_grouped_decorators.extend(step_tags.values())

        for decorators in tag_grouped_decorators:
            for decorator in decorators:
                #checking if each decorator starts with @ and if yes, we add it to mf_imports
                match = re.match(r"@([\w]+)", decorator.strip())
                if match:
                    mf_imports.add(match.group(1))

        # We start building the script starting with the metaflow base import
        script = [f"from metaflow import {', '.join(sorted(mf_imports))}\n"]

        # Adding other import statements    
        for code in flow.import_code.values():
            script.append(code)
        
        # Adding global code (code outside class)
        for code in flow.global_code.values():
            script.append(code)

        # Adding flow decorators
        for tag_grouped_decorators in flow.flow_decorators.values():
            for decorator in tag_grouped_decorators:
                script.append(decorator)
            
        script.append(f"class {flow_name}(FlowSpec):\n")
            
        # Adding local code (code inside class and before steps)
        INDENT = " " * 4
        for code in flow.local_code.values():
            if code.strip():
                script.append(textwrap.indent(code.strip(), INDENT) + "\n")
                
        # Adding steps
        for step_name, (body, is_join) in flow.steps.items():

            # Adding step decorator
            if step_name in flow.step_decorators:
                for tag_grouped_decorators in flow.step_decorators[step_name].values():
                    for decorator in tag_grouped_decorators:
                        script.append(f"{INDENT}{decorator}")
            
            # Adding step
            script.append(f"{INDENT}@step")
            script.append(f"{INDENT}def {step_name}(self{', inputs' if is_join else ''}):")
            script.append(textwrap.indent(body.strip(), INDENT * 2) + "\n")

        # Adding entry point
        script.extend(["if __name__ == '__main__':", f"{INDENT}{flow_name}()"])

        # returing the script as a single string adding new lines in between
        return "\n".join(script)

# Instance of the Registry for the magics to access and add code
registry = FlowRegistry()
