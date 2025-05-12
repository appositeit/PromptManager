#!/usr/bin/env python3
"""
Test server to check static files mounting.
"""

import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Create app
app = FastAPI()

# Set up static files and templates
current_dir = Path(__file__).parent.parent
static_dir = current_dir / "src" / "static"
templates_dir = current_dir / "src" / "templates"

print(f"Static dir: {static_dir}")
print(f"Templates dir: {templates_dir}")

# Ensure directories exist
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory=templates_dir)

# Add a simple test route
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Server</title>
    </head>
    <body>
        <h1>Test Server</h1>
        <p>Test server is running!</p>
        <p>Static files should be available at <a href="/static/js/utils.js">/static/js/utils.js</a></p>
    </body>
    </html>
    """

# Run the server with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8081)
