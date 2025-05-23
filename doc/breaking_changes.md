# Prompt Manager - Breaking Changes Log

This document tracks instances where functionality was unintentionally broken during development,
the symptoms, how it was fixed, and where possible, the cause and when it was introduced.

---

## Entry 1: Expanded Content on Prompt Editor Page Fails Intermittently

*   **Timestamp (Discovery):** User reported this after Search/Replace and ReferencedBy fixes.
*   **Symptom:** "Expand Content" tab on the Prompt Editor page (toggled by Alt+T or click) would sometimes not respond initially. Console logs showed `[DEBUG] toggleView: Bootstrap Tab instances not found.` indicating that `bootstrap.Tab.getInstance()` was failing for `rawContentTab` or `expandedContentTab`.
*   **Fix:** Modified the `toggleView` function in `src/templates/prompt_editor.html` to use `bootstrap.Tab.getOrCreateInstance(tabElement)` instead of `bootstrap.Tab.getInstance(tabElement)`. This ensures that a Tab instance is created if one doesn't already exist when `toggleView` is called, making it more resilient to timing issues with Bootstrap's JavaScript initialization.
*   **Cause/When Broken:** The `toggleView` function was trying to get Bootstrap tab instances using `getInstance()`. If called before Bootstrap had fully initialized these specific tab components (e.g., via early keyboard shortcut use), `getInstance()` would return null, preventing the view toggle. This became apparent after other JavaScript modifications on the page, possibly altering script execution timing.

---

## Entry 2: Search/Replace on Prompt Editor Page Not Working

*   **Timestamp (Discovery):** User reported this recently before the current "Expand Content" issue.
*   **Symptom:** The Search/Replace button on the Prompt Editor page did not open a functional search/replace dialog or perform replacements.
*   **Fix:**
    *   In `src/templates/prompt_editor.html`, within the `DOMContentLoaded` event listener:
        1.  Ensured the custom `SearchReplace` class (from `/static/js/search-replace.js`) was instantiated after the CodeMirror `editor` was initialized: `const searchReplace = new SearchReplace(editor);`.
        2.  The event listener for the "Search/Replace" button (`#search-replace-btn`) was updated to call `searchReplace.showDialog();` on this instance, only if the "Raw Content" tab is active.
*   **Cause/When Broken:** The button was previously attempting to use a generic CodeMirror command `editor.execCommand("replace")` which was not correctly set up or was not using the intended custom `SearchReplace` functionality. This was likely the state for some time until explicitly addressed.

---

## Entry 3: "Referenced By" Table on Prompt Editor Shows Error

*   **Timestamp (Discovery):** User reported this recently, around the same time as the Search/Replace issue.
*   **Symptom:** The "Referenced By" section on the Prompt Editor page showed an error like `Error loading referenced_by: SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON`.
*   **Fix:**
    1.  Added the missing API endpoint `GET /api/prompts/{prompt_id}/referenced_by` to `src/api/router.py`.
    2.  Implemented the corresponding service method `prompt_service.get_references_to_prompt(prompt_id)` in `src/services/prompt_service.py` to return a `List[Dict]` as expected by the frontend.
    3.  The JavaScript `updateReferencedByUI` in `src/templates/prompt_editor.html` was already trying to fetch this endpoint and parse JSON, so it started working once the backend was correct.
*   **Cause/When Broken:** The API endpoint `/api/prompts/{prompt_id}/referenced_by` did not exist. The frontend was requesting it, and the server returned a generic HTML 404 page, which caused a JSON parsing error in the client. This was likely an oversight when the "Referenced By" feature was initially conceived or partially implemented.

---

## Entry 4: Prompt Editor Page - Content Not Loading, Buttons Work (then other issues)

*   **Timestamp (Discovery):** During recent debugging session.
*   **Symptom Phase 1:** Prompt editor page (`prompt_editor.html`) loaded, editor box was active, but no prompt content (title, description, editor content) was displayed. Buttons were responsive.
*   **Fix Phase 1:** The main `<script>` block in `prompt_editor.html` was incorrectly placed inside an `{% block extra_css %}` Jinja block. It was moved to the correct `{% block page_specific_js %}` block (which is rendered at the end of the `<body>` in `base.html`).
*   **Symptom Phase 2 (after Phase 1 fix):** "Expanded Content" tab showed "Error loading expanded content: Failed to fetch expanded content: 404". Server log: `GET /api/prompts/mie_admin/expanded HTTP/1.1" 404 Not Found`.
*   **Fix Phase 2:** The `getExpandedContent` JavaScript function in `prompt_editor.html` was using `GET /api/prompts/{promptId}/expanded`. This was changed to make a `POST` request to the correct endpoint `/api/prompts/expand` and send the `prompt_id` in the JSON body.
*   **Cause/When Broken:**
    *   Phase 1: Template inheritance issue – incorrect Jinja block name used for page-specific JavaScript.
    *   Phase 2: Frontend API call was using the wrong HTTP method and endpoint for fetching expanded content.

---

## Entry 5: Homepage (Manage Prompts) - Tables Not Loading (Stuck on Spinner)

*   **Timestamp (Discovery):** During recent debugging session.
*   **Symptom:** Directories and prompts tables on `manage_prompts.html` were stuck on "Loading..." spinners. No browser console errors initially. Server logs showed no requests for `/api/prompts/all` or `/api/prompts/directories/all`.
*   **Fix:** The `manage_prompts.html` template was using `{% block extra_js %}` to include its JavaScript. However, `base.html` defined `{% block page_specific_js %}` for scripts at the end of the `<body>`. Changed `manage_prompts.html` to use `{% block page_specific_js %}`. Also, the required `/static/js/directory_manager.js` was not explicitly included; it was added within this corrected block.
*   **Cause/When Broken:** Template inheritance issue – incorrect Jinja block name used for page-specific JavaScript, leading to crucial JS files for loading data not being included/executed. This likely occurred when the Jinja blocks in `base.html` were defined or refactored.

---

## Entry 6: Header Buttons on Manage Prompts Page Unresponsive to Click

*   **Timestamp (Discovery):** User reported this after recent fixes to Prompt Editor page.
*   **Symptom:** The "New Prompt" button (ID: `add-prompt-btn`) and the main header "Add Directory" button (ID: `add-directory-modal-btn`) on the `manage_prompts.html` page did not trigger their respective modals when clicked. Keyboard shortcuts (Alt+N, Alt+A) and the secondary "Add Directory" button (within the Directories card) were functional.
*   **Fix:** Added the standard Bootstrap attributes `data-bs-toggle="modal"` and `data-bs-target="#<modalID>"` to the affected buttons in `src/templates/manage_prompts.html`:
    *   For `#add-prompt-btn`, added `data-bs-target="#newPromptModal"`.
    *   For `#add-directory-modal-btn`, added `data-bs-target="#addDirectoryModal"`.
*   **Cause/When Broken:** The buttons were missing the necessary Bootstrap data attributes to trigger modals on click. Their functionality relied solely on explicitly programmed keyboard shortcuts or other UI elements. This was likely an oversight during the initial implementation of these header buttons or a refactor that inadvertently removed/omitted these attributes.

---

## Entry 7: Toggling Directory Status Causes 500 Internal Server Error

*   **Timestamp (Discovery):** User reported on 2025-05-18.
*   **Symptom:** Attempting to enable/disable a directory from the "Manage Prompts" page resulted in a 500 Internal Server Error. The browser console showed the POST request to `/api/prompts/directories/{directory_path}/toggle` failing. Backend logs indicated a `fastapi.exceptions.ResponseValidationError` because the endpoint was returning `None` instead of the expected dictionary, and a secondary `KeyError: "'type'"` from Loguru.
*   **Fix:** Modified the `toggle_directory_status` function in `src/api/router.py` to:
    1.  Ensure it always returns `dir_to_toggle.dict()` at the end of the function, satisfying the `response_model=Dict`.
    2.  Added a call to `prompt_service._save_directory_config()` after toggling the directory's status to persist the change, similar to the `update_directory` endpoint.
*   **Cause/When Broken:** The `toggle_directory_status` endpoint did not have an explicit return statement for all code paths (e.g., if the directory's status was already the same as the requested toggle state). This led to an implicit `None` return, violating the `response_model=Dict`. Additionally, the configuration change wasn't being saved. This was likely an oversight in the initial implementation of the endpoint.

---

## Entry 8: Directory Name Shows as "-" in Prompt Editor Metadata

*   **Timestamp (Discovery):** User reported on 2025-05-18.
*   **Symptom:** On the Prompt Editor page (`prompt_editor.html`), the "Directory" field in the "Metadata" card was displaying as "-" for all prompts.
*   **Fix:** Modified the `get_prompt_by_id` function in `src/api/router.py`. Previously, it was adding a flat `directory_name` string to the response. The fix involved:
    1.  Calling `get_directory_by_path` (from `src.services.prompt_dirs`) to fetch the directory's configured details.
    2.  Structuring this information into a nested object `prompt_dict["directory_info"]` with `"name"` and `"path"` keys.
    3.  The frontend JavaScript (`updateMetadataUI` in `prompt_editor.html`) was already expecting `currentPromptData.directory_info.name`, so it started working correctly once the backend provided the data in the expected structure.
*   **Cause/When Broken:** There was a mismatch between the data structure provided by the `GET /api/prompts/{prompt_id}` backend endpoint and what the frontend JavaScript expected for displaying the directory name. The backend was providing a flat `directory_name`, while the frontend looked for `directory_info.name`. This was likely a regression or an oversight from a previous refactor of either the frontend or backend.

--- 