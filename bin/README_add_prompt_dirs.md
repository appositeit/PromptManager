# Add Prompt Directories Tool

A command-line utility for managing prompt directories in the Prompt Manager system.

## Overview

The `add_prompt_dirs.py` tool allows you to easily add one or more directories to your Prompt Manager configuration. It automatically generates human-readable display names based on directory paths and integrates directly with the Prompt Manager's JSON configuration file.

## Features

- **Automatic Display Name Generation**: Converts directory paths to readable names
- **Validation**: Checks that directories exist and are accessible
- **Safety Features**: Dry-run mode and confirmation prompts
- **List Current Configuration**: View currently configured directories
- **Duplicate Detection**: Prevents adding the same directory twice
- **File Counting**: Shows how many `.md` files are in each directory

## Installation

The tool is already installed in the Prompt Manager's `bin/` directory:

- **Python Script**: `/mnt/data/jem/development/prompt_manager/bin/add_prompt_dirs.py`
- **Bash Wrapper**: `/mnt/data/jem/development/prompt_manager/bin/add-prompt-dirs`

## Usage

### Basic Usage

```bash
# Add a single directory
python /mnt/data/jem/development/prompt_manager/bin/add_prompt_dirs.py /path/to/your/prompts

# Add multiple directories
python /mnt/data/jem/development/prompt_manager/bin/add_prompt_dirs.py /path/to/dir1 /path/to/dir2

# Using the bash wrapper (shorter)
/mnt/data/jem/development/prompt_manager/bin/add-prompt-dirs /path/to/your/prompts
```

### Command Line Options

```bash
# Show help
add_prompt_dirs.py --help

# List currently configured directories
add_prompt_dirs.py --list

# Dry run (show what would be done without making changes)
add_prompt_dirs.py --dry-run /path/to/directory

# Skip confirmation prompts
add_prompt_dirs.py --force /path/to/directory

# Show version
add_prompt_dirs.py --version
```

## Display Name Generation

The tool automatically generates human-readable display names from directory paths:

| Directory Path | Generated Display Name |
|----------------|----------------------|
| `/home/jem/development/prompt_manager/prompts` | **Prompt Manager** |
| `/home/jem/claude_prompts` | **Claude Prompts** |
| `/home/jem/ai_templates` | **Ai Templates** |
| `/home/jem/my_custom_directory` | **My Custom Directory** |

### Rules:
1. If the directory is named "prompts", use the parent directory name
2. Convert underscores (`_`) and hyphens (`-`) to spaces
3. Title-case each word

## Examples

### Example 1: Add a Single Directory
```bash
$ python add_prompt_dirs.py /home/jem/claude_prompts
🔍 Adding 1 directory to Prompt Manager...

📋 Directories to add:
  1. Path: /home/jem/claude_prompts
     Name: Claude Prompts
     Files: 15 .md files found

❓ Do you want to add these directories? [y/N]: y
📁 Added: Claude Prompts (/home/jem/claude_prompts)

🎉 Operation completed: 1 new directory added
📝 Configuration saved to: /home/jem/.prompt_manager/prompt_directories.json

💡 You can now:
   • Restart the Prompt Manager service to load the new prompts:
     sudo systemctl restart prompt-manager.service
   • Or use the Prompt Manager web interface to reload directories
   • Access the web interface at: http://nara:8095/
```

### Example 2: List Current Directories
```bash
$ python add_prompt_dirs.py --list
📂 Currently configured directories (5):
  1. AI Prompts (✅ enabled)
     Path: /home/jem/ai/prompts

  2. Nara Admin (✅ enabled)
     Path: /home/jem/development/nara_admin/prompts

  3. Mie Admin (✅ enabled)
     Path: /home/jem/development/mie_admin/prompts

  4. Claude Desktop decompilation (✅ enabled)
     Path: /home/jem/ai/mcp/claude_desktop/prompts

  5. Open WebUI Nara (✅ enabled)
     Path: /home/jem/development/openwebui/prompts
```

### Example 3: Dry Run
```bash
$ python add_prompt_dirs.py --dry-run /tmp/test_prompts
🔍 Adding 1 directory to Prompt Manager...

📋 Directories to add:
  1. Path: /tmp/test_prompts
     Name: Test Prompts
     Files: 3 .md files found

🔍 Dry run mode - no changes will be made
```

## Integration with Prompt Manager

After adding directories, you need to reload the Prompt Manager to see the new prompts:

### Option 1: Restart the Service
```bash
sudo systemctl restart prompt-manager.service
```

### Option 2: Use the Web Interface
1. Open http://nara:8095/ in your browser
2. Use the reload/refresh functionality in the web interface

## Configuration File

The tool modifies the Prompt Manager configuration file:
- **Location**: `~/.prompt_manager/prompt_directories.json`
- **Format**: JSON array of directory objects

### Configuration Structure
```json
[
  {
    "path": "/home/jem/claude_prompts",
    "name": "Claude Prompts",
    "description": "Added via add_prompt_dirs.py from /home/jem/claude_prompts",
    "enabled": true
  }
]
```

## Error Handling

The tool validates directories before adding them:

- ✅ **Directory exists**: Checks if the path exists on the filesystem
- ✅ **Is a directory**: Ensures the path points to a directory, not a file
- ✅ **Readable**: Verifies the directory can be read
- ✅ **No duplicates**: Prevents adding the same directory twice

## Troubleshooting

### Common Issues

**"Directory does not exist"**
- Check that the path is correct
- Use absolute paths when possible
- Ensure you have permission to access the directory

**"Directory already configured"**
- Use `--list` to see currently configured directories
- The tool prevents duplicate entries automatically

**"Permission denied"**
- Ensure you have read access to the directory
- Check file system permissions

### Debug Mode

For troubleshooting, you can run the script with Python's debug output:
```bash
python -v /mnt/data/jem/development/prompt_manager/bin/add_prompt_dirs.py --dry-run /path/to/directory
```

## Development

The tool is designed to be:
- **Standalone**: No dependencies on the Prompt Manager service being running
- **Safe**: Multiple validation steps and confirmation prompts
- **Extensible**: Easy to modify for additional features

### File Structure
```
/mnt/data/jem/development/prompt_manager/bin/
├── add_prompt_dirs.py      # Main Python script
├── add-prompt-dirs         # Bash wrapper script
└── README_add_prompt_dirs.md  # This documentation
```

## See Also

- **Prompt Manager Service**: `systemctl status prompt-manager.service`
- **Web Interface**: http://nara:8095/
- **Configuration File**: `~/.prompt_manager/prompt_directories.json`
- **Project Documentation**: `/mnt/data/jem/development/prompt_manager/doc/`
