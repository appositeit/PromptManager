#!/usr/bin/env python3
"""
Starter script for the prompt manager.
"""

import subprocess
import sys
import os
from pathlib import Path

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Create a simplified version of the server.py file
simplified_server_path = os.path.join(script_dir, "bin", "simplified_server.py")

# Write the simplified server
with open(simplified_server_path, "w") as f:
    f.write("""#!/usr/bin/env python3
\"\"\"
Simplified prompt manager server.
\"\"\"

import os
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

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

# Set up Jinja2 templates with special handling
class CustomTemplates(Jinja2Templates):
    def __init__(self, directory):
        super().__init__(directory)
        
    def TemplateResponse(self, name, context, status_code=200, headers=None, media_type=None, background=None):
        # Add static_url function to context
        context["static_url"] = lambda path: f"/static/{path}"
        
        # Call parent method
        return super().TemplateResponse(
            name, context, status_code=status_code, 
            headers=headers, media_type=media_type, background=background
        )

templates = CustomTemplates(directory=templates_dir)

# Main route for the web interface - redirect to the prompt management page
@app.get("/")
async def index(request: Request):
    \"\"\"Redirect to the prompt management page.\"\"\"
    return RedirectResponse(url="/manage/prompts")

# Prompt management
@app.get("/manage/prompts")
async def manage_prompts(request: Request):
    \"\"\"Render the prompt management page.\"\"\"
    return templates.TemplateResponse("manage_prompts.html", {"request": request})

# Route for prompt editor
@app.get("/prompts/{prompt_id}")
async def prompt_editor(request: Request, prompt_id: str):
    \"\"\"Render the prompt editor page.\"\"\"
    return templates.TemplateResponse(
        "prompt_editor.html", 
        {"request": request, "prompt_id": prompt_id}
    )

# Trigger API routes
@app.get("/api/prompts/all")
async def get_prompts():
    \"\"\"Get all prompts.\"\"\"
    return []

@app.get("/api/prompts/directories/all")
async def get_directories():
    \"\"\"Get all directories.\"\"\"
    return []

# Search and replace test page
@app.get("/debug/search-replace")
async def search_replace_test_page(request: Request):
    \"\"\"Render the search and replace test page.\"\"\"
    return templates.TemplateResponse("search_replace_test.html", {"request": request})

# Run the server with uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8081)
""")

# Make the file executable
os.chmod(simplified_server_path, 0o755)

# Run the script
print("Starting simplified prompt manager server...")
try:
    subprocess.run([
        sys.executable,
        simplified_server_path
    ], check=True)
except KeyboardInterrupt:
    print("\nServer terminated.")
except Exception as e:
    print(f"Error running server: {e}")
