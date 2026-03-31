import pathlib

def bundle_js():
    """Concatenates JS files in a rigid order. No regex, no imports, Bare Metal."""
    ui = pathlib.Path(__file__).parent / "WidgetUI"

    files = [
        ui / "config.js",
        ui / "utils.js",
        ui / "components" / "header.js",
        ui / "components" / "edge.js",
        ui / "components" / "node.js",
        ui / "components" / "dropdown.js",
        ui / "index.js"
    ]

    bundle = ""
    for f in files:
        if f.exists():
            content = f.read_text().splitlines()
            for line in content:
                code = line.strip().split()
                if not code or code[0] == "import":
                    continue
                elif f != ui / "index.js" and code[0] == "export":
                    idx = 2 if (len(code) > 1 and code[1] == "default") else 1
                    if code[idx] in ["function","const","class"]:
                        to_replace = "export default " if idx == 2 else "export "
                        line = line.replace(to_replace, "", 1)
                    else: pass
                bundle+=line+"\n"
    return bundle

def bundle_css():
    """Concatenates CSS filess"""
    styles = pathlib.Path(__file__).parent / "WidgetUI" / "styles"
    
    files = [
        styles / "main.css",
        styles / "header.css",
        styles / "node.css",
        styles / "edge.css",
        styles / "dropdown.css"
    ]

    bundle = ""
    for f in files:
        if f.exists():
            bundle += f.read_text()

    return bundle
