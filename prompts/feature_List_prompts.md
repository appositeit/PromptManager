# feature List prompts

[[/home/jem/development/prompt_manager/prompts/restart]]

I'd like to add a new box (also collapsible, default open) which lists the unique shortnames of the other prompts in that directory. We often want to cross reference/embed other prompts, so this acts as a reminder of which prompts already exist. Can we make it so we can drag the shortcut into the raw text edit window and it inserts the appropriate embed text shortcut, which will then expan in the Expanded Content tab to the appropriate prompt.

You have implemented this change, but the Directory Prompts never load. I see errors:

/home/jem/development/prompt_manager/prompts/feature_List_prompts:832 JavaScript Error: Object
(anonymous) @ /home/jem/development/prompt_manager/prompts/feature_List_prompts:832Understand this error
collapsible-sidebar.js:327 Uncaught TypeError: Cannot read properties of undefined (reading 'wrapper')
    at CollapsibleSidebar.setupEditorDragTarget (collapsible-sidebar.js:327:53)
    at CollapsibleSidebar.bindEvents (collapsible-sidebar.js:383:18)
    at new CollapsibleSidebar (collapsible-sidebar.js:15:14)
    at HTMLDocument.<anonymous> (collapsible-sidebar.js:406:37)