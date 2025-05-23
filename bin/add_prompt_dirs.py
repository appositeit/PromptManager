#!/usr/bin/env python3
"""
Command-line tool for adding prompt directories to Prompt Manager.

This tool allows you to add one or more directories to the Prompt Manager
configuration by directly modifying the JSON configuration file.

Usage:
    add_prompt_dirs.py /path/to/dir1 [/path/to/dir2 ...]
    add_prompt_dirs.py --help

Examples:
    # Add a single directory
    add_prompt_dirs.py /home/jem/development/prompt_manager/prompts

    # Add multiple directories
    add_prompt_dirs.py /home/jem/claude_prompts /home/jem/ai_templates

    # The display name is auto-generated from the path:
    # /home/jem/development/prompt_manager/prompts -> "Prompt Manager"
    # /home/jem/claude_prompts -> "Claude Prompts" 
    # /home/jem/ai_templates -> "AI Templates"
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import List, Dict, Any


def get_config_file_path() -> str:
    """Get the path to the Prompt Manager configuration file."""
    return os.path.join(os.path.expanduser("~"), ".prompt_manager", "prompt_directories.json")


def generate_display_name(directory_path: str) -> str:
    """
    Generate a display name from a directory path.
    
    Examples:
        /home/jem/development/prompt_manager/prompts -> "Prompt Manager"
        /home/jem/claude_prompts -> "Claude Prompts"
        /home/jem/ai_templates -> "AI Templates"
        /some/path/openai_stuff -> "Openai Stuff"
    
    Args:
        directory_path: The filesystem path to the directory
        
    Returns:
        A human-readable display name
    """
    path = Path(directory_path)
    
    # Get the directory name
    dir_name = path.name
    
    # Check if this is a common pattern like "project_name/prompts"
    parent_name = path.parent.name
    
    # Special case: if directory is "prompts" and parent contains meaningful name
    if dir_name.lower() == "prompts" and parent_name:
        # Use the parent directory name
        base_name = parent_name
    else:
        # Use the directory name itself
        base_name = dir_name
    
    # Convert underscores and hyphens to spaces
    display_name = base_name.replace('_', ' ').replace('-', ' ')
    
    # Title case each word
    display_name = ' '.join(word.capitalize() for word in display_name.split())
    
    return display_name


def normalize_path(path_str: str) -> str:
    """Normalize a path string: resolve ., .., handle multiple leading slashes, and remove trailing slashes."""
    normalized = os.path.normpath(os.path.expanduser(path_str))

    # If os.path.normpath preserved a double leading slash (e.g., '//foo/bar'),
    # and it's not a root like '//' (which normpath would likely turn to '/'),
    # reduce it to a single leading slash.
    if normalized.startswith(os.sep + os.sep) and len(normalized) > len(os.sep + os.sep):
        normalized = normalized[len(os.sep):]
    
    # Remove trailing slash, but not if it's the root itself.
    if normalized.endswith(os.sep) and normalized != os.sep:
        normalized = normalized.rstrip(os.sep)
    return normalized


def validate_directory(directory_path: str) -> tuple[bool, str]:
    """
    Validate that a directory path exists and is accessible.
    
    Args:
        directory_path: The path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    expanded_path = os.path.expanduser(directory_path)
    
    if not os.path.exists(expanded_path):
        return False, f"Directory does not exist: {expanded_path}"
    
    if not os.path.isdir(expanded_path):
        return False, f"Path is not a directory: {expanded_path}"
    
    if not os.access(expanded_path, os.R_OK):
        return False, f"Directory is not readable: {expanded_path}"
    
    return True, ""


def load_config() -> List[Dict[str, Any]]:
    """Load existing configuration from JSON file."""
    config_file = get_config_file_path()
    
    if not os.path.exists(config_file):
        print(f"🔧 Configuration file doesn't exist yet: {config_file}")
        return []
    
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"⚠️  Configuration file format is invalid (expected list, got {type(data)})")
            return []
        
        return data
    except json.JSONDecodeError as e:
        print(f"❌ Error reading configuration file: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error loading configuration: {e}")
        return []


def save_config(config: List[Dict[str, Any]]) -> bool:
    """Save configuration to JSON file."""
    config_file = get_config_file_path()
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Write configuration
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        return True
    except Exception as e:
        print(f"❌ Error saving configuration: {e}")
        return False


def add_directories(directories: List[str], 
                   force: bool = False, 
                   dry_run: bool = False) -> int:
    """
    Add directories to the Prompt Manager configuration.
    
    Args:
        directories: List of directory paths to add
        force: If True, skip confirmation prompts
        dry_run: If True, show what would be done without making changes
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    print(f"🔍 Adding {len(directories)} director{'y' if len(directories) == 1 else 'ies'} to Prompt Manager...")
    
    # Load existing configuration
    config = load_config()
    existing_paths = {entry.get('path') for entry in config if entry.get('path')}
    
    # Validate all directories first
    validated_dirs = []
    for directory in directories:
        is_valid, error_msg = validate_directory(directory)
        if not is_valid:
            print(f"❌ Error: {error_msg}")
            return 1
        
        normalized_path = normalize_path(directory)
        display_name = generate_display_name(normalized_path)
        
        # Check if already exists
        if normalized_path in existing_paths:
            print(f"⚠️  Directory already configured: {normalized_path}")
            continue
        
        validated_dirs.append({
            'path': normalized_path,
            'display_name': display_name,
            'original_input': directory
        })
    
    if not validated_dirs:
        print("ℹ️  No new directories to add.")
        return 0
    
    # Show what will be added
    print("\n📋 Directories to add:")
    for i, dir_info in enumerate(validated_dirs, 1):
        print(f"  {i}. Path: {dir_info['path']}")
        print(f"     Name: {dir_info['display_name']}")
        
        # Check if directory has any .md files
        try:
            md_count = len(list(Path(dir_info['path']).rglob('*.md')))
            print(f"     Files: {md_count} .md files found")
        except Exception:
            print(f"     Files: Unable to scan directory")
        print()
    
    if dry_run:
        print("🔍 Dry run mode - no changes will be made")
        return 0
    
    # Confirmation prompt
    if not force:
        response = input("❓ Do you want to add these directories? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Operation cancelled")
            return 1
    
    # Add directories to configuration
    added_count = 0
    for dir_info in validated_dirs:
        config.append({
            'path': dir_info['path'],
            'name': dir_info['display_name'],
            'description': f"Added via add_prompt_dirs.py from {dir_info['original_input']}",
            'enabled': True
        })
        print(f"📁 Added: {dir_info['display_name']} ({dir_info['path']})")
        added_count += 1
    
    # Save configuration
    if save_config(config):
        print(f"\n🎉 Operation completed: {added_count} new director{'y' if added_count == 1 else 'ies'} added")
        print(f"📝 Configuration saved to: {get_config_file_path()}")
        print("\n💡 You can now:")
        print("   • Restart the Prompt Manager service to load the new prompts:")
        print("     sudo systemctl restart prompt-manager.service")
        print("   • Or use the Prompt Manager web interface to reload directories")
        print(f"   • Access the web interface at: http://nara:8095/")
        return 0
    else:
        print("❌ Failed to save configuration")
        return 1


def list_directories():
    """List currently configured directories."""
    config = load_config()
    
    if not config:
        print("📂 No directories configured yet.")
        return
    
    print(f"📂 Currently configured directories ({len(config)}):")
    for i, entry in enumerate(config, 1):
        status = "✅ enabled" if entry.get('enabled', True) else "❌ disabled"
        print(f"  {i}. {entry.get('name', 'Unnamed')} ({status})")
        print(f"     Path: {entry.get('path', 'Unknown')}")
        if entry.get('description'):
            print(f"     Description: {entry['description']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Add prompt directories to Prompt Manager",
        epilog="""
Examples:
  %(prog)s /home/jem/development/prompt_manager/prompts
  %(prog)s /home/jem/claude_prompts /home/jem/ai_templates
  %(prog)s --dry-run /path/to/test/directory
  %(prog)s --list
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'directories',
        nargs='*',
        help='One or more directory paths to add to Prompt Manager'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List currently configured directories'
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='add_prompt_dirs.py 1.0.0'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_directories()
        return 0
    
    if not args.directories:
        parser.print_help()
        return 1
    
    return add_directories(
        directories=args.directories,
        force=args.force,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"❌ Unexpected error: {e}")
        print("Stack trace:")
        traceback.print_exc()
        sys.exit(1)
