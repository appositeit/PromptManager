#!/usr/bin/env python3
"""
Fix template caching in the prompt manager.

This script updates the server.py file to disable Jinja2 template caching correctly.
"""

import os
import sys
from pathlib import Path

# Add the project to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')

server_file = os.path.join(src_path, 'server.py')

# Read the server file
with open(server_file, 'r') as f:
    content = f.read()

# Check if we've already applied the fix
if 'ForceReloadLoader' in content:
    print("Fix appears to already be applied.")
    sys.exit(0)

# Identify the template initialization code
TEMPLATE_SECTION_START = "# Set up static files and templates"
TEMPLATE_SECTION_END = "# Main route for the web interface"

# Find the start and end positions
start_pos = content.find(TEMPLATE_SECTION_START)
end_pos = content.find(TEMPLATE_SECTION_END)

if start_pos == -1 or end_pos == -1:
    print("Error: Could not find the template section in server.py")
    sys.exit(1)

# Extract the template section
template_section = content[start_pos:end_pos]

# Create the replacement code with a simplified solution
new_template_section = """# Set up static files and templates
current_dir = Path(__file__).parent
static_dir = current_dir / "static"
templates_dir = current_dir / "templates"

# Ensure directories exist
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# Mount static files
if not os.path.exists(static_dir):
    logger.warning(f"Static directory {static_dir} does not exist, creating it")
    os.makedirs(static_dir, exist_ok=True)

# Create the css, js, and img subdirectories if they don't exist
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "img"), exist_ok=True)

# Mount the static directory
logger.info(f"Mounting static files directory: {static_dir}")
# Mount with a name for URL routing
static_files = StaticFiles(directory=static_dir)
app.mount("/static", static_files, name="static")

# Create a custom loader that forces template reloading
class ForceReloadLoader(FileSystemLoader):
    \"\"\"Custom loader that always reloads templates from disk.\"\"\"
    
    def get_source(self, environment, template):
        \"\"\"Get the template source, always forcing a reload from disk.\"\"\"
        filename = self.find_template(template)
        source = self.read_template_file(filename)
        # Always return a new uptodate function that returns False
        # to force template reloading
        return source, filename, lambda: False

# Create Jinja2 environment with caching completely disabled
env = Environment(
    loader=ForceReloadLoader(templates_dir),
    cache_size=0,  # Disable caching completely
    auto_reload=True,  # Always reload templates
    bytecode_cache=None  # Ensure no bytecode caching
)

# Add static_url function to global environment - always use this instead of url_for in templates
env.globals["static_url"] = lambda path: f"/static/{path}"

# Also add url_for compatibility for older templates
def template_url_for(name, **path_params):
    \"\"\"Template helper that implements url_for with fallback for static files.\"\"\"
    if name == "static" and "filename" in path_params:
        return f"/static/{path_params['filename']}"
    raise ValueError(f"Route {name} not found or url_for is not supported. Use static_url instead.")

env.globals["url_for"] = template_url_for

# Set up Jinja2 templates with custom environment
templates = Jinja2Templates(env=env)

# Log template configuration
logger.info(f"Template directory: {templates_dir} (caching completely disabled, forced reload enabled)")

# Helper function to add cache control headers
def add_no_cache_headers(response):
    \"\"\"Add cache control headers to prevent caching.\"\"\"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Add compatibility for URL routing in templates
@app.get("/static/{path:path}", include_in_schema=False)
async def static_files_redirect(path: str):
    \"\"\"Special handler for static files to support url_for in templates.\"\"\"
    from fastapi.responses import RedirectResponse
    response = RedirectResponse(url=f"/static/{path}")
    return add_no_cache_headers(response)

"""

# Replace the template section in the content
new_content = content[:start_pos] + new_template_section + content[end_pos:]

# Remove any middleware that tries to clear the cache
middleware_section = "@app.middleware(\"http\")\nasync def clear_template_cache"
if middleware_section in new_content:
    start_middleware = new_content.find(middleware_section)
    if start_middleware != -1:
        # Find the end of the middleware function
        end_middleware = new_content.find("    return await call_next(request)", start_middleware)
        if end_middleware != -1:
            end_middleware = new_content.find("\n", end_middleware + 30)
            # Remove the middleware function
            new_content = new_content[:start_middleware] + new_content[end_middleware:]

# Update the template rendering functions to use no-cache headers
template_functions = [
    "def prompt_editor(request: Request, prompt_id: str):",
    "def manage_prompts(request: Request):",
    "def settings(request: Request):",
    "def websocket_test_page(request: Request):",
    "def search_replace_test_page(request: Request):"
]

for func in template_functions:
    func_pos = new_content.find(func)
    if func_pos != -1:
        templates_response = "return templates.TemplateResponse("
        templates_pos = new_content.find(templates_response, func_pos)
        if templates_pos != -1:
            response_end = new_content.find(")", templates_pos)
            if response_end != -1:
                # Replace the simple return with a cached response
                original = new_content[templates_pos:response_end+1]
                replacement = f"""response = {original}
    return add_no_cache_headers(response"""
                new_content = new_content[:templates_pos] + replacement + new_content[response_end+1:]

# Write the updated content back to the file
with open(server_file, 'w') as f:
    f.write(new_content)

print("Applied template caching fix to server.py")
