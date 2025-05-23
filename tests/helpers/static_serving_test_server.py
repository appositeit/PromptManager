"""
Standalone FastAPI server for testing static file serving and
basic template engine setup.

This server mounts the static files directory (e.g., 'src/static')
and initializes Jinja2 templates. It provides a simple root
endpoint to help verify that static assets can be correctly
served and that the templating engine is configured.

It is intended to be run manually or as a target for other test
scripts that need to check basic server setup related to static
assets and HTML rendering.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Add the project root to the Python path to resolve src.* imports if any were added later
# Assumes this script is in tests/helpers/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Create app
app = FastAPI()

# Set up static files and templates relative to project root/src
static_dir = project_root / "src" / "static"
templates_dir = project_root / "src" / "templates"

print(f"Static dir: {static_dir}")
print(f"Templates dir: {templates_dir}")

# Ensure directories exist (optional, as StaticFiles/Jinja2Templates might handle it)
# However, good for clarity and explicit check if server runnable
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# Mount static files
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print(f"Warning: Static directory not found at {static_dir}. Static files will not be served.")

# Set up Jinja2 templates
if templates_dir.is_dir():
    templates = Jinja2Templates(directory=templates_dir)
else:
    print(f"Warning: Templates directory not found at {templates_dir}. Template responses will fail.")
    # Dummy templates object to prevent crash on server start if templates dir is missing
    class DummyTemplates:
        def TemplateResponse(self, name, context):
            raise RuntimeError(f"Templates directory {templates_dir} not found. Cannot render {name}.")
    templates = DummyTemplates()


# Add a simple test route
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Simple HTML response, does not require templates object to be valid for this route
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Server - Static/Template Check</title>
    </head>
    <body>
        <h1>Test Server - Static/Template Check</h1>
        <p>Test server is running!</p>
        <p>If static files are mounted correctly, this link should work: 
           <a href="/static/js/utils.js">/static/js/utils.js</a> (assuming utils.js exists)
        </p>
        <p>Attempting to render a test template (if templates are set up):</p>
        <p><a href="/test-template">Test Template Page</a></p>
    </body>
    </html>
    """

@app.get("/test-template", response_class=HTMLResponse)
async def test_template_page(request: Request):
    """Attempts to render a dummy test template."""
    try:
        # Create a dummy test_page.html in src/templates for this to work
        # e.g., with content: <h1>Template Page Test</h1><p>Request: {{ request.path }}</p>
        return templates.TemplateResponse("test_page.html", {"request": request, "message": "Test template rendered!"})
    except Exception as e:
        return HTMLResponse(f"<html><body><h1>Template Error</h1><p>{e}</p></body></html>", status_code=500)


# Run the server with uvicorn
if __name__ == "__main__":
    import uvicorn
    print("Starting static serving test server on http://127.0.0.1:8081")
    uvicorn.run(app, host="127.0.0.1", port=8081) 