import { test, expect } from '@playwright/test';

test.describe('Prompt Manager Navigation', () => {
  test('should navigate to manage prompts page and see title', async ({ page }) => {
    // Navigate to the manage prompts page
    await page.goto('/manage/prompts');

    // Check that the page title is correct
    await expect(page).toHaveTitle(/Prompt Manager/);

    // Check for a heading with the text "Prompt Manager"
    // This assumes a visible h1, h2, or similar element with this text.
    // We can refine this with more specific selectors like data-testid later.
    await expect(page.locator('h1')).toContainText('Prompt Manager');
  });
});

/*
Summary of what this test validates:
- Successfully navigates to the /manage/prompts page.
- Verifies that the HTML title of the page contains "Prompt Manager".
- Verifies that a visible heading (h1 or h2) with the text "Prompt Manager" exists on the page.
*/ 