# Feature Specification: Regex-Based Prompt Embedding

**ID:** `feature_regex_embedding` (Suggestion)
**Status:** Proposed
**Version:** 1.0
**Date:** {{CURRENT_DATE}}

## 1. Overview

This feature proposes allowing users to embed multiple prompts into a parent prompt by specifying a regular expression that matches against prompt IDs. This enables dynamic content aggregation and reduces manual linking for sets of related prompts.

## 2. Goal

To provide a powerful mechanism for users to include and manage collections of prompts based on naming conventions or other ID patterns, enhancing modularity and maintainability.

## 3. User Story

"As a power user, I want to embed prompts using regex patterns (e.g., `[[feature.*]]`) so that I can dynamically aggregate content from multiple related prompts without manually linking each one. This aggregation should update automatically as prompts are added, removed, or renamed according to my naming conventions, reflecting the current set of matching prompts when viewed."

## 4. Proposed Syntax

Prompts would be embedded using a syntax similar to direct embedding, but the content within the double square brackets would be interpreted as a regular expression:

`[[regex_pattern]]`

**Examples:**
*   `[[feature.*]]` - Embeds all prompts whose IDs start with "feature.".
*   `[[issue:.*-critical]]` - Embeds all prompts starting with "issue:" and ending with "-critical".
*   `[[^(archive:|deprecated:).*]]` - Embeds all prompts not starting with "archive:" or "deprecated:".

## 5. Behavior

### 5.1. Backend (Prompt Expansion)

1.  **Pattern Detection:** When the prompt expansion service encounters an inclusion `[[pattern]]`, it first attempts to resolve `pattern` as a direct prompt ID.
2.  **Regex Interpretation:** If no direct match is found OR if a syntax is adopted to explicitly denote regexes (e.g. a user setting, or if `pattern` contains common regex metacharacters not typical in prompt IDs), the `pattern` is treated as a regular expression.
3.  **Matching:** The regex is applied to the list of all available and active prompt IDs.
4.  **Sorting:** All prompt IDs that match the regex are collected and sorted alphabetically (ascending).
5.  **Recursive Expansion:** Each matched prompt is then recursively expanded.
6.  **Concatenation:** The fully expanded content of each matched prompt is concatenated together, with a single newline character separating the content of one embedded prompt from the next. This combined content is then inserted into the parent prompt's expansion.
7.  **Order of Appearance:** Matched prompts are embedded in the alphabetical order of their IDs.

### 5.2. Error Handling (Backend)

*   **Invalid Regex:** If the `pattern` is an invalid regex, the expansion should result in an inline error message within the parent prompt's expanded view (e.g., `<!-- ERROR: Invalid regex: "[[invalid_regex_here]]" -->` or a user-friendly display).
*   **No Matches:** If the regex is valid but matches no prompt IDs, it should expand to an empty string. (Alternatively, a configurable placeholder comment could be inserted, e.g., `<!-- No prompts found matching "[[regex_pattern]]" -->`).
*   **Circular Dependencies:** The existing circular dependency detection mechanism should be robust enough to handle cases where a regex might inadvertently cause a prompt to include itself or create a loop. The expansion should be halted, and an error reported.

### 5.3. Frontend (Prompt Editor - `prompt_editor.html`)

1.  **Autocomplete Trigger:** Autocomplete is triggered by typing `[[`.
2.  **Live Regex Preview in Autocomplete:**
    *   As the user types a pattern within `[[...` that could be a regex (e.g., contains `.` or `*`), the autocomplete suggestion list will dynamically update.
    *   The first item in the suggestion list will be the regex pattern itself as typed by the user (e.g., `feature.*`). This item will be visually distinct (e.g., normal white background).
    *   Subsequent items in the list will be the actual prompt IDs that currently match the typed regex. These items will be visually distinct from the regex pattern and normal prompt suggestions (e.g., light gray background, possibly indented).
    *   This provides immediate feedback on the regex's scope.
3.  **Autocomplete Selection:**
    *   If the user selects the regex pattern itself (e.g., `feature.*`) from the autocomplete list, the literal text `[[feature.*]]` is inserted into the editor.
    *   If the user selects a specific matched prompt ID (e.g., `feature:login-page`) from the grayed-out list, the text for a direct embed, `[[feature:login-page]]`, is inserted.
4.  **Expanded Content View:** The "Expanded Content" tab will display the result of the dynamic regex expansion, showing all concatenated and expanded prompts.

## 6. Impacted System Components

*   **PromptService / Expansion Logic:** Core changes to handle regex matching, sorting, and recursive expansion of multiple prompts.
*   **WebSocket Service:** If real-time updates of expanded view are maintained, this will need to trigger re-expansion on prompt changes that might affect regex results.
*   **Prompt Editor (`prompt_editor.html`):** Significant updates to the CodeMirror hint/autocomplete functionality.
*   **API:** Potentially new endpoints or modifications to existing ones if specific regex validation or testing tools are desired.
*   **Dependency Tracking:** The "Dependencies" and "Referenced By" views will need to be enhanced:
    *   A prompt containing `[[feature.*]]` will have dynamic dependencies on all prompts matching the regex.
    *   A prompt like `feature:login` might be referenced by another prompt directly (`[[feature:login]]`) or indirectly via a regex (`[[feature.*]]`). Both types of references should ideally be discoverable.

## 7. Potential Concerns and Challenges

*   **Performance:** Expanding prompts with broad regexes (`[[.*]]`) or those matching many other complex prompts could be resource-intensive. Caching strategies and efficient regex matching will be important. This might be deferred until identified as a real-world issue.
*   **Complexity:** Adds a new layer of abstraction and complexity to the prompt embedding mechanism.
*   **Distinguishing Regex from Literal ID:** If a prompt ID legitimately contains characters used in regex syntax (e.g., `my.prompt*v2`), a clear rule or an explicit syntax (e.g., `[[regex:pattern]]` vs `[[literal:pattern]]`) might be needed if simple `[[pattern]]` proves ambiguous. The preference is to keep it simple if possible.
*   **UI/UX for Regex Authoring:** While the live preview helps, users will need some understanding of regex syntax.

## 8. Future Considerations (Optional)

*   **Regex Testing Tool:** A dedicated UI section to test regex patterns against the current prompt list.
*   **Configurable Separator:** Allow users to define the separator between expanded regex-matched prompts (defaulting to newline).
*   **Limit on Matched Prompts:** A safety limit on the number of prompts a single regex can expand to prevent accidental denial-of-service.
