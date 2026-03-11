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
            bundle += f.read_text()

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
