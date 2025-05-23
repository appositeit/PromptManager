# Prompt Manager User Guide

## 1. Introduction

Welcome to the Prompt Manager! This guide provides a comprehensive overview of its features and functionalities, designed to help you efficiently create, organize, manage, and utilize text-based prompts.

Prompt Manager is ideal for developers, writers, researchers, and anyone working extensively with AI prompts, text templates, or reusable content snippets. It supports dynamic composition of prompts through inclusions, real-time collaboration, and robust API access.

## 2. Core Concepts

Understanding these core concepts will help you make the most of Prompt Manager:

*   **Prompts**: The fundamental unit in Prompt Manager. Each prompt is stored as an individual Markdown (`.md`) file. It has a unique **ID** (derived from its filename, e.g., `my_prompt.md` has an ID `my_prompt`), content, and associated metadata.
*   **Metadata**: Information about a prompt, such as its `description` and `tags`. This is embedded directly within the prompt's `.md` file using YAML front matter, enclosed by `---` lines at the beginning of the file.
    ```markdown
    ---
    description: An example prompt for demonstration.
    tags:
      - example
      - tutorial
    ---
    This is the actual content of the prompt.
    ```
*   **Prompt Directories**: Physical directories on your filesystem where prompt files are stored. Prompt Manager can manage prompts across multiple directories, allowing for flexible organization (e.g., by project, by type).
*   **Inclusions & Expansion**: A powerful feature allowing you to embed one prompt within another using the `[[prompt_id]]` syntax. When a prompt is "expanded," these inclusion tags are recursively replaced with the content of the referenced prompts.
*   **Unique ID**: While a prompt ID is its filename stem, a system-generated `unique_id` (often combining directory information with the prompt ID) is used internally for unambiguous referencing, especially when multiple prompts might share the same base ID across different directories.

## 3. Getting Started

### Server Management
The Prompt Manager server can be controlled using scripts located in the `bin/` directory of your project:
*   `bin/start_prompt_manager.sh`: Starts the server. It handles virtual environment setup and log initialization.
*   `bin/stop_prompt_manager.sh`: Stops the server.
*   `bin/restart_prompt_manager.sh`: Restarts the server.

These scripts are the recommended way to manage the server lifecycle.

### Accessing the UI
Once the server is running (typically on `http://localhost:8081` by default), you can access the Prompt Manager user interface through your web browser.
*   **Main Page**: `http://localhost:8081/` (which redirects to `/manage/prompts`)
*   **Prompt Editor**: `http://localhost:8081/prompts/{prompt_id}`

## 4. User Interface Overview

### 4.1. Main Page / Prompt Management View (`/manage/prompts`)

This view is the central hub for managing your prompts and directories.

**Features:**

*   **Prompt List**: Displays all available prompts from enabled directories.
    *   **Columns**: Typically include `ID`, `Name` (often same as ID), `Description`, `Tags`, and `Directory`.
    *   **Sorting**: Columns are usually sortable by clicking on their headers.
*   **Filtering/Searching Prompts**: A search bar is available to filter the prompt list by ID, content, description, or tags.
*   **Creating a New Prompt**:
    *   Click the "Create Prompt" or similar button.
    *   You'll be prompted to provide an **ID** and select a **Directory**. Description and tags can be added later in the editor.
*   **Managing Directories**:
    *   View a list of configured prompt directories.
    *   **Add Directory**: Specify a path to a new directory containing prompts.
    *   **Remove Directory**: Remove a directory from Prompt Manager's configuration (does not delete files).
    *   **Enable/Disable Directory**: Toggle whether prompts from a specific directory are loaded and displayed.
    *   **Reload Directory/All Prompts**: Manually trigger a reload of prompts from disk for a specific directory or all directories.

**Keyboard Shortcuts (Main Page):**
*   Standard browser shortcuts apply (e.g., `Ctrl+F` / `Cmd+F` for page search).
*   Specific application-level shortcuts for this page are not explicitly documented but may include tabbing through elements and `Enter` to activate buttons/links.

### 4.2. Prompt Editor View (`/prompts/{prompt_id}`)

This is where you edit individual prompts, their metadata, and see how they expand.

**Layout:**
The editor view is typically divided into several panes/tabs:
*   **Edit Tab / Editor Pane**: A rich text editor (likely CodeMirror) for modifying the raw Markdown content of your prompt.
*   **Metadata Pane**: Fields to view and edit the prompt's `description` and `tags`.
*   **Expanded View / Preview Pane**: Shows the current prompt's content with all `[[inclusion_tags]]` fully resolved. This is a read-only view.
*   **References Pane**: Lists other prompts that include the current prompt, and prompts that the current prompt includes.

**Editing Content (Editor Pane):**
*   **Markdown Editing**: The editor supports standard Markdown syntax.
*   **Tab Completion for Inclusions**:
    *   When you type `[[`, an autocomplete dropdown should appear, suggesting available `prompt_id`s from all loaded prompts.
    *   This list is populated by an API call (typically to `/api/prompts/all`) when the editor's WebSocket connection is established.
    *   Use arrow keys to navigate suggestions and `Enter` or `Tab` to select one, completing the `[[prompt_id]]` tag.
*   **Saving Prompts**:
    *   **Save Button**: Manually save your changes to content and metadata.
    *   **Real-time Save (via WebSocket)**: Changes are often sent to the server in real-time or near real-time. A status indicator (e.g., "Saved", "Saving...") should reflect this. If the WebSocket connection fails, the UI will typically fall back to using the REST API for saving, which might be less immediate.

**Editing Metadata (Metadata Pane):**
*   **Description**: A text field for a longer description of your prompt.
*   **Tags**: A list or tag input field to associate keywords with your prompt. Tags are typically comma-separated or added individually.
*   Changes here are also saved via the Save button or WebSocket.

**Viewing Expanded Content (Expanded View Pane):**
*   This pane displays the fully rendered version of your prompt.
*   Any `[[prompt_id]]` inclusions will be replaced by the content of those prompts.
*   If there are issues like "Prompt Not Found" or "Circular Dependency," warning messages will be displayed directly in the expanded content.

**Viewing References (References Pane):**
*   **Included By**: Shows a list of other prompts that use the current prompt (i.e., contain `[[current_prompt_id]]`).
*   **Includes**: Shows a list of prompt IDs that the current prompt directly includes in its content.

**Search and Replace in Editor:**
*   **Accessing**:
    *   Press `Alt-R` to open the Search/Replace dialog.
*   **Dialog Features**:
    *   **Search Input**: Enter text or a regular expression to search for.
    *   **Replace Input**: Enter text to replace matches with.
    *   **Use Regex**: Checkbox to enable regular expression mode for searching.
    *   **Match Case**: Checkbox to make the search case-sensitive.
    *   **Buttons**:
        *   `Find Next` / `Find Previous`: Navigate through matches.
        *   `Replace`: Replace the current highlighted match and move to the next.
        *   `Replace All`: Replace all occurrences in the editor.
        *   `Cancel`/`Close`: Close the dialog.
    *   **Match Info**: Displays the number of matches found (e.g., "1 of 5").
*   **Keyboard Shortcuts (within Search/Replace Dialog)**:
    *   `Esc`: Close dialog.
    *   `Enter`: Replace current match and find next.
    *   `Shift+Enter`: Find Previous match.
    *   `Ctrl+Enter` (or `Cmd+Enter`): Replace All matches.
    *   `F3` or `Ctrl+G` (or `Cmd+G`): Find Next match.
    *   `Shift+F3` or `Ctrl+Shift+G` (or `Cmd+Shift+G`): Find Previous match.

**General Keyboard Shortcuts (Prompt Editor - many are standard CodeMirror/text editor behavior):**
*   **Saving**:
    *   `Ctrl+S` (or `Cmd+S`): Save the current prompt (should trigger the save mechanism).
*   **Basic Editing**:
    *   `Ctrl+Z` (or `Cmd+Z`): Undo last action.
    *   `Ctrl+Y` (or `Cmd+Y` / `Ctrl+Shift+Z` or `Cmd+Shift+Z`): Redo last undone action.
    *   `Ctrl+X` (or `Cmd+X`): Cut selected text.
    *   `Ctrl+C` (or `Cmd+C`): Copy selected text.
    *   `Ctrl+V` (or `Cmd+V`): Paste text from clipboard.
    *   `Ctrl+A` (or `Cmd+A`): Select all content in the editor.
*   **Navigation (Editor Pane)**:
    *   Arrow keys: Move cursor.
    *   `Home`/`End`: Go to beginning/end of line.
    *   `Ctrl+Home` / `Ctrl+End` (or `Cmd+Home` / `Cmd+End`): Go to beginning/end of document.
    *   `PageUp`/`PageDown`: Scroll up/down.
*   **Indentation**:
    *   `Tab`: Indent selected lines or insert a tab character.
    *   `Shift+Tab`: Un-indent selected lines.
*   **Line Operations**:
    *   `Ctrl+D` (or `Cmd+D`): Duplicate current line or selection. (Common in some editors, may vary)
    *   `Ctrl+Shift+K` (or `Cmd+Shift+K`): Delete current line. (Common in some editors, may vary)
*   **Find (within editor, if not using dedicated Search/Replace dialog)**:
    *   `Ctrl+F` (or `Cmd+F`): Open basic find bar within the editor.
*   **Navigation between UI Panes/Tabs**:
    *   While not explicitly documented, standard web navigation like `Tab` and `Shift+Tab` should move focus between UI elements (editor, metadata fields, buttons, tabs). `Enter` or `Space` can often activate focused buttons or switch tabs.
    *   *Suggestion*: It would be beneficial if dedicated shortcuts existed to quickly switch between the Edit, Expanded, and Metadata views/panes (e.g., `Alt+1`, `Alt+2`, `Alt+3`).

## 5. Advanced Features

### 5.1. Prompt Inclusions In-Depth
The `[[prompt_id]]` syntax is the cornerstone of creating complex, reusable prompts.
*   **Resolution**: When a prompt is expanded, Prompt Manager looks for `[[...]]` tags. The `prompt_id` inside the brackets is used to find the corresponding prompt file (e.g., `[[my_other_prompt]]` looks for `my_other_prompt.md`).
*   **Nested Inclusions**: Included prompts can themselves contain further inclusions. These are resolved recursively.
*   **Circular Dependency Handling**: Prompt Manager detects if an inclusion chain would result in an infinite loop (e.g., Prompt A includes Prompt B, and Prompt B includes Prompt A). If detected, it stops expansion at that point and usually inserts a warning message like `[[CIRCULAR DEPENDENCY: prompt_id]]`.
*   **Prompt Not Found**: If an inclusion tag refers to a `prompt_id` that doesn't exist, a warning like `[[PROMPT NOT FOUND: prompt_id]]` is typically inserted into the expanded content.

### 5.2. Working with Multiple Directories
Organizing prompts into different directories helps manage large collections or separate concerns.
*   **Configuration**: Directory paths are stored in a configuration file (typically `~/.prompt_manager/prompt_directories.json`).
*   **Loading**: Only enabled directories are scanned for prompts when the server starts or when a reload is triggered.
*   **Prompt ID Uniqueness**: While prompt IDs (filenames) can be the same across different directories, the system uses a more unique internal identifier that often incorporates the directory path to distinguish them. When using `[[prompt_id]]` for inclusions, the system searches across all loaded prompts. If multiple prompts share the same ID, the behavior for which one is chosen might be based on load order or might require disambiguation (the `get_prompt` API endpoint allows specifying a directory for disambiguation).

## 6. API Reference

Prompt Manager provides a RESTful API for programmatic interaction. The API prefix is typically `/api`. (A more detailed API specification might be available via an OpenAPI/Swagger UI endpoint like `/docs` on the server, if configured).

**Key Endpoint Groups:**

*   **Prompts (`/api/prompts`)**:
    *   `GET /all`: Get metadata for all loaded prompts.
    *   `GET /{prompt_id}`: Get full details of a specific prompt.
    *   `POST /`: Create a new prompt.
    *   `PUT /{prompt_id}`: Update an existing prompt.
    *   `DELETE /{prompt_id}`: Delete a prompt.
    *   `POST /rename`: Rename a prompt.
    *   `POST /expand`: Expand content with inclusions.
    *   `GET /check_exists/{prompt_id}`: Check if a prompt ID exists.
*   **Prompt Directories (`/api/prompts/directories`)**:
    *   `GET /all`: List all configured prompt directories.
    *   `POST /`: Add a new directory.
    *   `PUT /{directory_path:path}`: Update properties of a directory.
    *   `DELETE /{directory_path:path}`: Remove a directory from configuration.
    *   `POST /{directory_path:path}/toggle`: Enable/disable a directory.
    *   `POST /{directory_path:path}/reload`: Reload prompts from a specific directory.
*   **Server Actions**:
    *   `POST /api/prompts/reload`: Reload all prompts from all enabled directories.
    *   `GET /api/exit`: (If enabled) Shuts down the server.
*   **WebSockets (`/ws/prompts/{prompt_id}`)**:
    *   Provides real-time bidirectional communication for prompt editing and updates. Messages are JSON objects with an `action` field (see `websocket_protocol.md` for details).

## 7. Troubleshooting

*   **WebSocket Connection Issues**:
    *   Ensure the server is running and accessible.
    *   Check browser console for error messages.
    *   The UI may show a "WebSocket connection error. Falling back to API." message. This means real-time updates are off, but saving should still work.
*   **Prompt Not Found Errors**:
    *   Verify the `prompt_id` in your inclusion tag `[[prompt_id]]` exactly matches the filename (without `.md`) of an existing prompt in an enabled directory.
    *   Ensure the directory containing the prompt is enabled in the Prompt Manager settings.
*   **Circular Dependencies**:
    *   Review your prompt inclusion chains. If Prompt A includes B, and B includes A, this will cause an error. Refactor your prompts to break the cycle.
*   **Log Files**:
    *   Server logs are crucial for diagnosing issues. They are typically found in the `logs/` directory of the project (e.g., `logs/prompt_manager.log` and timestamped versions). These logs contain information about server startup, API requests, WebSocket activity, and errors.

## 8. Keyboard Shortcut Summary

| Scope                     | Shortcut                                       | Action                                           |
| ------------------------- | ---------------------------------------------- | ------------------------------------------------ |
| **Prompt Editor**         | `Alt-R`                                        | Open Search/Replace Dialog                       |
|                           | `Ctrl+S` / `Cmd+S`                             | Save Prompt                                      |
|                           | `Ctrl+Z` / `Cmd+Z`                             | Undo                                             |
|                           | `Ctrl+Y` / `Cmd+Y` (or `Ctrl+Shift+Z`)       | Redo                                             |
|                           | `Ctrl+F` / `Cmd+F`                             | Basic Find (within editor component)             |
| **Search/Replace Dialog** | `Esc`                                          | Close Dialog                                     |
|                           | `Enter`                                        | Replace current match & Find Next                |
|                           | `Shift+Enter`                                  | Find Previous match                            |
|                           | `Ctrl+Enter` / `Cmd+Enter`                     | Replace All                                      |
|                           | `F3` or `Ctrl+G` / `Cmd+G`                     | Find Next match                            |
|                           | `Shift+F3` or `Ctrl+Shift+G` / `Cmd+Shift+G` | Find Previous match                            |

*(Standard text editing shortcuts like Cut, Copy, Paste, Select All, line operations, and navigation keys are generally available in the editor pane, behaving as they would in a typical CodeMirror or similar text editor.)*

---

This guide provides a comprehensive starting point. Further details on specific API message formats, advanced configurations, or development contributions would typically be found in separate, dedicated documents (e.g., `API_REFERENCE.md`, `CONTRIBUTING.md`). 