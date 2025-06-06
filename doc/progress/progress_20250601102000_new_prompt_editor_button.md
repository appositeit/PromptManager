# Progress: New Prompt Button in Prompt Editor

**Date:** Sunday, June 1, 2025  
**Time:** 10:20 +1100 (Sydney)  
**Status:** 🔄 **IN PROGRESS** - Adding New Prompt button to Prompt Editor  
**Branch:** `feature/new-prompt-editor-button`

## 🎯 Mission Summary: Add New Prompt Button and Enhanced Modal to Prompt Editor

Adding a New Prompt button to the prompt editor page header, exactly like the one on the home page. The requirements are:

1. **New Prompt Button**: Add button to prompt editor header with Alt+N shortcut
2. **Enhanced Modal**: Modify existing New Prompt dialog to include:
   - "Create in new tab" button with Ctrl+Shift+Enter shortcut
   - Default Directory field to current directory
   - Hover text on all buttons/fields showing keyboard shortcuts
3. **Reuse Existing**: Must reuse the existing new prompt dialog, not recreate it
4. **Optional Functions**: Enable certain functions only when on Prompt Editor page

## 📋 Implementation Plan

### Phase 1: Analysis
- ✅ Review current New Prompt modal in `manage_prompts.html`
- ✅ Review prompt editor structure in `prompt_editor.html`
- ✅ Understand current modal functionality and keyboard shortcuts

### Phase 2: Extract and Modularize New Prompt Modal
- [ ] Extract New Prompt modal HTML to a reusable template/macro
- [ ] Extract New Prompt JavaScript functions to shared utility
- [ ] Update `manage_prompts.html` to use modularized components

### Phase 3: Add New Prompt Button to Prompt Editor
- [ ] Add New Prompt button to prompt editor header
- [ ] Add Alt+N keyboard shortcut for prompt editor
- [ ] Include the modularized New Prompt modal in prompt editor

### Phase 4: Enhance Modal with Required Features
- [ ] Add "Create in new tab" button with Ctrl+Shift+Enter shortcut
- [ ] Default Directory field to current directory when in prompt editor
- [ ] Add hover text/tooltips showing keyboard shortcuts on all buttons and fields

### Phase 5: Testing and Documentation
- [ ] Test all functionality on both manage_prompts and prompt_editor pages
- [ ] Verify keyboard shortcuts work correctly
- [ ] Update help documentation
- [ ] Create progress completion document

## 🔍 Current Analysis

### Existing New Prompt Modal Features
- Modal ID: `newPromptModal`
- Form ID: `newPromptForm`
- Key functions: `createPrompt()`, `populateDirectorySelect()`, `updateIdPreview()`
- Fields: Prompt Name, Directory, Generated ID, Display Name Preview, Description, Tags
- Current shortcuts: Alt+N (manage_prompts only)

### Prompt Editor Current Structure
- Header has: Back, Copy, Toggle View, Search/Replace, Rename, Save, Delete buttons
- Uses `{% block header_actions %}` structure
- Current shortcuts: Alt+S, Alt+C, Alt+T, Alt+R, Alt+B, Alt+M, Alt+Shift+C

### Requirements Analysis
1. **New Button**: Should fit naturally in header actions group
2. **Current Directory**: Need to extract directory from current prompt's metadata
3. **New Tab Creation**: Will need window.open() or target="_blank" functionality
4. **Keyboard Shortcuts**: Comprehensive tooltip system needed

---

**Status: IN PROGRESS** 🔄  
**Next**: Begin Phase 2 - Extract and modularize New Prompt modal components
