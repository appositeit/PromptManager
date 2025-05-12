# Code Duplication Analysis - May 15, 2025

## Overview

A thorough analysis of the prompt_manager codebase was conducted to identify duplicate code patterns and opportunities for refactoring. This document highlights key findings and recommendations for improving code reuse in accordance with the DRY (Don't Repeat Yourself) principle.

## Major Duplication Findings

### 1. JavaScript Toast Notification System

**Duplication Severity: High**

The `showToast()` function for displaying notifications is duplicated across multiple templates:
- `base.html`
- `fragment_editor.html`
- `manage_fragments.html`
- `manage_templates.html`
- `prompt_editor.html`
- `settings.html`
- `template_editor.html`

Each implementation has nearly identical logic for creating a toast container, adding toast elements, and showing notifications. This creates maintenance challenges as any update to the toast system requires changes to multiple files.

### 2. Stable Sort Implementation

**Duplication Severity: Medium**

The `stableSort()` function is duplicated in:
- `utils.js` (canonical implementation)
- `manage_fragments.html`
- `manage_prompts.html`
- `manage_templates.html`

This is a utility function that should be implemented once and reused across the application.

### 3. Python Service Classes

**Duplication Severity: High**

The `FragmentService` and `PromptService` classes share significant code duplication:

- Both implement nearly identical methods for:
  - Directory management (`add_directory()`)
  - Loading resources from files (`load_fragment()`/`load_prompt()`)
  - Saving resources to files (`save_fragment()`/`save_prompt()`)
  - Handling front matter extraction
  - Managing tags and metadata
  - Expanding inclusions (`expand_inclusions()`)

These services follow the same patterns but operate on different model types.

### 4. HTML Template Structure

**Duplication Severity: Medium**

The templates for managing prompts, fragments, and templates share similar structure and JavaScript implementations:
- Table rendering logic
- Sorting and filtering functionality
- Modal dialogs (creation, deletion)
- Event handling

## Recommendations

### 1. Consolidate JavaScript Utilities

**Solution:** Create a unified JavaScript utility module that's properly imported by all templates.

1. **Move all toast notification code to `utils.js`**:
   - Ensure every template imports utils.js
   - Remove individual toast implementations
   - Update `base.html` to include this utility by default

2. **Ensure consistent use of `stableSort()`**:
   - Remove duplicate implementations
   - Ensure proper function import in all templates

### 2. Create a Base Service Class

**Solution:** Implement a base service class for common functionality.

1. **Create `BaseResourceService` class**:
   ```python
   class BaseResourceService:
       """Base class for resource services (prompts, fragments, templates)."""
       
       def __init__(self, base_directories=None, auto_load=True):
           # Common initialization code
           
       def add_directory(self, path, name=None, description=None):
           # Common directory management
           
       # Additional shared methods
   ```

2. **Refactor existing services to inherit**:
   ```python
   class PromptService(BaseResourceService):
       # Prompt-specific functionality
   
   class FragmentService(BaseResourceService):
       # Fragment-specific functionality
   ```

### 3. Create Reusable Template Components

**Solution:** Implement template inheritance and components for common UI elements.

1. **Create macro files for common components**:
   - `_macros/table.html` for sortable tables
   - `_macros/modals.html` for standard dialog patterns
   - `_macros/toast.html` for notification components

2. **Use the macro system in templates**:
   ```html
   {% import "_macros/table.html" as table_macros %}
   
   {{ table_macros.sortable_table(headers, data, sort_options) }}
   ```

### 4. Shared Frontend Components System

**Solution:** Develop a proper frontend component architecture.

1. **Create modular JavaScript components**:
   - `/static/js/components/data-table.js`
   - `/static/js/components/toast-manager.js`
   - `/static/js/components/modal-dialog.js`

2. **Implement component registration system**:
   ```javascript
   // Component system
   const UIComponents = {
       register(name, component) {
           // Register component
       },
       init() {
           // Initialize all components on page
       }
   };
   ```

## Implementation Priority

1. **JavaScript Utility Consolidation**: Highest priority - quick wins with significant benefit
2. **Base Service Class**: High priority - reduces future maintenance burden
3. **Template Macro System**: Medium priority - improves consistency
4. **Component Architecture**: Lower priority - longer-term architectural improvement

## Benefits

1. **Reduced Maintenance Burden**: Changes need to be made in fewer places
2. **Consistency**: User interface and code behavior will be more consistent
3. **Testing Efficiency**: Fewer code paths to test
4. **Easier Onboarding**: New developers will find the codebase more organized and predictable
5. **Better Performance**: Can optimize shared code paths

## Next Steps

1. Create a branch for refactoring work
2. Implement JavaScript utility consolidation
3. Create proof-of-concept for base service class
4. Update documentation with new patterns
5. Implement incremental improvements for template system
