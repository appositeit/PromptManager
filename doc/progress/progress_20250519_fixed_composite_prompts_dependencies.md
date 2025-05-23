# Progress: Fixed Composite Prompts and Dependencies Functionality

## Issues Fixed

### 1. Missing `expand_prompt_content` Method

The "Expanded Content" view in the prompt editor was failing with a 500 Internal Server Error, because the PromptService class was missing the `expand_prompt_content` method that was expected by the API endpoint:

```
AttributeError: 'PromptService' object has no attribute 'expand_prompt_content'
```

### 2. Missing `find_prompts_by_inclusion` Method

Unit tests for composite prompt handling were failing with an error due to another missing method:

```
FAILED tests/unit/test_composite_handling.py::TestPromptServiceComposites::test_find_prompts_by_inclusion - AttributeError: 'PromptService' object has no attribute 'find_prompts_by_inclusion'
```

## Root Cause

Both issues stemmed from missing method implementations in the PromptService class. The class had an `expand_inclusions` method that provided the core functionality for expanding prompt references, but there were no dedicated methods for the specific API endpoints and functionality required by the UI and tests.

## Fixes Implemented

### 1. Added `expand_prompt_content` Method

```python
def expand_prompt_content(self, prompt_id: str) -> Tuple[str, List[str], List[str]]:
    """
    Expand a prompt's content by recursively including all dependencies.
    
    Args:
        prompt_id: The unique ID of the prompt to expand
        
    Returns:
        Tuple of (expanded_content, dependencies_list, warnings_list)
    """
    logger.debug(f"Expanding prompt content for: {prompt_id}")
    prompt = self.prompts.get(prompt_id)
    if not prompt:
        raise ValueError(f"Prompt not found: {prompt_id}")
        
    # Use the existing expand_inclusions method
    expanded_content, dependencies_set, warnings_list = self.expand_inclusions(
        content=prompt.content,
        inclusions=set(),  # Start with an empty set
        parent_id=prompt_id
    )
    
    # Convert the dependencies set to a list for the API response
    dependencies_list = list(dependencies_set)
    
    return expanded_content, dependencies_list, warnings_list
```

This serves as a bridge between the API endpoint and the existing `expand_inclusions` functionality, making it available to the frontend.

### 2. Added `find_prompts_by_inclusion` Method

```python
def find_prompts_by_inclusion(self, prompt_id: str) -> List[Prompt]:
    """
    Find all prompts that include (directly or indirectly) a specific prompt.
    
    Args:
        prompt_id: The ID of the prompt to search for as an inclusion.
        
    Returns:
        A list of Prompt objects that include the specified prompt.
    """
    logger.debug(f"Finding prompts that include '{prompt_id}' (directly or indirectly)")
    result = []
    
    # Normalize prompt ID to handle extensions
    normalized_target_id = prompt_id
    if normalized_target_id.endswith('.md'):
        normalized_target_id = normalized_target_id[:-3]
        
    # First check if the target prompt exists
    if not self.get_prompt(normalized_target_id):
        logger.warning(f"Target prompt '{normalized_target_id}' not found. Cannot find prompts including it.")
        return []
        
    # For each prompt, check if it includes the target
    for prompt in self.prompts.values():
        if prompt.id == normalized_target_id:
            continue  # Skip the target itself
            
        if prompt.is_composite:
            # Get all transitive dependencies through expand_inclusions
            _, transitive_dependencies, _ = self.expand_inclusions(
                prompt.content,
                parent_id=prompt.id
            )
            
            if normalized_target_id in transitive_dependencies:
                result.append(prompt)
                
    logger.debug(f"Found {len(result)} prompts including '{normalized_target_id}'")
    return result
```

This method helps identify which prompts depend on (include) a specific prompt, which is useful for the UI to show dependencies between prompts.

## Results

- The "Expanded Content" view in the prompt editor now works correctly
- The unit tests for composite prompt handling are now passing
- Users can view prompts with all inclusions expanded

## Test Results

- All unit tests are now passing, including the previously failing `test_find_prompts_by_inclusion`
- The integration tests related to WebSockets still have some issues, but those are unrelated to the fixes we implemented

## Next Steps

- Consider adding a specific endpoint that uses the `find_prompts_by_inclusion` method to display prompt dependencies in the UI
- Review other potential functionality gaps where implementation might be missing
- Add more comprehensive unit tests for these and related functions to prevent regression
- Investigate and fix the WebSocket integration test issues separately 