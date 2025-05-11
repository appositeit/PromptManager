# Progress Update: Removed Fragment Concept

## Changes Made
I've removed the fragment concept from the system, simplifying everything to just "prompts" that can be composed. The changes include:

1. Archived the original fragments_router_redirect.py to remove direct support for the fragments API
2. Created a new fragments_router_redirect.py that redirects all fragment API requests to the prompts API
3. Updated the app.py file to include the new redirect router

The changes maintain compatibility by:
- Properly redirecting any requests to /api/prompts/fragments/* to the corresponding /api/prompts/* endpoints
- Preserving HTTP methods using 307 redirects for POST, PUT, and DELETE operations
- Keeping special handling for the /api/prompts/fragments/expand endpoint

After these changes, any code or UI that was still using fragment endpoints will continue to work through the redirects, but all operations now use the unified prompt concept internally.

## Next Steps
If needed, we can also:
1. Update any remaining UI references to fragments
2. Clean up any fragment-specific code in the frontend JavaScript
3. Remove fragment-specific templates
