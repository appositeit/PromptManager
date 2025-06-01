export default [
    {
        files: ["src/static/js/**/*.js"],
        languageOptions: {
            ecmaVersion: 2022,
            sourceType: "script", // Most browser JS is still script, not module
            globals: {
                // Browser globals
                window: "readonly",
                document: "readonly",
                console: "readonly",
                setTimeout: "readonly",
                clearTimeout: "readonly",
                setInterval: "readonly",
                clearInterval: "readonly",
                fetch: "readonly",
                alert: "readonly",
                confirm: "readonly",
                localStorage: "readonly",
                FormData: "readonly",
                WebSocket: "readonly",
                CustomEvent: "readonly",
                
                // Third-party library globals that are loaded via CDN
                bootstrap: "readonly",
                CodeMirror: "readonly",
                marked: "readonly",
                dayjs: "readonly",
                dayjs_plugin_relativeTime: "readonly",
                d3: "readonly",
                
                // Our application globals
                showToast: "readonly",
                showNewPromptModal: "readonly",
                populateNewPromptDirectories: "readonly",
                NewPromptModal: "readonly",
                SearchReplace: "readonly",
                loadPrompts: "readonly",
                showNotification: "readonly",
                createSessionWebSocket: "readonly",
                VisualizationWebSocketClient: "readonly",
                TaskGraphVisualizer: "readonly",
                TaskTimelineVisualizer: "readonly"
            }
        },
        rules: {
            // Rules that would have caught our specific regression
            "no-redeclare": "error",              // ⭐ Would have caught newPromptModal conflict
            "no-undef": "error",                  // ⭐ Would have caught window.promptHint forward reference
            "no-unused-vars": "warn",             // Catch unused variables
            "no-global-assign": "error",          // Prevent global variable reassignment
            
            // Code quality rules
            "no-var": "error",                    // Prefer let/const over var
            "prefer-const": "warn",               // Use const when variable isn't reassigned
            "eqeqeq": "error",                    // Require === instead of ==
            "curly": "error",                     // Require curly braces for all control statements
            
            // Best practices for our patterns
            "no-implicit-globals": "error",       // Prevent accidental globals
            "no-shadow": "warn",                  // Warn about variable shadowing
            "consistent-return": "warn",          // Consistent return statements
            
            // Error prevention
            "no-unreachable": "error",            // Catch unreachable code
            "no-dupe-args": "error",              // Catch duplicate function arguments
            "no-dupe-keys": "error",              // Catch duplicate object keys
            "no-duplicate-case": "error",         // Catch duplicate switch cases
        }
    },
    {
        // Specific rules for files that define globals
        files: ["src/static/js/utils.js", "src/static/js/new_prompt_modal.js", "src/static/js/components/toast-manager.js", "src/static/js/search-replace.js", "src/static/js/visualization/*.js", "src/static/js/websocket_client.js"],
        languageOptions: {
            globals: {
                // Allow these files to define globals
                showToast: "writable",
                showNewPromptModal: "writable", 
                NewPromptModal: "writable",
                newPromptModal: "writable",  // Allow the global instance
                SearchReplace: "writable",
                TaskGraphVisualizer: "writable",
                TaskTimelineVisualizer: "writable",
                VisualizationWebSocketClient: "writable"
            }
        },
        rules: {
            "no-redeclare": "off"  // Allow redeclaration in files that define globals
        }
    }
];
