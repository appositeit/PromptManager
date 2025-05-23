const { test, expect } = require('@playwright/test');

test.describe('Prompt Dependencies and Referenced By', () => {
  test('referenced_and_embedded prompt shows correct dependencies and referenced by', async ({ page }) => {
    // Go directly to the prompt editor page for the test prompt
    await page.goto('http://localhost:8081/prompts/referenced_and_embedded');

    // Wait for the Dependencies card to load
    await expect(page.locator('div.card:has-text("Dependencies")')).toBeVisible();
    // Check that the dependency referencing_test is present as a link
    const dependenciesSection = page.locator('#dependencies');
    await expect(dependenciesSection).toContainText('referencing_test');
    await expect(dependenciesSection.locator('a', { hasText: 'referencing_test' })).toBeVisible();

    // Wait for the Referenced By card to load
    await expect(page.locator('div.card:has-text("Referenced By")')).toBeVisible();
    // Check that the referenced by embedding_test is present as a link
    const referencedBySection = page.locator('#referenced-by');
    // Wait for the referenced by section to finish loading
    await referencedBySection.waitFor({ state: 'visible' });
    await expect(referencedBySection).toContainText('embedding_test');
    await expect(referencedBySection.locator('a', { hasText: 'embedding_test' })).toBeVisible();
  });
}); 