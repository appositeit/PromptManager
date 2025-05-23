import { test, expect } from '@playwright/test';

test.describe('Homepage (Manage Prompts Page)', () => {
  test('should load prompts and directories successfully', async ({ page }) => {
    // 1. Navigate to the homepage
    await page.goto('/'); // Assuming /manage/prompts is the effective homepage via baseURL

    // 2. Wait for the main title to be visible (basic page load confirmation)
    await expect(page.locator('h3:has-text("Manage Prompts & Directories")')).toBeVisible();

    // 3. Wait for prompts table to load (spinner disappears, at least one data row appears)
    const promptsTableBody = page.locator('#prompts-table-body');
    await expect(promptsTableBody.locator('tr:has-text("Loading prompts...")')).not.toBeVisible({ timeout: 15000 });
    const promptRowCount = await promptsTableBody.locator('tr td:first-child').count();
    expect(promptRowCount).toBeGreaterThan(0);

    // 4. Wait for directories table to load (spinner disappears, at least one data row appears)
    const directoriesTableBody = page.locator('#directories-table-body');
    await expect(directoriesTableBody.locator('tr:has-text("Loading directories...")')).not.toBeVisible({ timeout: 15000 });
    const directoryRowCount = await directoriesTableBody.locator('tr td:first-child').count();
    expect(directoryRowCount).toBeGreaterThan(0);

    console.log('Prompts and directories tables appear to have loaded data.');
  });

  test('should navigate prompts table with arrow keys', async ({ page }) => {
    await page.goto('/');
    const promptsTableBody = page.locator('#prompts-table-body');
    await expect(promptsTableBody.locator('tr:has-text("Loading prompts...")')).not.toBeVisible({ timeout: 15000 });
    const initialPromptRowCount = await promptsTableBody.locator('tr td:first-child').count();
    expect(initialPromptRowCount).toBeGreaterThan(0);

    const firstRow = promptsTableBody.locator('tr').nth(0);
    const secondRow = promptsTableBody.locator('tr').nth(1);

    await page.locator('body').press('ArrowDown');
    await page.waitForTimeout(100); // Short wait for JS to apply class
    await expect(firstRow).toHaveClass(/selected/);

    if (initialPromptRowCount > 1) {
      await page.locator('body').press('ArrowDown');
      await page.waitForTimeout(100); // Short wait
      await expect(firstRow).not.toHaveClass(/selected/);
      await expect(secondRow).toHaveClass(/selected/);

      await page.locator('body').press('ArrowUp');
      await page.waitForTimeout(100); // Short wait
      await expect(secondRow).not.toHaveClass(/selected/);
      await expect(firstRow).toHaveClass(/selected/);
    } else {
      console.log('Skipping down/up arrow test for multiple rows as only one prompt found.');
    }
  });

  test('should filter prompts when typing in search', async ({ page }) => {
    await page.goto('/');
    const promptsTableBody = page.locator('#prompts-table-body');
    await expect(promptsTableBody.locator('tr:has-text("Loading prompts...")')).not.toBeVisible({ timeout: 15000 });
    
    const initialPromptCountForSearch = await promptsTableBody.locator('tr td:first-child').count();
    expect(initialPromptCountForSearch).toBeGreaterThan(0);
    
    const initialVisibleRowCount = await promptsTableBody.locator('tr:not(:has-text("No prompts found."))').count();
    if (initialVisibleRowCount === 0) {
        console.log("Skipping search test as no prompts are initially visible.");
        return;
    }

    const searchInput = page.locator('#prompt-search');
    const searchTerm = 'admin';

    await searchInput.fill(searchTerm);
    await page.waitForTimeout(500);

    const filteredVisibleRowCount = await promptsTableBody.locator('tr:not(:has-text("No prompts found."))').count();
    
    if (initialVisibleRowCount > 0 && filteredVisibleRowCount < initialVisibleRowCount) {
        console.log(`Search filtered rows from ${initialVisibleRowCount} to ${filteredVisibleRowCount}`);
    } else if (initialVisibleRowCount > 0 && filteredVisibleRowCount === initialVisibleRowCount) {
        console.log(`Search term '${searchTerm}' did not reduce row count, or all rows match.`);
    } else if (filteredVisibleRowCount === 0) {
        console.log(`Search term '${searchTerm}' resulted in no matching prompts.`);
    }
    expect(filteredVisibleRowCount).toBeLessThanOrEqual(initialVisibleRowCount);

    const rows = await promptsTableBody.locator('tr:not(:has-text("No prompts found."))').all();
    for (const row of rows) {
      const rowText = await row.textContent();
      expect(rowText.toLowerCase()).toContain(searchTerm.toLowerCase());
    }
  });

  // We will add more tests here for arrow key navigation and searching
}); 