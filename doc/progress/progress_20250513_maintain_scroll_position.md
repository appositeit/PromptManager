# Progress Update: Maintain Scroll Position When Toggling Directory Status

## Change Description
Fixed an issue where toggling a directory's status (Enable/Disable) would cause the page to scroll back to the top, forcing users to scroll down to the Directories table again. The modification now preserves the user's scroll position during status toggle operations.

## Issue
Previously, when a user clicked the status badge to toggle a directory's enabled state, the page would reload the prompts and directories, causing the browser to scroll back to the top of the page. This created a poor user experience, especially when dealing with many directories.

## Implementation Details
1. Added scroll position tracking to save the current vertical scroll position before making the API call
2. Created new functions for updating the UI without requiring a full data reload:
   - `updatePromptsWithFilteredData()`: Updates the prompts table based on the current filters
   - `updateDirectoriesUI()`: Refreshes the directories table without reloading data from the server
3. Modified the directory toggle handler to:
   - Save the current scroll position
   - Update the local data state
   - Update both UI tables
   - Restore the scroll position afterward
4. Updated the main `loadDirectories()` function to use the new `updateDirectoriesUI()` method for better code reuse

## Files Modified
- `/home/jem/development/prompt_manager/src/templates/manage_prompts.html`

## Benefits
- Users can now toggle directory status without losing their place on the page
- The interface feels much more responsive since it doesn't require reloading all data from the server
- The changes maintain all existing functionality while improving the user experience
