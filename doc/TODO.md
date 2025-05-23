# Project TODO List

## Code Quality

*   [ ] Run `make lint-cpd` and examine every bit of duplicated code.
    *   Decide whether the duplication should be refactored into a function call.
    *   If yes, refactor the code.
    *   If no, add it to the whitelist in `doc/code_duplication.md`.

## UI/UX Enhancements

*   [ ] **Help System:**
    *   [ ] In the top right-hand corner of each of the main web pages, add a help button (e.g., a question mark in a circle).
    *   [ ] Clicking the help button should open an overlay that floats over the main window.
    *   [ ] The overlay should contain:
        *   Help text explaining the purpose of the page.
        *   A list/table of available keyboard shortcuts for that page.
        *   A more detailed explanation of the page's functionality.
*   [ ] **Table Column Widths (Directories Page):**
    *   [ ] Adjust the "Directories" table so column widths flow better.
    *   [ ] Ensure the "Path" column is not overly crunched and avoids excessive wrapping.
    *   [ ] Allow column widths to adjust dynamically to optimize space based on content (e.g., "Description" column shouldn't be overly wide if empty).
*   [ ] **Table Row Heights:**
    *   [ ] Reduce row heights in tables across the application to display more rows on the screen at once.
*   [ ] **"Saved" Indicator:**
    *   [ ] Make the background color of the "Saved" notification/indicator less intense (e.g., ~20% of the current green color intensity) for a more subtle visual cue.
*   [ ] **Navigation Icon:**
    *   [ ] Remove "Prompt Manager:" prefix from page titles in the browser tab/title bar.
    *   [ ] Add a Prompt Manager icon (from `/home/jem/development/prompt_manager/doc/pm_logo.png`) to the top-left corner of the menu bar on each page.
    *   [ ] This icon should link to the homepage (`/manage/prompts`).
    *   [ ] Scale the icon appropriately to fit well in the menu bar.

## Content/Display

*   [ ] **Prompt Editor "Referenced By" Table:**
    *   [ ] Remove the "Type" column (which currently always shows "Composite") from the "Referenced By" table in the Prompt Editor to save space.

## MCP Client/Server Improvements (May 2025)

- [x] Implement listDirectories tool and handler in MCP server
- [x] Add list_all_directories() method to MCP client
- [ ] Implement fuzzy directory matching in the client
- [ ] Update save_prompt() to require and resolve directory using fuzzy matching
- [ ] Update documentation and examples
- [ ] Add listDirectories to the test harness and validate
- [x] Fix directory tab completion: implement or route POST /api/prompts/filesystem/complete_path to avoid 404 errors (needed for directory tab completion in UI)
- [ ] Fix prompt uniqueness: use full directory path (not just filename) as the unique identifier for prompts, so prompts with the same name can exist in different directories. (Currently, creating an 'overview' prompt in a new directory fails if it exists elsewhere.)

* BUG: In the prompt management page the Dependencies (and probably Referenced By) are not showing. 