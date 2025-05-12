# Progress Update: Removing Fragment Concept

## Intent
Remove the concept of "fragments" from the system completely, simplifying to just "prompts" that can be composed. This will:

1. Reduce conceptual complexity
2. Eliminate duplicate interfaces and code
3. Make the system more intuitive to use
4. Ensure all functionality works through a single consistent interface

## Approach
1. Archive fragment-specific files rather than deleting them
2. Route fragment endpoints to prompt endpoints
3. Update UI to remove references to fragments
4. Ensure inclusion functionality works with unified prompt approach
5. Test the system to verify functionality

The goal is to have a clean, single-concept system while maintaining all functionality.
