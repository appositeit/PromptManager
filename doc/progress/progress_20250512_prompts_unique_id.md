# Progress Update - 2025-05-12

## Fixed Prompt ID Collision Issue

We've identified and fixed a problem with prompts with the same ID from different directories. The issue was in how unique IDs are generated and used throughout the system.

### Problem

Multiple prompt files with the same name (e.g., restart.md) from different directories would cause collisions when loaded into the system. The last one loaded would overwrite the earlier ones because:

1. The `get_unique_id` method in the Prompt model was only using the directory *name* rather than the full path
2. The `get_prompt` method in the PromptService class didn't handle cases where multiple prompts had the same ID

### Solution

1. Updated the `get_unique_id` method to use more directory path information:
   - Now uses the last two parts of the directory path instead of just the last one
   - This ensures unique IDs like "prompt_manager_prompts_restart" and "sms_challenge_prompts_restart" 
   - Cleaned up any special characters that might cause issues

2. Updated the `get_prompt` method to handle multiple prompts with the same ID:
   - Added an optional directory parameter to narrow down the search
   - First tries to find by unique_id, then by simple ID
   - Logs a warning when multiple matching prompts are found

3. Added directory parameter to the API router:
   - Made the API more flexible by allowing directory specification
   - This allows disambiguating which prompt is requested

### Testing

We've tested the fix with Puppeteer and confirmed that:

1. Both prompt files show up in the prompts list page
2. Both prompt files can be accessed individually by their unique IDs
3. The metadata displays correctly for each prompt
4. The content loads properly for both prompts

### Future Enhancements

Consider further UI improvements to make it clearer when multiple prompts with the same ID exist and to help users navigate between them.

This fix ensures that all prompts in the system are properly loaded and accessible, regardless of whether they share the same ID with prompts in other directories.