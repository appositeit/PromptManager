# Playwright E2E Testing Workflow

This document outlines the workflows for End-to-End (E2E) testing using Playwright in the Prompt Manager project, including trace recording, AI-assisted test generation, and best practices.

## 1. Recording Playwright Traces for Test Generation

Playwright traces are invaluable for understanding user interactions and for generating E2E tests, especially with AI assistance. A trace captures a recording of a test run, including DOM snapshots, actions, console logs, and network requests.

**How to Record a Trace Manually:**

1.  **Ensure your local development server is running.** (e.g., `python src/server.py` or your project's run command, typically on `http://localhost:8081`).

2.  **Use the Playwright Inspector with trace saving:**
    Open your terminal and run the following command:

    ```bash
    npx playwright open --save-trace prompts_flow_trace.zip http://localhost:8081
    ```

    -   `npx playwright open`: Starts the Playwright Inspector, which allows you to interact with the browser and record actions.
    -   `--save-trace <trace_file_name>.zip`: Specifies the file where the trace will be saved. Use a descriptive name for the trace file (e.g., `create_new_prompt_trace.zip`, `edit_existing_prompt_trace.zip`).
    -   `<URL>`: The URL to start the recording from (e.g., `http://localhost:8081/manage/prompts`).

3.  **Perform the User Flow:**
    -   The Playwright Inspector will open a browser window.
    -   Manually click through the user flow you want to test. Interact with the application as a user would.
    -   The Inspector will record your actions.

4.  **Stop Recording & Save Trace:**
    -   Once you have completed the user flow, close the browser window that Playwright Inspector opened.
    -   The trace file (e.g., `prompts_flow_trace.zip`) will be saved in your current directory.

**Tips for Effective Trace Recording:**

*   **Focus on a Single, Coherent Flow:** Each trace should ideally cover one specific user story or feature interaction.
*   **Be Deliberate:** Click and type as a typical user would, but avoid overly rapid or erratic movements that might not translate well to a test.
*   **Note Key Assertions:** As you go through the flow, mentally (or physically) note the expected outcomes or states of the UI at each major step. This will be helpful for AI test generation or manual test writing.
*   **Convention for Trace Files:** 
    *   Store raw trace `.zip` files in a dedicated directory: `tests/e2e/traces/`.
    *   This directory should be added to `.gitignore` as traces are typically large and temporary.

## 2. AI-Assisted Test Generation from Traces

Once a Playwright trace (`.zip` file) has been recorded, it can be provided to an AI assistant to help generate an E2E test script. Below is a template prompt that can be used or adapted for this purpose.

**Example AI Prompt for Trace-to-Test Conversion:**

```text
You're a developer assistant. Convert the following Playwright trace into a fully working E2E test.

## Context:
The trace was captured during a manual walkthrough of a core user flow in the Prompt Manager application. The goal is to create a test that simulates the same user actions and asserts the expected outcomes.

## Instructions:
- Use `@playwright/test` syntax (TypeScript).
- Use explicit selectors (`data-testid`, `aria-label`, or `text=`), avoid auto-generated XPaths.
- Add `await expect()` assertions at each major step (e.g. page load, modal open, submission).
- If something failed in the trace, infer the fix (e.g. add `await page.waitForSelector(...)`).
- Keep the test file organized: setup, actions, assertions.
- At the end, include a summary comment of what the test validates.

## Trace File:
<insert path to trace.zip file or describe how it will be provided>

## Additional Hints (Optional - tailor to the specific trace):
- Example Hint: The user logs in with test credentials (`user@example.com`, `password123`).
- Example Hint: They navigate to `/prompts`, click "New Prompt", fill out a title, select a model, and submit.
- Example Hint: After submission, the prompt appears in the list and a toast notification confirms success.

Write a test file named `example-flow.spec.ts` that captures this behavior.
```

**Process:**

1.  Replace `<insert path to trace.zip file...>` with the actual path or a note on how the AI will access the trace.
2.  Tailor the "Additional Hints" section based on the specific flow captured in the trace.
3.  Provide this prompt to the AI assistant.
4.  Review and refine the generated Playwright test script (`.spec.ts` or `.spec.js`). Ensure it meets quality standards, uses correct selectors, and has appropriate assertions.
5.  Save the validated test script in the `tests/e2e/` directory (e.g., `tests/e2e/my-new-feature.spec.js`). Consider a subdirectory like `tests/e2e/generated/` for initial AI output before it's cleaned up and moved to the main `tests/e2e/` folder.

**Convention for Storing Traces and Generated Tests:**

-   **Traces:** 
    -   Location: `tests/e2e/traces/`
    -   Naming: Use descriptive names, e.g., `feature-x-user-flow-y_YYYYMMDD.zip`.
    -   Git: Add `tests/e2e/traces/` to `.gitignore`.
-   **Generated Tests (Initial AI Output):**
    -   Location: `tests/e2e/generated/` (optional, for review before final placement)
    -   Naming: Correlate with the trace file, e.g., `feature-x-user-flow-y.spec.js`.
    -   Git: This directory can also be in `.gitignore` if only used for temporary AI output.
-   **Final E2E Tests:**
    -   Location: `tests/e2e/`
    -   Naming: Clear, descriptive names, e.g., `prompt-creation.spec.js`, `manage-directories.spec.js`.
    -   Git: Version controlled.

## 3. Canonical Test Examples

*(This section will list or link to manually curated E2E tests that serve as best-practice examples.)*

## 4. AI-Driven Test Scaffolding for New Routes

To accelerate the creation of baseline E2E test coverage for new frontend routes, AI can be used to generate test scaffolds. These scaffolds ensure basic rendering and navigation are quickly covered.

**Process for Generating Test Scaffolds:**

1.  **Developer Action:** When a new frontend route is created (e.g., `/admin/users`, `/reports/summary`), the developer should identify:
    *   The exact route path.
    *   The expected page title or a key part of it.
    *   2-3 stable, key UI elements that should always be present on the page (e.g., a main heading, a primary form, a critical button).
2.  **AI Interaction:** The developer provides this information to an AI assistant using a prompt similar to the template below.
3.  **AI Output:** The AI generates a basic Playwright test script (`.spec.js` or `.spec.ts`).
4.  **Developer Review & Integration:** The developer reviews the scaffold, adjusts selectors if immediately possible (preferring `data-testid` if available, otherwise using robust text or ARIA labels), and integrates it into the `tests/e2e/` directory.

**Example AI Prompt for Test Scaffolding:**

```text
You're a developer assistant. Generate a basic Playwright test scaffold for a new frontend route in the Prompt Manager application.

## Route Information:
- **Route Path:** <Insert New Route Path, e.g., /settings/profile>
- **Page Title Hint:** <Expected page title or key phrase, e.g., "User Profile Settings">
- **Key Elements Present:** <List 2-3 key elements and their expected text or type, e.g., "Main heading with text 'User Profile'; An input field for email; A button with text 'Save Profile'">

## Instructions:
- Use `@playwright/test` syntax (JavaScript is preferred for this project unless specified otherwise).
- The test file should be named descriptively based on the route (e.g., `settings-profile-page.spec.js`).
- The test should:
    1. Navigate to the specified route path using `page.goto()`.
    2. Assert that the page title is relevant to the route (e.g., contains the Page Title Hint) using `await expect(page).toHaveTitle(...)`.
    3. For each key element listed:
        a. Locate the element. Prioritize text-based selectors, then ARIA roles/labels, then basic HTML tags if necessary. Avoid overly specific CSS class-based selectors for these scaffolds unless they are highly stable.
        b. Assert that the element `toBeVisible()`.
    4. Include comments indicating where more specific selectors (like `data-testid="your-id"`) should be added by the developer once the UI is updated.
- Keep the test file organized with clear sections for setup (if any), actions (navigation), and assertions.
- At the end, include a summary comment of what the test scaffold validates at a high level.

Write a test file that implements this basic scaffold.
```

---
*This document is a living guide and will be updated as our E2E testing practices evolve.* 