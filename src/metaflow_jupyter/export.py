import argparse, ast, sys, nbformat, warnings
from pathlib import Path
from .magics import MetaflowMagics
from .registry import registry

# Ignore id warnings from older notebook formats
warnings.filterwarnings("ignore", module="nbformat")


def _populate_registry(nb_path):
    """
    Populate the registry with the cell magics from the notebook
    """
    path = Path(nb_path)
    if not path.exists() or path.suffix != ".ipynb":
        raise ValueError(f"Invalid notebook: {nb_path}")

    with open(path, "r", encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    mf = MetaflowMagics(None)
    registry.clear()

    # If the cell is a code cell, we check if it contains cell magic
    for cell in (c for c in nb.cells if c.cell_type == "code"):
        content = cell.source

        # If if the content of the code cell starts with %%mf_, its a cell magic
        if content.startswith("%%mf_"):
            # Split the content into list of lines
            lines = content.splitlines()
        
            # lines[0] gives the cell magic header and we slice of the %%
            # and then split the header into two parts: cell magic name and arguments
            parts = lines[0][2:].split(maxsplit=1)
            name, args = parts[0], parts[1] if len(parts) > 1 else ""

            # if the cell magic name is in the MetaflowMagics class, we call the method
            if hasattr(mf, name):
                body = "\n".join(lines[1:]) + "\n"
                getattr(mf, name)(args, body)



def _write_script(flow, out_dir):
    """
    Convert the registry to a python script and write it to a file
    """
    try:
        code = registry.to_script(flow)
        ast.parse(code)
        dest = Path(out_dir)
        dest.mkdir(parents=True, exist_ok=True)
        with open(dest / f"{flow}.py", "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Exported {flow} to {dest}/{flow}.py")
    except Exception as e:
        print(f"Error exporting {flow}: {e}")



def main():
    """
    CLI entrypoint for mf-export
    """
    parser = argparse.ArgumentParser(description="Convert Metaflow magics in a notebook to .py files.")
    parser.add_argument("notebook")
    parser.add_argument("--flows", nargs="*")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--output", default=".")
    args = parser.parse_args()

    _populate_registry(args.notebook)

    # From the registry we populated, we extract the list of flows recorded
    available = list(registry.flows.keys())
    if not available:
        print("No flows found.")
        return 

    # We check if the user wants to export all flows or specific flows
    if args.all:
        flows_to_export = available
    elif args.flows:
        flows_to_export = args.flows
    else:
        # If now flow is given, we consider it to be our default flow
        flows_to_export = ["MyFlow"]

    # For each flow the user wants to export, we write its script to a file
    for flow in flows_to_export:
        if flow in available:
            _write_script(flow, args.output)
        else:
            print(f"Warning: Flow '{flow}' not found.")

if __name__ == "__main__":
    main()
