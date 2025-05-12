# Progress Update: Removed PromptType References

## Change Description
Removed the legacy `PromptType` enum from the unified prompt model and references to it in the codebase. The system has evolved to use the `is_composite` property instead of an explicit prompt type field.

## Implementation
1. Removed the `PromptType` enum class from the unified prompt model:
   - Deleted the entire enum class from `/home/jem/development/prompt_manager/src/models/unified_prompt.py`
   - The system now fully relies on the `is_composite` property to determine if a prompt contains inclusions

2. Fixed a JavaScript error in the "Create New Prompt" functionality:
   - Removed a reference to the non-existent `promptType` element in the `createPrompt` function
   - This prevents the error: `Uncaught TypeError: Cannot read properties of null (reading 'value')`

## Background
The prompt system originally had different types of prompts (standard, composite, system, user), but has since simplified to just standard prompts and composite prompts. Instead of maintaining a separate field, the system now detects composites by checking for inclusion markers (`[[` and `]]`) in the content.

## Benefits
- Simplified codebase without redundant enumerated types
- Removed dead code paths that were using the old type system
- Fixed JavaScript errors when creating new prompts
- Made the code more maintainable by using a property-based approach instead of explicit types

## Files Modified
- `/home/jem/development/prompt_manager/src/models/unified_prompt.py`
- `/home/jem/development/prompt_manager/src/templates/manage_prompts.html`
