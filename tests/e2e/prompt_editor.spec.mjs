import { test, expect } from '@playwright/test';

test.describe('Prompt Editor Page', () => {
  test('should load an existing prompt and display its content', async ({ page }) => {
    // 1. Navigate to the homepage
    await page.goto('/');

    // 2. Wait for prompts table to load
    const promptsTableBody = page.locator('#prompts-table-body');
    await expect(promptsTableBody.locator('tr:has-text("Loading prompts...")')).not.toBeVisible({ timeout: 15000 });
    
    const firstPromptRow = promptsTableBody.locator('tr.prompt-row').nth(0);
    await expect(firstPromptRow).toBeVisible({ timeout: 10000 }); 
    
    const promptCount = await promptsTableBody.locator('tr.prompt-row').count();
    expect(promptCount).toBeGreaterThan(0);

    // 3. Get the unique_id (for content verification) and display_id (for URL verification)
    const promptUniqueIdForContentCheck = await firstPromptRow.getAttribute('data-prompt-id');
    expect(promptUniqueIdForContentCheck).toBeTruthy(); 

    const nameLink = firstPromptRow.locator('td').nth(1).locator('a');
    const promptDisplayIdForUrl = await nameLink.textContent();
    expect(promptDisplayIdForUrl).toBeTruthy();

    // 4. Click the prompt name link to navigate
    await nameLink.click();

    // 5. Verify that the URL changes to the correct prompt editor URL (/prompts/{display_id})
    if (promptDisplayIdForUrl) {
        const escapedDisplayId = promptDisplayIdForUrl.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        await expect(page).toHaveURL(new RegExp(`.*\/prompts\/${escapedDisplayId}(\\?.*)?$`), { timeout: 10000 });
    } else {
        throw new Error("Prompt display ID for URL was not found.");
    }
    
    // 6. Verify that an element unique to the editor page is visible
    await expect(page.locator(`h3:has-text("${promptDisplayIdForUrl.trim()}")`)).toBeVisible({ timeout: 10000 });
    await expect(page.locator('#editor')).toBeVisible({ timeout: 10000 }); 

    // 7. Verify that the hidden #prompt-true-unique-id span matches the unique_id from manage_prompts page
    const displayedTrueUniqueId = await page.locator('#prompt-true-unique-id').textContent();
    expect(displayedTrueUniqueId).toBe(promptUniqueIdForContentCheck.trim());

    // 8. Verify the editor has some content (is not empty)
    // CodeMirror uses .CodeMirror-code for the lines container, and .CodeMirror-line for individual lines
    const editorLinesContainer = page.locator('#editor .CodeMirror-code'); 
    await expect(editorLinesContainer).toBeVisible({ timeout: 10000 });
    
    const lineCount = await editorLinesContainer.locator('.CodeMirror-line').count();
    expect(lineCount).toBeGreaterThan(0); // Check if there's at least one line

    console.log(`Successfully navigated to editor for prompt (URL ID: ${promptDisplayIdForUrl}, Unique ID: ${promptUniqueIdForContentCheck})`);
  });

  test('should create, edit, save, and delete prompt content', async ({ page, request }) => {
    const uniqueTestPromptId = `e2e-content-test-${Date.now()}`;
    const initialContent = "Original E2E Content for " + uniqueTestPromptId;
    const editedContent = "Edited E2E Content for " + uniqueTestPromptId;
    
    // Get a valid directory to create the prompt in
    const dirsResponse = await request.get('/api/prompts/directories/all');
    expect(dirsResponse.ok(), "Failed to fetch directories").toBeTruthy();
    const configuredDirectories = await dirsResponse.json();
    const enabledDirectories = configuredDirectories.filter(d => d.enabled);
    expect(enabledDirectories.length).toBeGreaterThan(0, "No enabled directories found to create prompt in");
    const targetDirectoryPath = enabledDirectories[0].path; // Use the path of the first enabled directory
    console.log(`[Test Log] Using directory for new prompt: ${targetDirectoryPath}`);

    // 1. Create the prompt via API
    const createResponse = await request.post('/api/prompts/', {
      data: {
        id: uniqueTestPromptId,
        content: initialContent,
        directory: targetDirectoryPath, 
        description: 'E2E test prompt for content editing',
        tags: ['e2e']
      }
    });
    if (!createResponse.ok()) {
        console.error("Failed to create prompt:", await createResponse.text());
    }
    expect(createResponse.ok(), `Failed to create prompt. Status: ${createResponse.status()}`).toBeTruthy();
    const createdPromptData = await createResponse.json();
    expect(createdPromptData.id).toBe(uniqueTestPromptId);
    console.log(`[Test Log] Created prompt: ${uniqueTestPromptId} in directory ${targetDirectoryPath}`);

    // 2. Navigate to homepage, find the new prompt, and open it
    await page.goto('/');
    await expect(page.locator('#prompts-table-body tr:has-text("Loading prompts...")')).not.toBeVisible({timeout: 15000});
    
    const newPromptRowLocator = page.locator(`#prompts-table-body tr[data-prompt-id="${targetDirectoryPath}/${uniqueTestPromptId}"]`);
    await expect(newPromptRowLocator).toBeVisible({ timeout: 15000 });
    
    const nameLink = newPromptRowLocator.locator('td a').filter({ hasText: uniqueTestPromptId });
    await nameLink.click();

    // 3. Verify initial content in editor
    await expect(page.locator('#editor .CodeMirror-code')).toBeVisible({ timeout: 10000 });
    const loadedInitialContent = await page.evaluate(() => document.querySelector('#editor .CodeMirror').CodeMirror.getValue());
    expect(loadedInitialContent).toBe(initialContent);
    console.log("[Test Log] Verified initial content in editor.");

    // 4. Set new content
    await page.evaluate((content) => {
      document.querySelector('#editor .CodeMirror').CodeMirror.setValue(content);
    }, editedContent);

    // 5. Click Save
    const saveButton = page.locator('#save-btn');
    await saveButton.click();
    await expect(saveButton).toContainText('Saved', { timeout: 10000 }); // Increased timeout for save
    await expect(saveButton).not.toContainText('Saving...', { timeout: 2000 });

    // 6. Verify content via API immediately after save
    const apiGetResponse = await request.get(`/api/prompts/${uniqueTestPromptId}?directory=${encodeURIComponent(targetDirectoryPath)}`);
    if (!apiGetResponse.ok()) {
        console.error("Failed to GET prompt after save:", await apiGetResponse.text());
    }
    expect(apiGetResponse.ok(), `Failed to GET prompt after save. Status: ${apiGetResponse.status()}`).toBeTruthy();
    const promptDataFromApi = await apiGetResponse.json();
    expect(promptDataFromApi.content).toBe(editedContent);
    console.log("[Test Log] API content immediately after save matches editedContent.");

    // 7. Reload page
    await page.reload();
    await expect(page.locator('#editor .CodeMirror-code')).toBeVisible({ timeout: 10000 });

    // 8. Verify editor shows edited content after reload
    const persistedContent = await page.evaluate(() => document.querySelector('#editor .CodeMirror').CodeMirror.getValue());
    expect(persistedContent).toBe(editedContent);
    console.log("[Test Log] Editor content after reload matches editedContent.");

    // 9. Delete the prompt via API (cleanup)
    const deleteResponse = await request.delete(`/api/prompts/${uniqueTestPromptId}?directory=${encodeURIComponent(targetDirectoryPath)}`);
    if (!deleteResponse.ok()) {
        console.error("Failed to delete prompt:", await deleteResponse.text());
    }
    expect(deleteResponse.ok(), `Failed to delete prompt. Status: ${deleteResponse.status()}`).toBeTruthy();
    console.log(`[Test Log] Deleted prompt: ${uniqueTestPromptId}`);
  });

  test('should edit and save prompt metadata (description and tags)', async ({ page, request }) => {
    const uniqueMetaTestPromptId = `e2e-meta-test-${Date.now()}`;
    const initialMetaContent = "Content for metadata test prompt: " + uniqueMetaTestPromptId;
    const initialDescription = "Initial E2E Description for " + uniqueMetaTestPromptId;
    const initialTagsString = "e2e,initial-meta-tag";

    // Get a valid directory to create the prompt in
    const dirsResponse = await request.get('/api/prompts/directories/all');
    expect(dirsResponse.ok(), "Failed to fetch directories for metadata test").toBeTruthy();
    const configuredDirectories = await dirsResponse.json();
    const enabledDirectories = configuredDirectories.filter(d => d.enabled);
    expect(enabledDirectories.length).toBeGreaterThan(0, "No enabled directories found for metadata test");
    const targetDirectoryPathMeta = enabledDirectories[0].path;
    console.log(`[Test Log] Using directory for metadata test prompt: ${targetDirectoryPathMeta}`);

    // Create prompt for this test
    const createMetaResponse = await request.post('/api/prompts/', {
      data: {
        id: uniqueMetaTestPromptId,
        content: initialMetaContent,
        directory: targetDirectoryPathMeta,
        description: initialDescription,
        tags: initialTagsString.split(',').map(t=>t.trim())
      }
    });
    if (!createMetaResponse.ok()) {
        console.error("Failed to create prompt for metadata test:", await createMetaResponse.text());
    }
    expect(createMetaResponse.ok(), `Failed to create prompt for metadata test. Status: ${createMetaResponse.status()}`).toBeTruthy();
    const createdMetaPromptData = await createMetaResponse.json();
    console.log(`[Test Log] Created prompt for metadata test: ${uniqueMetaTestPromptId} in dir ${targetDirectoryPathMeta}`);

    // Navigate to its editor page
    await page.goto('/');
    await expect(page.locator('#prompts-table-body tr:has-text("Loading prompts...")')).not.toBeVisible({timeout: 15000});
    const metaPromptRowLocator = page.locator(`#prompts-table-body tr[data-prompt-id="${targetDirectoryPathMeta}/${uniqueMetaTestPromptId}"]`);
    await expect(metaPromptRowLocator).toBeVisible({ timeout: 15000 });
    const metaNameLink = metaPromptRowLocator.locator('td a').filter({ hasText: uniqueMetaTestPromptId });
    await metaNameLink.click();
    await expect(page.locator('#editor .CodeMirror-code')).toBeVisible({ timeout: 10000 });

    const descriptionInput = page.locator('#prompt-description');
    const tagsInput = page.locator('#prompt-tags');
    const saveButton = page.locator('#save-btn');

    // Verify initial description and tags
    await expect(descriptionInput).toHaveValue(initialDescription, { timeout: 5000 });
    await expect(tagsInput).toHaveValue(initialTagsString, { timeout: 5000 });
    console.log("[Test Log] Verified initial metadata in editor.");

    // Define and set new metadata
    const appendedText = " -- Edited by Playwright";
    const newDescription = initialDescription + appendedText;
    const newTag = "e2e-meta-added";
    const newTags = `${initialTagsString}, ${newTag}`;

    await descriptionInput.fill(newDescription);
    await tagsInput.fill(newTags);

    // Click the Save button
    await saveButton.click();
    await expect(saveButton).toContainText('Saved', { timeout: 10000 });
    await expect(saveButton).not.toContainText('Saving...', { timeout: 2000 });
    
    // Verify API response after save
    const apiGetMetaResponse = await request.get(`/api/prompts/${uniqueMetaTestPromptId}?directory=${encodeURIComponent(targetDirectoryPathMeta)}`);
    expect(apiGetMetaResponse.ok(), `Failed to GET prompt after metadata save. Status: ${apiGetMetaResponse.status()}`).toBeTruthy();
    const metaPromptFromApi = await apiGetMetaResponse.json();
    expect(metaPromptFromApi.description).toBe(newDescription);
    expect(metaPromptFromApi.tags).toEqual(expect.arrayContaining(newTags.split(',').map(t => t.trim())));
    console.log("[Test Log] API metadata immediately after save matches new values.");

    // Reload the page
    await page.reload();
    await expect(page.locator('#editor .CodeMirror-code')).toBeVisible({ timeout: 10000 });
    await expect(descriptionInput).toBeVisible();
    await expect(tagsInput).toBeVisible();

    // Verify new metadata persisted
    await expect(descriptionInput).toHaveValue(newDescription, { timeout: 5000 });
    const persistedTagsValue = await tagsInput.inputValue();
    expect(persistedTagsValue).toContain(newTag); // Check new tag is present
    initialTagsString.split(',').forEach(tag => {
        if (tag.trim()) expect(persistedTagsValue).toContain(tag.trim());
    });
    console.log("[Test Log] Verified persisted new metadata after reload.");

    // Cleanup: Delete the created prompt
    const deleteMetaResponse = await request.delete(`/api/prompts/${uniqueMetaTestPromptId}?directory=${encodeURIComponent(targetDirectoryPathMeta)}`);
    expect(deleteMetaResponse.ok(), `Failed to delete metadata test prompt. Status: ${deleteMetaResponse.status()}`).toBeTruthy();
    console.log(`[Test Log] Deleted metadata test prompt: ${uniqueMetaTestPromptId}`);
  });
}); 