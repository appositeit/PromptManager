#!/usr/bin/env python3
"""
Apply a simple fix for the template caching issue in prompt manager.
"""

import sys
import os
import shutil

# Define the file path
server_file = '/home/jem/development/prompt_manager/src/server.py'

# Create a backup of the original file
backup_file = server_file + '.bak'
shutil.copy2(server_file, backup_file)
print(f"Created backup at: {backup_file}")

# Read the original content
with open(server_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Define the section to find and replace
template_setup = """# Set up Jinja2 templates with custom environment
templates = Jinja2Templates(env=env)

# Log template configuration
logger.info(f"Template directory: {templates_dir} (caching completely disabled, forced reload enabled)")"""

# Define the new section
new_template_setup = """# Set up Jinja2 templates with custom environment
templates =