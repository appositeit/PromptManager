# feature New Prompt on Prompt Editor

[[/home/jem/development/prompt_manager/prompts/restart]]

Currently the prompt editor window does not have a New Prompt button (and shortcut). Let's add one, exactly like on the home page.

I want to modify New Prompt dialog:
- Add a new button "Create in new tab" with ctrl+shift+enter as the keyboard shortcut.
- We should default Directory field to the current directory. 
- Hovertext on all buttons and fields should show the keyboard shortcut for that button.

Please make sure we reuse the existing new prompt dialog and don't recreate it. There may be need to be some optional functions which are only enabled in the Prompt Editor page.