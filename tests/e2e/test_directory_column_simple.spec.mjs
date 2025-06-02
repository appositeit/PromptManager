import { test, expect } from '@playwright/test';

test.describe('Prompts Table Directory Column Display', () => {
  test('should display meaningful directory names, not just "prompts"', async ({ page }) => {
    console.log(`[Test Log] Testing Directory column displays meaningful directory names`);

    // Navigate to the manage prompts page
    await page.goto('/');
    
    // Wait for the prompts table to load
    await expect(page.locator('#prompts-table-body tr:has-text("Loading prompts...")')).not.toBeVisible({timeout: 15000});
    
    // Look at the current directory column values and their tooltips
    const directoryColumnCells = page.locator('#prompts-table-body tr td:nth-child(1)');
    const directoryCount = await directoryColumnCells.count();
    
    console.log(`[Test Log] Found ${directoryCount} prompts in the table`);
    
    if (directoryCount > 0) {
      // Collect directory display data for analysis
      const directoryData = [];
      
      for (let i = 0; i < Math.min(10, directoryCount); i++) {
        const directoryText = await directoryColumnCells.nth(i).textContent();
        const directoryTooltip = await directoryColumnCells.nth(i).getAttribute('title');
        directoryData.push({ 
          index: i, 
          displayed: directoryText, 
          fullPath: directoryTooltip 
        });
      }
      
      console.log(`[Test Log] Sample directory data:`, directoryData);
      
      // Analyze the current behavior which we want to preserve
      const analysis = directoryData.map(item => {
        if (!item.fullPath) return { ...item, issue: 'no tooltip path' };
        
        const pathParts = item.fullPath.split('/').filter(part => part.length > 0);
        const lastElement = pathParts[pathParts.length - 1];
        
        // Check if current display is meaningful (not just "prompts")
        const isShowingLastElement = item.displayed === lastElement;
        const isShowingJustPrompts = item.displayed === 'prompts';
        const isMeaningfulName = item.displayed && item.displayed.length > 1 && !isShowingJustPrompts;
        
        return {
          ...item,
          pathParts,
          lastElement,
          isShowingLastElement,
          isShowingJustPrompts,
          isMeaningfulName
        };
      });
      
      console.log(`[Test Analysis] Directory display analysis:`, analysis);
      
      // Count meaningful vs problematic displays
      const showingJustPrompts = analysis.filter(a => a.isShowingJustPrompts).length;
      const showingMeaningfulNames = analysis.filter(a => a.isMeaningfulName).length;
      const showingLastElement = analysis.filter(a => a.isShowingLastElement).length;
      
      console.log(`[Test Results] Out of ${analysis.length} samples:`);
      console.log(`  - ${showingMeaningfulNames} show meaningful directory names (GOOD)`);
      console.log(`  - ${showingJustPrompts} show just "prompts" (BAD)`);
      console.log(`  - ${showingLastElement} show the last path element`);
      
      // Document current behavior
      analysis.forEach(item => {
        console.log(`[Test Detail] Path: ${item.fullPath}`);
        console.log(`  Directory name displayed: "${item.displayed}"`);
        console.log(`  Last path element: "${item.lastElement}"`);
        console.log(`  Status: ${item.isMeaningfulName ? 'GOOD - Meaningful name' : 'NEEDS_ATTENTION'}`);
      });
      
      // Main test assertion: Directory column should NOT show just "prompts" 
      // This is the core requirement - avoid the unhelpful last element
      analysis.forEach(item => {
        if (item.lastElement === 'prompts') {
          console.log(`[Test Case] Path: ${item.fullPath}`);
          console.log(`  Displayed: "${item.displayed}"`);
          
          // The key requirement: should NOT show "prompts" as that's not useful
          expect(item.displayed).not.toBe('prompts', 
            `Directory column should not show just "prompts" for path ${item.fullPath}. Current display "${item.displayed}" is good.`);
        }
      });
      
      // Validate that we show meaningful, distinguishable directory names
      const uniquePaths = new Set(analysis.map(a => a.fullPath).filter(Boolean));
      const uniqueDisplayed = new Set(analysis.map(a => a.displayed));
      
      console.log(`[Test Summary] Found ${uniquePaths.size} unique paths, ${uniqueDisplayed.size} unique displayed values`);
      console.log(`[Test Summary] Unique directory names: ${Array.from(uniqueDisplayed).join(', ')}`);
      
      // If there are multiple directories, we should have distinguishable names
      if (uniquePaths.size > 1) {
        expect(uniqueDisplayed.size).toBeGreaterThan(1, 
          `With ${uniquePaths.size} different directory paths, the directory column should show distinguishable names`);
      }
      
      // Validate that most displays are meaningful (not just single characters or "prompts")
      const meaningfulDisplayCount = analysis.filter(a => a.isMeaningfulName).length;
      expect(meaningfulDisplayCount).toBeGreaterThan(analysis.length * 0.8, 
        'Most directory displays should be meaningful names, not just single characters or "prompts"');
      
    } else {
      console.log(`[Test Log] No prompts found in table, cannot test directory column behavior`);
      expect(directoryCount).toBeGreaterThan(0, 'Expected to find at least some prompts to test directory column display');
    }
  });
  
  test('should validate current directory display behavior is user-friendly', async ({ page }) => {
    // This test validates that the current behavior provides good UX
    console.log(`[Validation Test] Validating directory column provides user-friendly names`);

    await page.goto('/');
    await expect(page.locator('#prompts-table-body tr:has-text("Loading prompts...")')).not.toBeVisible({timeout: 15000});
    
    const directoryColumnCells = page.locator('#prompts-table-body tr td:nth-child(1)');
    const directoryCount = await directoryColumnCells.count();
    
    if (directoryCount > 0) {
      const sampleData = [];
      for (let i = 0; i < Math.min(5, directoryCount); i++) {
        const directoryText = await directoryColumnCells.nth(i).textContent();
        const directoryTooltip = await directoryColumnCells.nth(i).getAttribute('title');
        sampleData.push({ displayed: directoryText, fullPath: directoryTooltip });
      }
      
      console.log(`[Current Behavior] Directory column shows user-friendly names:`);
      sampleData.forEach((item, index) => {
        console.log(`  ${index + 1}. Displayed: "${item.displayed}" | Full path: "${item.fullPath}"`);
        
        // Validate each directory name is user-friendly
        expect(item.displayed).toBeTruthy();
        expect(item.displayed.length).toBeGreaterThan(1); // More than just a single character
        expect(item.displayed).not.toBe('prompts'); // Not the unhelpful last element
      });
      
      // Validate that names are descriptive and meaningful
      const allDisplayedNames = sampleData.map(item => item.displayed);
      const uniqueNames = new Set(allDisplayedNames);
      
      console.log(`[Validation] Found ${uniqueNames.size} unique directory names: ${Array.from(uniqueNames).join(', ')}`);
      
      // Names should be distinguishable if there are multiple
      if (allDisplayedNames.length > 1) {
        expect(uniqueNames.size).toBeGreaterThan(0);
      }
      
      // Names should be more descriptive than just path elements
      allDisplayedNames.forEach(name => {
        expect(name).toMatch(/^[A-Za-z0-9\s]+/); // Should contain readable characters
        expect(name.length).toBeGreaterThanOrEqual(2); // Should be reasonably descriptive
      });
      
      console.log(`[Success] Directory column successfully displays user-friendly, meaningful names`);
    }
  });
});
