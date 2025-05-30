# issue Prompt ID is not unique

Prompt Manager has a critical flaw. The prompt manager key does not incorporate the directory path so it is not unique. The Prompt ID in the "Create New Prompt" dialog should really be the "Name" of the prompt, and the prompt id should be the full path filename.

Can you please tell me how we can make this change so that we catch all and correct all usages of Prompt ID.

I think I'm bascially saying: let's make sure each prompt has a Prompt Id which is unique, a Name which can be duplicated, and a Directory which can be duplicated. However the Prompt ID is the full path made up the Directory plus path (os.path.join as it were) which is (normally!) unique.

# Project Rules

[[project_maintenance_rules]]

# Current Problem Analysis

Current ID System: prompt.id is just the filename stem (e.g., "test_prompt")
Non-Unique: Same filename in different directories creates collisions
Confusion: "Prompt ID" field should be "Name" and the real ID should be the full path

🏗️ Comprehensive Fix Strategy
Here's how I propose to fix this systematically:
Phase 1: Data Model Changes

Add name field to Prompt model for display purposes
Change id to be full path (directory + filename)
Keep unique_id as backup during transition
Update database/storage to handle the change

Phase 2: API Changes

Update all routes to use full-path IDs
Modify prompt creation to generate proper IDs
Update search/filter logic to work with new ID system
Fix inclusion resolution ([[prompt_name]] references)

Phase 3: UI Changes

Rename "Prompt ID" to "Name" in create dialog
Update display logic to show name vs full path
Fix editor URLs to handle full-path IDs
Update deletion/editing to use correct IDs

Phase 4: Reference Resolution

Update inclusion system to resolve [[name]] to full paths
Add directory context for inclusion resolution
Handle name conflicts when resolving inclusions
Update WebSocket/real-time features

Please create a detailed implementation plan and write out a progress update with the complete implementation plan and an overview of the problem we are trying to solve.
