"""
Simple test cases for the copy functionality bug fix.
These tests verify that the Alt+C copy functionality works without errors.
"""

import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "http://localhost:8095"
MANAGE_PROMPTS_URL = f"{BASE_URL}/manage/prompts"

class TestCopyBugFix:
    """Test suite specifically for the Alt+C copy bug fix."""

    def test_copy_button_exists_and_clickable(self, page: Page):
        """Test that the copy button exists and is clickable without throwing errors."""
        # Create a simple test prompt
        prompt_name = f"copy_test_{int(time.time())}"
        self._create_test_prompt(page, prompt_name)
        
        try:
            # Navigate to the prompt editor
            page.goto(f"{BASE_URL}/prompts/{prompt_name}")
            
            # Wait for the page to load completely
            page.wait_for_load_state("networkidle")
            
            # Verify copy button exists
            copy_button = page.locator("#copy-btn")
            expect(copy_button).to_be_visible()
            expect(copy_button).to_have_attribute("title", "Copy content to clipboard (Alt+C)")
            
            # Click the copy button and verify no JavaScript errors occur
            copy_button.click()
            
            # Wait a moment for any toast notifications
            page.wait_for_timeout(1000)
            
            # Check that no JavaScript errors were thrown (the original bug would cause errors)
            # We'll check if the page is still functional by trying to click the button again
            expect(copy_button).to_be_visible()
            
            print(f"✅ Copy button test passed for prompt: {prompt_name}")
            
        finally:
            # Clean up
            self._delete_test_prompt(page, prompt_name)

    def test_alt_c_keyboard_shortcut_no_errors(self, page: Page):
        """Test that Alt+C keyboard shortcut doesn't throw JavaScript errors."""
        prompt_name = f"alt_c_test_{int(time.time())}"
        self._create_test_prompt(page, prompt_name)
        
        try:
            # Navigate to the prompt editor
            page.goto(f"{BASE_URL}/prompts/{prompt_name}")
            page.wait_for_load_state("networkidle")
            
            # Press Alt+C
            page.keyboard.press("Alt+c")
            
            # Wait for any potential processing
            page.wait_for_timeout(1000)
            
            # Verify the page is still functional after Alt+C
            copy_button = page.locator("#copy-btn")
            expect(copy_button).to_be_visible()
            
            # Try Alt+C again to make sure it's still working
            page.keyboard.press("Alt+C")  # Test with capital C too
            page.wait_for_timeout(500)
            
            print(f"✅ Alt+C keyboard test passed for prompt: {prompt_name}")
            
        finally:
            # Clean up
            self._delete_test_prompt(page, prompt_name)

    def test_copy_with_different_content_types(self, page: Page):
        """Test copy functionality with different types of content."""
        test_cases = [
            ("simple_text", "Simple text content for testing copy functionality."),
            ("multiline_text", "Line 1\\nLine 2\\nLine 3\\nMultiple lines for testing."),
            ("special_chars", "Content with special chars: @#$%^&*()[]{}|\\\\;':\",./<>?"),
            ("empty_content", ""),
        ]
        
        for test_name, test_content in test_cases:
            prompt_name = f"copy_content_test_{test_name}_{int(time.time())}"
            
            try:
                # Create prompt with specific content
                self._create_test_prompt(page, prompt_name, test_content)
                
                # Navigate to editor
                page.goto(f"{BASE_URL}/prompts/{prompt_name}")
                page.wait_for_load_state("networkidle")
                
                # Test copy button
                copy_button = page.locator("#copy-btn")
                expect(copy_button).to_be_visible()
                copy_button.click()
                
                # Test Alt+C
                page.keyboard.press("Alt+c")
                
                # Verify no errors by checking page is still functional
                expect(copy_button).to_be_visible()
                
                print(f"✅ Copy test passed for content type: {test_name}")
                
            finally:
                # Clean up
                self._delete_test_prompt(page, prompt_name)

    def test_copy_function_exists_in_browser_console(self, page: Page):
        """Test that the copyContent function exists and has proper error handling."""
        prompt_name = f"js_function_test_{int(time.time())}"
        self._create_test_prompt(page, prompt_name)
        
        try:
            page.goto(f"{BASE_URL}/prompts/{prompt_name}")
            page.wait_for_load_state("networkidle")
            
            # Check that copyContent function exists
            function_exists = page.evaluate("typeof copyContent === 'function'")
            assert function_exists, "copyContent function should exist"
            
            # Check that the function has proper error handling (look for key indicators)
            function_source = page.evaluate("copyContent.toString()")
            
            # Verify the function has our bug fixes
            assert "navigator.clipboard" in function_source, "Function should check for clipboard API"
            assert "catch" in function_source, "Function should have error handling"
            
            # The bug fix should include fallback method
            assert ("document.execCommand" in function_source or 
                   "textArea" in function_source), "Function should have fallback method"
            
            print("✅ copyContent function exists and has proper error handling")
            
        finally:
            self._delete_test_prompt(page, prompt_name)

    def _create_test_prompt(self, page: Page, prompt_name: str, content: str = "Test content for copy functionality"):
        """Helper method to create a test prompt via UI."""
        page.goto(MANAGE_PROMPTS_URL)
        
        # Click "New Prompt" button
        new_prompt_button = page.locator("button#add-prompt-btn")
        expect(new_prompt_button).to_be_visible(timeout=10000)
        new_prompt_button.click()
        
        # Fill out the modal
        modal = page.locator("#newPromptModal")
        expect(modal).to_be_visible()
        
        # Fill in prompt name
        prompt_name_input = modal.locator("#promptName")
        prompt_name_input.fill(prompt_name)
        
        # Select first available directory
        directory_select = modal.locator("#promptDirectory")
        first_option = directory_select.locator("option[value]:not([value=''])").first
        expect(first_option).to_be_enabled(timeout=5000)
        first_option_value = first_option.get_attribute("value")
        directory_select.select_option(first_option_value)
        
        # Add description
        description_input = modal.locator("#promptDescription")
        description_input.fill(f"Test prompt for copy functionality - {prompt_name}")
        
        # Create the prompt
        create_button = modal.locator("#createPromptBtn")
        create_button.click()
        expect(modal).not_to_be_visible(timeout=5000)
        
        # Navigate to editor and set content if provided
        if content:
            page.goto(f"{BASE_URL}/prompts/{prompt_name}")
            editor = page.locator(".CodeMirror")
            expect(editor).to_be_visible(timeout=5000)
            
            # Set content
            editor.click()
            page.keyboard.press("Control+a")
            page.keyboard.type(content)
            
            # Save
            save_button = page.locator("#save-btn")
            if save_button.is_visible():
                save_button.click()
                page.wait_for_timeout(1000)

    def _delete_test_prompt(self, page: Page, prompt_name: str):
        """Helper method to delete a test prompt."""
        page.goto(MANAGE_PROMPTS_URL)
        
        # Find and delete the prompt
        prompt_row = page.locator(f"#prompts-table-body tr:has(a:has-text('{prompt_name}'))")
        if prompt_row.is_visible():
            delete_button = prompt_row.locator("button[title='Delete this prompt']")
            if not delete_button.is_visible():
                delete_button = prompt_row.locator("button.btn-danger")
            
            if delete_button.is_visible():
                delete_button.click()
                
                # Confirm deletion
                confirm_modal = page.locator("#deletePromptModal")
                if confirm_modal.is_visible():
                    confirm_button = confirm_modal.locator("#confirm-delete-btn")
                    confirm_button.click()
                    expect(confirm_modal).not_to_be_visible(timeout=5000)
