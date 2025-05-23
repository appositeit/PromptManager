# Feature: Tab Completion for Add Directory Input

## 1. Feature Description

This feature introduces tab-completion functionality to the directory path input field used when adding a new prompt directory via the "Add Directory" feature on the Prompt Management page (`/manage/prompts`). The goal is to enhance user experience by making it faster and more accurate to input directory paths, similar to tab completion in a command-line terminal.

### User Experience:

1.  **Initiation**: The user clicks the "Add Directory" button, and an input field appears for the directory path.
2.  **Typing a Path**: The user begins typing a partial directory path (e.g., `/home/user/proj`).
3.  **Triggering Completion**: When the user presses the `Tab` key within this input field:
    *   The system sends the current partial path to the backend.
    *   The backend searches the server's filesystem for directories matching the prefix.
4.  **Completion Behavior**:
    *   **Single Match**: If only one directory extends the typed path (e.g., typed `/home/user/proj`, matches `/home/user/projects/`), the input field auto-updates to the matched path, typically with a trailing slash (e.g., `/home/user/projects/`).
    *   **Multiple Matches (Common Prefix)**: If multiple directories share a longer common prefix than what was typed (e.g., typed `/var/l`, matches `/var/lib/` and `/var/local/`), the input field updates to the longest common prefix (e.g., `/var/l`). A subsequent `Tab` press might then list the distinct options (`lib/`, `local/`).
    *   **Multiple Matches (Suggestion List)**: If multiple distinct options exist after a common prefix, or if `Tab` is pressed again, a list of possible completions could be displayed below the input field. Users could navigate this list (e.g., with arrow keys) and select an option (e.g., with `Enter`).
    *   **No Match**: If no matching directories are found, pressing `Tab` should provide some feedback (e.g., no change, or a subtle visual cue).
    *   **Recursive Completion**: The completion should allow navigating deeper into the filesystem. After a directory is completed (e.g., `/home/user/projects/`), typing a subsequent partial name (e.g., `my_app`) and pressing `Tab` should attempt completion within `/home/user/projects/`.

## 2. Implementation Plan

This feature will require changes to both the frontend (JavaScript) and the backend (Python/FastAPI).

### 2.1. Backend (Python/FastAPI)

*   **New API Endpoint**: Create a new API endpoint, for example, `POST /api/filesystem/complete_path`.
    *   **Request Body**: Will accept a JSON object with the `partial_path` string.
        ```json
        {
            "partial_path": "/home/user/doc"
        }
        ```
    *   **Response Body**: Will return a JSON object containing:
        *   `completed_path`: The single completed path if only one match exists, or the longest common prefix if multiple matches share one.
        *   `suggestions`: A list of strings representing possible next path components if multiple distinct options exist beyond the `completed_path`.
        *   `is_directory`: A boolean indicating if the `completed_path` (if a single match) is a directory.
        ```json
        // Example 1: Single match
        {
            "completed_path": "/home/user/documents/",
            "suggestions": [],
            "is_directory": true 
        }

        // Example 2: Multiple matches with common prefix
        {
            "completed_path": "/var/lo",
            "suggestions": ["cal/", "ck/", "g/"], // suggesting local/, lock/, log/
            "is_directory": true // or false if /var/lo is not a dir itself
        }

        // Example 3: No further completion but multiple options
        {
            "completed_path": "/home/user/projects/", // if user typed this and tabbed
            "suggestions": ["app1/", "lib2/", "data3/"],
            "is_directory": true
        }
        ```
*   **Filesystem Logic (in a new service or utility module)**:
    *   Implement a function that takes a `partial_path`.
    *   This function will use Python's `os` and `glob` modules (or `pathlib`) to scan the filesystem.
    *   **Security**: Crucially, this scanning must be restricted to prevent arbitrary filesystem exploration. For a local tool, this might mean starting searches from the user's home directory, the project root, or a predefined list of allowed base paths. It should not allow navigating to sensitive system areas (e.g., `/etc`, `/root`) unless explicitly intended and configured.
    *   The logic will need to handle:
        *   Finding all directories (and possibly files, though directories are primary) that start with the `partial_path`.
        *   Determining the longest common prefix if multiple matches are found.
        *   Generating a list of unique next components if multiple distinct matches exist.
        *   Handling edge cases: empty `partial_path`, path to a file, non-existent path.
    *   Consider using `os.path.expanduser("~")` to correctly resolve paths starting with `~`.

### 2.2. Frontend (JavaScript)

*   **Event Listener**: In the JavaScript code for the Prompt Management page (`/manage/prompts`), attach a `keydown` event listener to the directory path input field.
*   **Handle `Tab` Key**: Inside the listener, specifically check for the `Tab` key press (`event.key === 'Tab'`).
    *   Prevent default tab behavior (which would normally move focus to the next form element) using `event.preventDefault()`.
*   **API Call**: When `Tab` is pressed:
    *   Get the current value of the input field (`partial_path`).
    *   Make an asynchronous `fetch` request to the new backend endpoint (`/api/filesystem/complete_path`) with the `partial_path`.
*   **Update Input Field/Show Suggestions**: Based on the API response:
    *   If `completed_path` is returned and it's a single, unambiguous completion, update the input field's value to `completed_path`.
    *   If `suggestions` are returned, dynamically create and display a small dropdown/list below the input field showing these suggestions. This list should be navigable (e.g., arrow keys) and allow selection (e.g., `Enter` key), which would then update the input field and potentially re-trigger a completion request for the new path.
    *   Carefully manage focus and state (e.g., if a suggestion list is open, `Tab` might cycle through suggestions or close the list).
*   **UI for Suggestions (Optional but Recommended)**:
    *   Style the suggestion list appropriately.
    *   Ensure it's accessible (ARIA attributes).
    *   Handle clicks on suggestions to select them.

### 2.3. Considerations & Refinements

*   **Performance**: Filesystem scanning can be slow on large directories. The backend should be optimized, and perhaps limit the depth or number of results. For very common base paths (like `/`), initial tab completion might be disabled or limited until more characters are typed.
*   **User Feedback**: Provide clear visual feedback (e.g., a spinner or subtle loading indicator) if the backend call takes a moment.
*   **Error Handling**: Gracefully handle API errors or cases where the backend cannot provide completions.
*   **Configuration for Search Scope (Advanced)**: For a more robust solution, the allowed base paths for tab completion could be configurable by the user or system administrator, especially if Prompt Manager is used in diverse environments.
*   **Initial Implementation Focus**: Start with basic single completion and common prefix. The suggestion list for multiple matches can be a refinement if the initial implementation proves useful.

## 3. Potential Challenges

*   **Security**: Ensuring the backend filesystem scanning is appropriately sandboxed or restricted is paramount to prevent exposing sensitive parts of the server's filesystem.
*   **Cross-Platform Path Compatibility**: Ensure path handling (slashes, case sensitivity differences if targeting multiple OS for the server) is considered, though `os.path` usually abstracts this well.
*   **Frontend Complexity**: Implementing a good suggestion list UI with keyboard navigation can be tricky.

This plan outlines the major components and steps involved in implementing the tab completion feature for directory input. 