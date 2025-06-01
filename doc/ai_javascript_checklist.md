# AI Development Checklist for JavaScript Changes

This checklist should be followed whenever making changes to JavaScript code, especially in templates that include external JS files.

## Pre-Change Analysis
- [ ] **List imported JS files:** Check what JavaScript files are imported in the template
- [ ] **Check global variables:** Review global variables declared in imported files (search for `let`, `const`, `var` declarations)
- [ ] **Identify naming conflicts:** Ensure new variable names don't conflict with globals
- [ ] **Review function dependencies:** Check if functions reference other functions defined later

## During Implementation
- [ ] **Use specific variable names:** Prefer `componentVariableName` over generic names like `modal`
- [ ] **Define before use:** Ensure all functions are defined before being referenced
- [ ] **Add error handling:** Wrap initialization in try/catch blocks
- [ ] **Handle DOM timing:** Check for both early and late script execution scenarios

## Testing Protocol
- [ ] **Browser console check:** Open browser dev tools and check for JavaScript errors immediately after changes
- [ ] **Functionality test:** Manually test the changed functionality in the browser
- [ ] **Page reload test:** Test with hard refresh (Ctrl+F5) to ensure clean loading
- [ ] **Run E2E tests:** Execute `make test-e2e` for any template changes affecting user flows

## Post-Implementation Verification
- [ ] **Error monitoring:** Check that global error handler doesn't trigger
- [ ] **Cross-browser check:** Test in different browsers if possible
- [ ] **Integration test:** Verify that new functionality doesn't break existing features
- [ ] **Commit atomic changes:** Each functional change should be a separate commit with clear description

## Red Flags to Watch For
- ⚠️ **"Identifier has already been declared" errors:** Variable name conflicts
- ⚠️ **"Function is not defined" errors:** Forward references or missing imports
- ⚠️ **Silent failures:** Page loads but functionality missing (like the CodeMirror issue)
- ⚠️ **DOMContentLoaded timing:** Script execution happening at wrong time

## Recovery Actions
If a JavaScript error is discovered:
1. **Immediate:** Use browser dev tools to identify the exact error
2. **Isolate:** Comment out recent changes to identify the problematic code
3. **Fix:** Address the root cause, not just the symptom
4. **Test:** Verify the fix doesn't introduce new issues
5. **Document:** Add entry to regressions.yaml following the failure process

## Tools for Prevention
- **Browser Dev Tools:** Always keep console open during development
- **ESLint/JSHint:** Consider adding static analysis tools
- **Error Monitoring:** Use the global error handler added to base.html
- **Incremental Testing:** Test after each significant change, not just at the end

This checklist is designed to prevent the specific JavaScript issues that caused the prompt editor regression.
