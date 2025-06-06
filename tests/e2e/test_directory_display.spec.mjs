import { test, expect } from '@playwright/test';

test.describe('Prompt Editor Directory Display', () => {
  test('should display full directory path in metadata box', async ({ page, request }) => {
    const uniqueTestPromptId = `e2e-directory-display-test-${Date.now()}`;
    const testContent = "Content for directory display test: " + uniqueTestPromptId;
    
    // Get a valid directory to create the prompt in
    const dirsResponse = await request.get('/api/prompts/directories/all');
    expect(dirsResponse.ok(), "Failed to fetch directories").toBeTruthy();
    const configuredDirectories = await dirsResponse.json();
    const enabledDirectories = configuredDirectories.filter(d => d.enabled);
    expect(enabledDirectories.length).toBeGreaterThan(0, "No enabled directories found to create prompt in");
    
    // Select a directory that has a multi-part path (subdirectories) if available, 
    // otherwise use any enabled directory
    let targetDirectory = enabledDirectories.find(d => d.path && d.path.includes('/')) || enabledDirectories[0];
    const targetDirectoryPath = targetDirectory.path;
    
    console.log(`[Test Log] Using directory: ${targetDirectoryPath}`);
    console.log(`[Test Log] Directory info:`, targetDirectory);

    // 1. Create the test prompt via API
    const createResponse = await request.post('/api/prompts/', {
      data: {
        id: uniqueTestPromptId,
        content: testContent,
        directory: targetDirectoryPath, 
        description: 'E2E test prompt for directory display validation',
        tags: ['e2e', 'directory-test']
      }
    });
    
    if (!createResponse.ok()) {
        console.error("Failed to create prompt:", await createResponse.text());
    }
    expect(createResponse.ok(), `Failed to create prompt. Status: ${createResponse.status()}`).toBeTruthy();
    console.log(`[Test Log] Created prompt: ${uniqueTestPromptId} in directory ${targetDirectoryPath}`);

    // 2. Navigate to the prompt editor
    await page.goto('/');
    await expect(page.locator('#prompts-table-body tr:has-text("Loading prompts...")')).not.toBeVisible({timeout: 15000});
    
    const promptRowLocator = page.locator(`#prompts-table-body tr[data-prompt-id="${targetDirectoryPath}/${uniqueTestPromptId}"]`);
    await expect(promptRowLocator).toBeVisible({ timeout: 15000 });
    
    const nameLink = promptRowLocator.locator('td a').filter({ hasText: uniqueTestPromptId });
    await nameLink.click();

    // 3. Wait for the editor to load
    await expect(page.locator('#editor .CodeMirror-code')).toBeVisible({ timeout: 10000 });

    // 4. Locate the directory display element in the metadata box
    const directoryDisplayElement = page.locator('#prompt-directory');
    await expect(directoryDisplayElement).toBeVisible({ timeout: 5000 });

    // 5. Get the displayed directory text
    const displayedDirectory = await directoryDisplayElement.textContent();
    console.log(`[Test Log] Displayed directory: "${displayedDirectory}"`);
    console.log(`[Test Log] Expected full path: "${targetDirectoryPath}"`);

    // 6. Validate that the full directory path is displayed
    // The requirement is that the FULL directory path should be shown, not just the last part
    expect(displayedDirectory).toBe(targetDirectoryPath, 
      `Expected full directory path "${targetDirectoryPath}" but got "${displayedDirectory}"`);

    // 7. Additional validation: check tooltip contains the same full path
    const directoryTitle = await directoryDisplayElement.getAttribute('title');
    console.log(`[Test Log] Directory tooltip: "${directoryTitle}"`);
    
    // The title/tooltip should also contain the full path
    if (directoryTitle) {
      expect(directoryTitle).toBe(targetDirectoryPath, 
        `Expected tooltip to show full path "${targetDirectoryPath}" but got "${directoryTitle}"`);
    }

    // 8. Verify via API that the prompt data structure contains the expected directory info
    const apiGetResponse = await request.get(`/api/prompts/${uniqueTestPromptId}?directory=${encodeURIComponent(targetDirectoryPath)}`);
    expect(apiGetResponse.ok(), `Failed to GET prompt via API. Status: ${apiGetResponse.status()}`).toBeTruthy();
    const promptDataFromApi = await apiGetResponse.json();
    
    console.log(`[Test Log] API prompt data directory field: "${promptDataFromApi.directory}"`);
    console.log(`[Test Log] API prompt data directory_info:`, promptDataFromApi.directory_info);
    
    // The API should return the full directory path
    expect(promptDataFromApi.directory).toBe(targetDirectoryPath);
    
    // 9. Cleanup: Delete the created prompt
    const deleteResponse = await request.delete(`/api/prompts/${uniqueTestPromptId}?directory=${encodeURIComponent(targetDirectoryPath)}`);
    if (!deleteResponse.ok()) {
        console.error("Failed to delete prompt:", await deleteResponse.text());
    }
    expect(deleteResponse.ok(), `Failed to delete prompt. Status: ${deleteResponse.status()}`).toBeTruthy();
    console.log(`[Test Log] Deleted prompt: ${uniqueTestPromptId}`);
  });

  test('should show short directory name vs full path behavior', async ({ page, request }) => {
    // This test documents the current vs expected behavior for directory display
    const uniqueTestPromptId = `e2e-directory-comparison-test-${Date.now()}`;
    const testContent = "Content for directory comparison test: " + uniqueTestPromptId;
    
    // Get directories to test different path scenarios
    const dirsResponse = await request.get('/api/prompts/directories/all');
    expect(dirsResponse.ok(), "Failed to fetch directories").toBeTruthy();
    const configuredDirectories = await dirsResponse.json();
    const enabledDirectories = configuredDirectories.filter(d => d.enabled);
    expect(enabledDirectories.length).toBeGreaterThan(0, "No enabled directories found");
    
    // Create a prompt in the first available directory
    const targetDirectory = enabledDirectories[0];
    const targetDirectoryPath = targetDirectory.path;
    
    console.log(`[Test Log] Testing with directory: ${targetDirectoryPath}`);
    console.log(`[Test Log] Directory has name: "${targetDirectory.name}"`);
    console.log(`[Test Log] Directory has path: "${targetDirectory.path}"`);

    // Create the test prompt
    const createResponse = await request.post('/api/prompts/', {
      data: {
        id: uniqueTestPromptId,
        content: testContent,
        directory: targetDirectoryPath, 
        description: 'Test prompt for directory display comparison',
        tags: ['e2e', 'directory-comparison']
      }
    });
    expect(createResponse.ok()).toBeTruthy();

    // Navigate to the prompt editor
    await page.goto('/');
    await expect(page.locator('#prompts-table-body tr:has-text("Loading prompts...")')).not.toBeVisible({timeout: 15000});
    
    const promptRowLocator = page.locator(`#prompts-table-body tr[data-prompt-id="${targetDirectoryPath}/${uniqueTestPromptId}"]`);
    await expect(promptRowLocator).toBeVisible({ timeout: 15000 });
    
    const nameLink = promptRowLocator.locator('td a').filter({ hasText: uniqueTestPromptId });
    await nameLink.click();
    await expect(page.locator('#editor .CodeMirror-code')).toBeVisible({ timeout: 10000 });

    // Get what's currently displayed
    const directoryDisplayElement = page.locator('#prompt-directory');
    const displayedDirectory = await directoryDisplayElement.textContent();
    const directoryTooltip = await directoryDisplayElement.getAttribute('title');
    
    console.log(`[Test Comparison] Currently displayed: "${displayedDirectory}"`);
    console.log(`[Test Comparison] Tooltip shows: "${directoryTooltip}"`);
    console.log(`[Test Comparison] Full path should be: "${targetDirectoryPath}"`);
    console.log(`[Test Comparison] Directory name is: "${targetDirectory.name}"`);
    
    // Document the behavior: if the displayed text is different from the full path,
    // it indicates the bug where only the short name is shown
    if (displayedDirectory !== targetDirectoryPath) {
      console.log(`[Test Finding] BUG CONFIRMED: Directory display shows "${displayedDirectory}" instead of full path "${targetDirectoryPath}"`);
      console.log(`[Test Finding] This confirms that only the directory name/short name is displayed instead of the full path`);
    } else {
      console.log(`[Test Finding] Directory display correctly shows full path`);
    }

    // Cleanup
    const deleteResponse = await request.delete(`/api/prompts/${uniqueTestPromptId}?directory=${encodeURIComponent(targetDirectoryPath)}`);
    expect(deleteResponse.ok()).toBeTruthy();
    console.log(`[Test Log] Deleted comparison test prompt: ${uniqueTestPromptId}`);
  });
});
