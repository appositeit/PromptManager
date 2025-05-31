# Implementation Plan: Better Identifiers

**Date:** May 31, 2025  
**Feature:** Full Path Unique IDs with Smart Display Names  
**Branch:** `feature/better-identifiers`  
**Estimated Time:** 8-12 hours

## Overview

Transform the prompt identifier system from collision-prone directory/filename IDs to full-path unique IDs with intelligent display name calculation.

## Implementation Phases

### **Phase 1: Data Model Updates**

#### **1.1 Update Prompt Model (`src/models/unified_prompt.py`)**
- **1.1.1** Change `id` field to store full file path as accessed by user
- **1.1.2** Add `display_name` property for smart display name calculation
- **1.1.3** Update `generate_id()` method to use full paths
- **1.1.4** Add `calculate_display_name()` static method
- **1.1.5** Ensure backward compatibility with `unique_id` field

#### **1.2 Display Name Calculation Logic**
- **1.2.1** Implement algorithm to find shortest unique display name
- **1.2.2** Handle directory parsing and comparison logic
- **1.2.3** Support colon-separated directory hierarchy (`project:dir:file`)
- **1.2.4** Add caching mechanism for performance optimization

### **Phase 2: Service Layer Updates**

#### **2.1 Update PromptService (`src/services/prompt_service.py`)**
- **2.1.1** Modify `load_prompt()` to generate full-path IDs
- **2.1.2** Update `get_prompt()` to handle both full paths and legacy IDs
- **2.1.3** Fix `create_prompt()` to use full-path ID generation
- **2.1.4** Update `rename_prompt()` for new ID schema
- **2.1.5** Modify `delete_prompt()` to handle full-path lookups

#### **2.2 Display Name Service**
- **2.2.1** Create `calculate_all_display_names()` method
- **2.2.2** Add `get_display_name_for_prompt()` helper method
- **2.2.3** Implement directory uniqueness analysis
- **2.2.4** Add performance optimization for large prompt sets

#### **2.3 Inclusion Resolution Updates**
- **2.3.1** Update `expand_inclusions()` to handle full-path IDs
- **2.3.2** Support both display names and full paths in `[[]]` syntax
- **2.3.3** Improve error messages for ambiguous inclusions
- **2.3.4** Add directory context for inclusion resolution

### **Phase 3: API Layer Updates**

#### **3.1 Update API Routes (`src/api/router.py`)**
- **3.1.1** Modify route parameters to accept full-path IDs
- **3.1.2** Update URL encoding/decoding for file paths
- **3.1.3** Add display name fields to API responses
- **3.1.4** Ensure backward compatibility during transition

#### **3.2 Response Schema Updates**
- **3.2.1** Add `display_name` field to prompt response models
- **3.2.2** Include both `id` (full path) and `display_name` in listings
- **3.2.3** Update create/update endpoints for new ID schema
- **3.2.4** Add migration endpoints for legacy ID handling

### **Phase 4: UI and Frontend Updates**

#### **4.1 Template Updates (`src/templates/`)**
- **4.1.1** Update prompt listings to show display names
- **4.1.2** Modify create/edit forms to handle new ID schema
- **4.1.3** Update deletion confirmations with display names
- **4.1.4** Ensure full path IDs are used in form submissions

#### **4.2 JavaScript Updates (`src/static/js/`)**
- **4.2.1** Update tab completion to use display names
- **4.2.2** Modify AJAX requests to send full-path IDs
- **4.2.3** Update search/filter functionality
- **4.2.4** Improve error handling for path-based operations

#### **4.3 Tab Completion Enhancement**
- **4.3.1** Implement smart display name suggestions
- **4.3.2** Add fuzzy matching for display names
- **4.3.3** Show both display name and full path in tooltips
- **4.3.4** Handle selection of display names vs full paths

### **Phase 5: Testing and Validation**

#### **5.1 Unit Tests Updates**
- **5.1.1** Update all existing prompt model tests
- **5.1.2** Add comprehensive display name calculation tests
- **5.1.3** Test ID generation with various path structures
- **5.1.4** Validate backward compatibility with legacy IDs

#### **5.2 Service Tests**
- **5.2.1** Update PromptService tests for new ID schema
- **5.2.2** Test inclusion resolution with full paths
- **5.2.3** Validate display name uniqueness algorithms
- **5.2.4** Test performance with large prompt sets

#### **5.3 API Integration Tests**
- **5.3.1** Update all API endpoint tests
- **5.3.2** Test URL encoding/decoding of file paths
- **5.3.3** Validate response schemas with new fields
- **5.3.4** Test backward compatibility endpoints

#### **5.4 UI Tests**
- **5.4.1** Update Playwright tests for new display logic
- **5.4.2** Test tab completion with display names
- **5.4.3** Validate form submissions with full-path IDs
- **5.4.4** Test edge cases (special characters, long paths)

### **Phase 6: Migration and Deployment**

#### **6.1 Migration Strategy**
- **6.1.1** Create migration script for existing installations
- **6.1.2** Support both old and new ID formats during transition
- **6.1.3** Add deprecation warnings for legacy usage
- **6.1.4** Provide rollback mechanism if needed

#### **6.2 Performance Optimization**
- **6.2.1** Implement display name caching
- **6.2.2** Optimize directory comparison algorithms
- **6.2.3** Add lazy loading for large prompt collections
- **6.2.4** Monitor memory usage with full-path IDs

#### **6.3 Documentation Updates**
- **6.3.1** Update API documentation with new schemas
- **6.3.2** Create migration guide for existing users
- **6.3.3** Document display name calculation algorithm
- **6.3.4** Add troubleshooting guide for path issues

## Technical Implementation Details

### **Display Name Algorithm**

```python
def calculate_display_name(prompt_paths: List[str], target_path: str) -> str:
    """
    Calculate the shortest unique display name for a prompt.
    
    Algorithm:
    1. Extract filename and check if globally unique
    2. If not unique, find first unique directory segment
    3. Build colon-separated path until unique
    4. Return shortest unique identifier
    """
    # Implementation details in Phase 1.2
```

### **ID Generation**

```python
def generate_full_path_id(file_path: str) -> str:
    """
    Generate full path ID preserving user's access path.
    
    Args:
        file_path: Complete file path as accessed by user
        
    Returns:
        Full path without .md extension
    """
    # Implementation details in Phase 1.1
```

### **Backward Compatibility**

- Maintain `unique_id` field during transition period
- Support legacy ID lookups in `get_prompt()`
- Add deprecation warnings for old format usage
- Provide migration utilities for existing data

## Risk Assessment

### **High Risk Areas**
- **URL Encoding**: File paths in URLs may cause encoding issues
- **Performance**: Display name calculation with large prompt sets
- **Migration**: Risk of data loss during ID schema changes
- **Testing**: Comprehensive test updates required

### **Mitigation Strategies**
- **URL Encoding**: Use proper percent-encoding for file paths
- **Performance**: Implement caching and lazy evaluation
- **Migration**: Create backup and rollback procedures
- **Testing**: Incremental testing with each phase

## Success Criteria

### **Functional Requirements**
- ✅ **Unique IDs**: All prompts have globally unique full-path IDs
- ✅ **Smart Display**: Display names are shortest unique identifiers
- ✅ **Tab Completion**: Works with intelligent display names
- ✅ **Backward Compatibility**: Legacy IDs work during transition
- ✅ **Performance**: No significant slowdown with new system

### **Technical Requirements**
- ✅ **100% Test Coverage**: All new functionality covered by tests
- ✅ **Zero Data Loss**: Migration preserves all existing prompts
- ✅ **API Consistency**: All endpoints use consistent ID schema
- ✅ **UI Consistency**: All interfaces show appropriate names

### **User Experience Requirements**
- ✅ **Clarity**: No ambiguous names in any interface
- ✅ **Efficiency**: Quick identification of desired prompts
- ✅ **Intuitive**: Display names make logical sense to users
- ✅ **Seamless**: Migration appears transparent to users

## Timeline Estimate

| Phase | Description | Time Estimate |
|-------|-------------|---------------|
| 1 | Data Model Updates | 2-3 hours |
| 2 | Service Layer Updates | 2-3 hours |
| 3 | API Layer Updates | 1-2 hours |
| 4 | UI and Frontend Updates | 2-3 hours |
| 5 | Testing and Validation | 2-3 hours |
| 6 | Migration and Deployment | 1-2 hours |

**Total Estimated Time:** 10-16 hours

## Next Steps

1. **Review and Approval**: Confirm implementation approach
2. **Phase 1 Implementation**: Start with data model updates
3. **Incremental Development**: Complete each phase with testing
4. **Integration Testing**: Validate end-to-end functionality
5. **Migration Preparation**: Create and test migration procedures
6. **Deployment**: Roll out with monitoring and rollback capability

---

**Implementation Status:** Ready to Begin  
**Prerequisites:** Implementation plan approval  
**Dependencies:** None - can proceed immediately
