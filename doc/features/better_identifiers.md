# Feature: Better Identifiers

**Date:** May 31, 2025  
**Status:** Planning  
**Priority:** High  
**Branch:** `feature/better-identifiers`

## Problem Statement

The current unique identifier system for prompts creates collisions and confusion:

1. **Current ID Schema**: Uses `directory_name/filename` (e.g., `prompts/restart`)
2. **Collision Problem**: Multiple projects with same structure create identical IDs:
   - `projectA/prompts/restart` → `prompts/restart`
   - `projectB/prompts/restart` → `prompts/restart`
   - `projectC/prompts/restart` → `prompts/restart`
3. **User Confusion**: Display shows duplicate "IDs" making selection ambiguous

## Solution Requirements

### 1. Full Path as Unique ID
- Use the **complete file path** as accessed by the user
- Examples:
  - `/home/jem/development/projectA/prompts/restart`
  - `/home/jem/development/projectB/prompts/restart`
  - `/home/jem/development/projectC/prompts/restart`
- **Important**: Use the path as the user accesses it, NOT the realpath

### 2. Smart Display Names
Calculate the shortest unique display name using this priority:
1. **Filename only** (if unique across all prompts)
2. **First unique directory element + filename** (e.g., `projectA:restart`)
3. **Unique directory combination + filename** (e.g., `dev:projectA:restart`)

### 3. Display Name Examples
Given these files:
```
/home/jem/development/projectA/doc/restart
/home/jem/development/projectA/prompts/cats  
/home/jem/development/projectA/prompts/restart
/home/jem/development/projectB/prompts/restart
/home/jem/development/projectC/prompts/restart
```

Display names would be:
- `doc:restart` (unique at directory level)
- `cats` (filename is globally unique)
- `projectA:restart` (needs project level for uniqueness)
- `projectB:restart` (needs project level for uniqueness)  
- `projectC:restart` (needs project level for uniqueness)

## User Experience Goals

- **Tab Completion**: Show smart display names for easy selection
- **Clarity**: No ambiguous duplicate names in listings
- **Efficiency**: Shortest possible unique identifiers
- **Consistency**: Same display logic across all UI components

## Technical Impact

- **Data Model**: Change ID field to store full paths
- **API Layer**: Update all endpoints to handle full path IDs
- **UI Layer**: Update display logic and tab completion
- **Testing**: Comprehensive test updates for new schema
- **Migration**: Backward compatibility during transition
