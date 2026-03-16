import os, io, ast, re, sys
from metaflow.runner.nbrun import NBRunner
from metaflow.runner.utils import get_current_cell
from IPython import get_ipython

class CleanNBRunner:
    """
    A wrapper for NBRunner with clean error messages.
    """
    
    # ANSI ESCAPE codes to format the output text
    ESC = {"RED": "\033[91m", "YEL": "\033[93m", "BOLD": "\033[1m", "END": "\033[0m"}

    # Output Text for each corresponding failure case
    MSG = {
        "NO_FLOW": ("No FlowSpec found", "Your class must directly inherit from FlowSpec:\n  class MyFlow(FlowSpec)"),
        "REF": ("Reference Error", "The name '{}' is not defined. Move imports/helpers ABOVE the flow class."),
        "FAIL": ("Run Failed", "{}"),
        "TRUNC": ("Silent Drop Detected", "Code BELOW the Flow class is ignored by NBRunner:\n- {}\nMove these definitions ABOVE the flow class.")
    }

    def __init__(self, flow, **kwargs):
        self.flow = flow
        self.kwargs = kwargs
        self.silently_dropped = []


    def run(self, **run_kwargs):
        """
        Run the NBRunner instance with error handlers
        """
        self.silently_dropped = []
        self._check_silent_drop()
        
        # Stores the output for future error extraction
        captured = io.StringIO()

        # Making a reference of the old sys.stdout.write which only gives the data to the console
        original_write = sys.stdout.write

        # We rewrite the function to give the data to the console and our stored output
        # Everytime time NBRunner calls sys.stdout.write, it will use this new function
        sys.stdout.write = lambda data: (original_write(data), captured.write(data))
        
        # try/except wraps the runner to catch the error and show it in a cleaner way
        try:
            # Initialized the NBRunner directly when run instead of doing in __init__
            # This is to clean the error in the initialization stage too
            run_obj = NBRunner(self.flow, **self.kwargs).nbrun(**run_kwargs)
            if run_obj and not run_obj.successful:
                self._extract_error_from_output(captured.getvalue())
            return run_obj
        except Exception as e:
            self._handle_exception(e)
        finally:
            # Recover the original function after the run ends
            sys.stdout.write = original_write 


    def _handle_exception(self, e):
        """
        Check the error occured and print a cleaner error message
        """
        error_string = str(e)
        custom_base_error = "The cell doesn't contain any class that inherits from 'FlowSpec'"
        validity_error = "Validity checker found an issue"

        if (isinstance(e, ModuleNotFoundError) and custom_base_error in error_string):
            self._print_error("NO_FLOW")

        elif validity_error in error_string:
            # validity error is clean itself. So no custom error message required
            return

        elif isinstance(e, NameError):
            # A NameError message is like this: name 'x' is not defined
            # so we get the name 'x' by splitting the error string
            name = error_string.split("'")[1] if "'" in error_string else "unknown"
            self._print_error("REF", name)
        else:
            # If no such error found, print the error as it is
            # This still cleans the error as it removes the long trackback
            self._print_error("FAIL", e)


    def _extract_error_from_output(self, output):
        """
        Extracts error from the output log of NBRunner if it fails
        """
        # Remove the timestamp prefix from each line
        clean_output = [re.sub(r'^.*?\] ', '', l) for l in output.splitlines()]
        try:
            # Find the last traceback line
            idx = max(i for i, l in enumerate(clean_output) if l.strip().startswith("File "))

            # Get the error message lines (drop Metaflow's last 7 trailing status lines)
            error_lines = [l for l in clean_output[idx+1:-7] if l.strip()]

            if error_lines:
                # the last line is the actual error message
                last_line = error_lines[-1] 

                if "NameError:" in last_line:
                    # If NameError, we use the same error hanlding like in _handle_exception
                    name = last_line.split("'")[1] if "'" in last_line else "unknown"
                    return self._print_error("REF", name)
                
                # If any other error, print it as it is but without the long traceback
                return self._print_error("FAIL", "\n".join(error_lines))
        except: pass
        self._print_error("FAIL", "See logs above for details.")



    def _print_error(self, key, *args):
        """
        Prints the error message using the message template and the text format specified
        """
        error_title, error_message = self.MSG[key]
        error_message = error_message.format(*args)
        sys.stdout.flush()
        
        print(f"\n{self.ESC['RED']}{self.ESC['BOLD']}{error_title}{self.ESC['END']}")
        print(error_message)
        
        # If we found any silent drop, we include that too in our error message
        if self.silently_dropped:
            t2, m2 = self.MSG["TRUNC"]
            print(f"\n{self.ESC['YEL']}{self.ESC['BOLD']}{t2}{self.ESC['END']}")
            print(m2.format('\n- '.join(self.silently_dropped)))

        # Mark the end of the output message
        print("\n")
        sys.stdout.flush()



    def _check_silent_drop(self):
        """
        Check whether any code is defined below the flow class
        """
        # Get the current cell content
        ipy = get_ipython()
        content = get_current_cell(ipy) if ipy else None
        if not content: 
            return

        try:
            tree = ast.parse(content)
            
            # Find the end line of the class definition
            end_line = next((n.end_lineno for n in tree.body if isinstance(n, ast.ClassDef) and n.name == self.flow.__name__), 0)
            if not end_line: 
                return

            # For any lines which are before end_line, we dont have to check as only code after the class definition is sliently dropped
            # We also skip the lines which contain "ClearNBRunner","NBRunner","print()" as they are not part of the flow definition         
            for n in tree.body:
                if getattr(n, 'lineno', 0) <= end_line or any(x in ast.dump(n) for x in ["ClearNBRunner","NBRunner","print("]): 
                    continue

                # Function Definition, Class Definition, Variable Assignment, Import Statement
                # which are below the class definition are silently dropped
                # so we add them to the silently_dropped list
                if isinstance(n, ast.FunctionDef): self.silently_dropped.append(f"Function '{n.name}'")
                elif isinstance(n, ast.ClassDef): self.silently_dropped.append(f"Class '{n.name}'")
                elif isinstance(n, ast.Assign):
                    for t in n.targets:
                        if isinstance(t, ast.Name): self.silently_dropped.append(f"Variable '{t.id}'")
                elif isinstance(n, (ast.Import, ast.ImportFrom)):
                    for a in n.names: self.silently_dropped.append(f"Import '{a.name}'")

            # Remove Duplicates (Used dict.fromkeys to preserve order)
            self.silently_dropped = list(dict.fromkeys(self.silently_dropped))
        except: 
            pass
