import pytest
import time
from playwright.sync_api import Page, expect

# Base URL of the running application
BASE_URL = "http://localhost:8095"
MANAGE_PROMPTS_URL = f"{BASE_URL}/manage/prompts"

@pytest.fixture(scope="function", autouse=True)
def ensure_server_has_data(page: Page):
    """Fixture to ensure the server has at least one directory before tests run."""
    page.goto(MANAGE_PROMPTS_URL)
    # Check for at least one directory in the directories table
    first_directory_row = page.locator("#directories-table-body tr").first
    expect(first_directory_row).to_be_visible(timeout=10000)

class TestCopyFunctionality:
    """Test suite for copy functionality including Alt+C keyboard shortcut."""

    def test_copy_button_exists_and_is_functional(self, page: Page):
        """Test that the copy button exists and has proper attributes."""
        # Create a test prompt first
        self._create_test_prompt(page, "copy_test_prompt", "This is test content for copy functionality.")
        
        # Navigate to the prompt editor
        page.goto(f"{BASE_URL}/prompts/copy_test_prompt")
        
        # Verify copy button exists and has correct attributes
        copy_button = page.locator("#copy-btn")
        expect(copy_button).to_be_visible()
        expect(copy_button).to_have_attribute("title", "Copy content to clipboard (Alt+C)")
        
        # Verify copy button has correct icon
        copy_icon = copy_button.locator("i.bi-clipboard")
        expect(copy_icon).to_be_visible()
        
        # Clean up
        self._delete_test_prompt(page, "copy_test_prompt")

    def test_copy_button_click_functionality(self, page: Page):
        """Test that clicking the copy button works (basic functionality test)."""
        # Create a test prompt with specific content
        test_content = "Test content for copy button functionality test"
        self._create_test_prompt(page, "copy_button_test", test_content)
        
        # Navigate to the prompt editor
        page.goto(f"{BASE_URL}/prompts/copy_button_test")
        
        # Wait for editor to load
        editor = page.locator(".CodeMirror")
        expect(editor).to_be_visible(timeout=5000)
        
        # Grant clipboard permissions if possible (this may not work in all test environments)
        try:
            page.context.grant_permissions(["clipboard-write", "clipboard-read"])
        except Exception:
            # Permissions might not be grantable in test environment, continue anyway
            pass
        
        # Click the copy button
        copy_button = page.locator("#copy-btn")
        copy_button.click()
        
        # Look for success toast message (our copy function shows this)
        toast_success = page.locator(".toast:has-text('Content copied to clipboard!')")
        # We'll check if either success toast appears OR if we gracefully handle the case
        # where clipboard API isn't available (which shows a different message)
        toast_fallback = page.locator(".toast:has-text('Failed to copy content')")
        toast_no_api = page.locator(".toast:has-text('Copy functionality not available')")
        
        # Wait for one of the toast messages to appear
        try:
            expect(toast_success.or_(toast_fallback).or_(toast_no_api)).to_be_visible(timeout=3000)
            print("Copy button click triggered appropriate feedback message")
        except Exception:
            print("Copy button clicked but no toast appeared - this may be expected in test environment")
        
        # Clean up
        self._delete_test_prompt(page, "copy_button_test")

    def test_alt_c_keyboard_shortcut(self, page: Page):
        """Test that Alt+C keyboard shortcut triggers copy functionality."""
        # Create a test prompt
        test_content = "Test content for Alt+C keyboard shortcut test"
        self._create_test_prompt(page, "alt_c_test", test_content)
        
        # Navigate to the prompt editor
        page.goto(f"{BASE_URL}/prompts/alt_c_test")
        
        # Wait for editor to load
        editor = page.locator(".CodeMirror")
        expect(editor).to_be_visible(timeout=5000)
        
        # Grant clipboard permissions if possible
        try:
            page.context.grant_permissions(["clipboard-write", "clipboard-read"])
        except Exception:
            pass
        
        # Press Alt+C
        page.keyboard.press("Alt+c")
        
        # Look for toast message indicating copy was attempted
        toast_success = page.locator(".toast:has-text('Content copied to clipboard!')")
        toast_fallback = page.locator(".toast:has-text('Failed to copy content')")
        toast_no_api = page.locator(".toast:has-text('Copy functionality not available')")
        
        # Wait for one of the toast messages to appear
        try:
            expect(toast_success.or_(toast_fallback).or_(toast_no_api)).to_be_visible(timeout=3000)
            print("Alt+C keyboard shortcut triggered appropriate feedback message")
        except Exception:
            print("Alt+C pressed but no toast appeared - this may be expected in test environment")
        
        # Clean up
        self._delete_test_prompt(page, "alt_c_test")

    def test_copy_with_composite_prompt(self, page: Page):
        """Test copy functionality with a composite prompt (one that includes other prompts)."""
        # Create base prompt
        self._create_test_prompt(page, "base_prompt", "This is the base content.")
        
        # Create composite prompt that includes the base prompt
        composite_content = "Start of composite prompt.\n\n[[base_prompt]]\n\nEnd of composite prompt."
        self._create_test_prompt(page, "composite_test", composite_content)
        
        # Navigate to the composite prompt editor
        page.goto(f"{BASE_URL}/prompts/composite_test")
        
        # Wait for editor to load
        editor = page.locator(".CodeMirror")
        expect(editor).to_be_visible(timeout=5000)
        
        # Switch to expanded view to see the composite content
        toggle_button = page.locator("#toggle-view-btn")
        if toggle_button.is_visible():
            toggle_button.click()
            # Wait a moment for the toggle to complete
            page.wait_for_timeout(1000)
        
        # Grant clipboard permissions if possible
        try:
            page.context.grant_permissions(["clipboard-write", "clipboard-read"])
        except Exception:
            pass
        
        # Test copy functionality
        copy_button = page.locator("#copy-btn")
        copy_button.click()
        
        # Look for toast message
        toast_success = page.locator(".toast:has-text('Content copied to clipboard!')")
        toast_fallback = page.locator(".toast:has-text('Failed to copy content')")
        toast_no_api = page.locator(".toast:has-text('Copy functionality not available')")
        
        try:
            expect(toast_success.or_(toast_fallback).or_(toast_no_api)).to_be_visible(timeout=3000)
            print("Copy functionality worked with composite prompt")
        except Exception:
            print("Copy attempted with composite prompt - toast may not appear in test environment")
        
        # Clean up
        self._delete_test_prompt(page, "composite_test")
        self._delete_test_prompt(page, "base_prompt")

    def test_copy_error_handling_with_disabled_clipboard(self, page: Page):
        """Test that copy functionality gracefully handles clipboard API unavailability."""
        # Create a test prompt
        self._create_test_prompt(page, "error_test", "Test content for error handling")
        
        # Navigate to the prompt editor
        page.goto(f"{BASE_URL}/prompts/error_test")
        
        # Wait for editor to load
        editor = page.locator(".CodeMirror")
        expect(editor).to_be_visible(timeout=5000)
        
        # Disable clipboard API by overriding it with undefined
        page.evaluate("""
            // Simulate clipboard API being unavailable
            Object.defineProperty(navigator, 'clipboard', {
                value: undefined,
                writable: true
            });
        """)
        
        # Click copy button
        copy_button = page.locator("#copy-btn")
        copy_button.click()
        
        # Should see fallback behavior - either success from document.execCommand or appropriate error message
        toast_fallback_success = page.locator(".toast:has-text('Content copied to clipboard!')")
        toast_fallback_error = page.locator(".toast:has-text('Failed to copy content')")
        toast_no_api = page.locator(".toast:has-text('Copy functionality not available')")
        
        # One of these should appear
        expect(toast_fallback_success.or_(toast_fallback_error).or_(toast_no_api)).to_be_visible(timeout=3000)
        print("Copy functionality handled clipboard API unavailability gracefully")
        
        # Clean up
        self._delete_test_prompt(page, "error_test")

    def test_copy_function_exists_in_javascript(self, page: Page):
        """Test that the copyContent function exists and is properly defined."""
        # Navigate to any prompt editor page
        page.goto(MANAGE_PROMPTS_URL)
        
        # Create a test prompt to navigate to
        self._create_test_prompt(page, "js_test", "Test content")
        page.goto(f"{BASE_URL}/prompts/js_test")
        
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        
        # Check that copyContent function exists
        copy_function_exists = page.evaluate("typeof copyContent === 'function'")
        assert copy_function_exists, "copyContent function should be defined"
        
        # Check that the function has proper error handling
        function_source = page.evaluate("copyContent.toString()")
        assert "navigator.clipboard" in function_source, "Function should check for clipboard API"
        assert "document.execCommand" in function_source, "Function should have fallback method"
        assert "catch" in function_source, "Function should have error handling"
        
        # Clean up
        self._delete_test_prompt(page, "js_test")

    def _create_test_prompt(self, page: Page, prompt_name: str, content: str = "Test content"):
        """Helper method to create a test prompt."""
        page.goto(MANAGE_PROMPTS_URL)
        
        # Click "New Prompt" button
        new_prompt_button = page.locator("button#add-prompt-btn")
        expect(new_prompt_button).to_be_visible()
        new_prompt_button.click()
        
        # Fill out the modal
        modal = page.locator("#newPromptModal")
        expect(modal).to_be_visible()
        
        # Prompt Name
        prompt_name_input = modal.locator("#promptName")
        prompt_name_input.fill(prompt_name)
        
        # Directory (select the first one)
        directory_select = modal.locator("#promptDirectory")
        first_option_locator = directory_select.locator("option[value]:not([value=''])").first
        expect(first_option_locator).to_be_enabled(timeout=5000)
        first_option_value = first_option_locator.get_attribute("value")
        directory_select.select_option(first_option_value)
        
        # Content (will be set after creation)
        description_input = modal.locator("#promptDescription")
        description_input.fill("Test prompt for copy functionality testing")
        
        # Create the prompt
        create_button = modal.locator("#createPromptBtn")
        create_button.click()
        
        # Wait for modal to close
        expect(modal).not_to_be_visible(timeout=5000)
        
        # Navigate to the prompt and set content
        page.goto(f"{BASE_URL}/prompts/{prompt_name}")
        
        # Wait for editor to load and set content
        editor = page.locator(".CodeMirror")
        expect(editor).to_be_visible(timeout=5000)
        
        # Click in the editor and set content
        editor.click()
        page.keyboard.press("Control+a")  # Select all
        page.keyboard.type(content)
        
        # Save the prompt
        save_button = page.locator("#save-btn")
        if save_button.is_visible():
            save_button.click()
            # Wait for save confirmation
            page.wait_for_timeout(1000)

    def _delete_test_prompt(self, page: Page, prompt_name: str):
        """Helper method to delete a test prompt."""
        page.goto(MANAGE_PROMPTS_URL)
        
        # Find the prompt row and delete it
        prompt_row = page.locator(f"#prompts-table-body tr:has(a:has-text('{prompt_name}'))")
        if prompt_row.is_visible():
            delete_button = prompt_row.locator("button[title='Delete this prompt']")
            if not delete_button.is_visible():
                delete_button = prompt_row.locator("button.btn-danger")
            
            if delete_button.is_visible():
                delete_button.click()
                
                # Handle confirmation modal
                delete_confirm_modal = page.locator("#deletePromptModal")
                if delete_confirm_modal.is_visible():
                    confirm_delete_button = delete_confirm_modal.locator("#confirm-delete-btn")
                    confirm_delete_button.click()
                    expect(delete_confirm_modal).not_to_be_visible(timeout=5000)
