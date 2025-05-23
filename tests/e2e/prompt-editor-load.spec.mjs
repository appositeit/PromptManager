import { test, expect } from '@playwright/test';

test.describe('Prompt Editor Basic Load', () => {
  const promptId = 'getting_started'; // Assuming this prompt exists

  test(`should navigate to editor for prompt '${promptId}' and see editor components`, async ({ page }) => {
    // Navigate to the prompt editor page
    await page.goto(`/prompts/${promptId}`);

    // Check that the page title contains the prompt ID
    await expect(page).toHaveTitle(new RegExp(promptId, 'i'));

    // Check for the editor container (CodeMirror or a similar identifiable element)
    // This uses a generic ID, which might need to be made more specific or use data-testid.
    const editorElement = page.locator('#editor'); // The div where CodeMirror is initialized
    await expect(editorElement).toBeVisible();

    // Check for the save button
    const saveButton = page.locator('button#save-btn:has-text("Save")');
    await expect(saveButton).toBeVisible();

    // Check for the metadata section (e.g., description input)
    const descriptionInput = page.locator('#prompt-description');
    await expect(descriptionInput).toBeVisible();
  });
});

/*
Summary of what this test validates:
- Successfully navigates to the prompt editor page for a specific prompt (e.g., 'getting_started').
- Verifies that the HTML title of the page contains the prompt ID.
- Verifies that the main editor element (e.g., CodeMirror container) is visible.
- Verifies that the "Save" button is visible.
- Verifies that the prompt description input field is visible.
*/ 