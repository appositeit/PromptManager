# Feature: Collapsible Sidebar with Prompt References

**Date:** 2025-06-01  
**Status:** Complete ✅

## Overview

Enhance the prompt editor's right sidebar to make all boxes collapsible and add a new prompt cross-reference box for better usability.

## Design Decisions

### 1. Collapsible Boxes
- All boxes in the right column should be collapsible using Bootstrap collapse functionality
- Default state: open (expanded)
- Use chevron icons to indicate collapse state
- Maintain state using sessionStorage for user convenience

### 2. Prompt Cross-Reference Box
- New collapsible box listing unique shortnames of other prompts in the same directory
- Sortable alphabetically for easy scanning
- Drag-and-drop functionality to insert `[[prompt_name]]` syntax into raw editor
- Visual feedback during drag operations

### 3. Drag-and-Drop Implementation
- Use HTML5 drag and drop API
- Only active when Raw Content tab is visible
- Insert at cursor position in CodeMirror editor
- Provide visual feedback (drag image, cursor changes)

## Technical Approach

### HTML Structure
- Use Bootstrap collapse components with data-bs-toggle
- Add unique IDs for each collapsible section
- Include chevron icons that rotate based on state

### JavaScript
- Event listeners for collapse state changes
- Drag start/end handlers for prompt references
- CodeMirror integration for cursor position insertion
- sessionStorage for state persistence

### CSS
- Smooth transitions for chevron rotation
- Drag feedback styling
- Consistent spacing and visual hierarchy

## Implementation Plan

1. Update HTML template with collapsible structure
2. Add CSS for visual enhancements
3. Implement JavaScript for drag-and-drop
4. Add API endpoint for directory prompt listing
5. Test functionality across browsers

## User Experience

- Users can collapse sections they don't need for a cleaner interface
- Quick access to other prompts in the directory
- Intuitive drag-and-drop for cross-referencing prompts
- Visual feedback throughout interactions
