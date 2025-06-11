"""
E2E test for directory sorting in the New Prompt modal.
Tests that directories appear in alphabetical order in the select dropdown.
"""

import pytest
from playwright.sync_api import Page, expect

# Base URL of the running application
BASE_URL = "http://localhost:8095"
MANAGE_PROMPTS_URL = f"{BASE_URL}/manage/prompts"


class TestDirectorySortingE2E:
    """Test directory sorting in the browser."""
    
    def test_new_prompt_modal_directory_sorting(self, page: Page):
        """Test that directories are sorted alphabetically in the New Prompt modal."""
        # Navigate to manage prompts page
        page.goto(MANAGE_PROMPTS_URL)
        
        # Wait for page to load and ensure directories are loaded
        page.wait_for_load_state("networkidle")
        
        # Click the "New Prompt" button to open modal
        page.click("button[data-bs-target='#newPromptModal']")
        
        # Wait for modal to appear
        modal = page.locator("#newPromptModal")
        expect(modal).to_be_visible()
        
        # Get the directory select element
        directory_select = modal.locator("#promptDirectory")
        expect(directory_select).to_be_visible()
        
        # Wait a moment for the directories to be populated
        page.wait_for_timeout(1000)
        
        # Get all option elements (skip the first one which might be empty)
        options = directory_select.locator("option[value]:not([value=''])")
        
        # Check if we have any options
        option_count = options.count()
        if option_count == 0:
            pytest.skip("No directories available for testing")
        
        # Get all option texts
        option_texts = []
        for i in range(option_count):
            option_text = options.nth(i).text_content()
            if option_text:
                option_texts.append(option_text)
        
        # Verify that the options are sorted alphabetically
        sorted_texts = sorted(option_texts)
        
        # Compare the actual order with the sorted order
        assert option_texts == sorted_texts, f"Directory options are not sorted. Got: {option_texts}, Expected: {sorted_texts}"
        
        # Close the modal
        page.keyboard.press("Escape")
        
    def test_new_prompt_modal_directory_sorting_after_refresh(self, page: Page):
        """Test that directories remain sorted after refreshing directories."""
        # Navigate to manage prompts page
        page.goto(MANAGE_PROMPTS_URL)
        
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        
        # Click refresh all button to ensure directories are fresh
        page.click("#refresh-all-btn")
        
        # Wait for refresh to complete
        page.wait_for_timeout(2000)
        
        # Click the "New Prompt" button to open modal
        page.click("button[data-bs-target='#newPromptModal']")
        
        # Wait for modal to appear
        modal = page.locator("#newPromptModal")
        expect(modal).to_be_visible()
        
        # Get the directory select element
        directory_select = modal.locator("#promptDirectory")
        expect(directory_select).to_be_visible()
        
        # Wait a moment for the directories to be populated
        page.wait_for_timeout(1000)
        
        # Get all option elements (skip empty values)
        options = directory_select.locator("option[value]:not([value=''])")
        
        # Check if we have any options
        option_count = options.count()
        if option_count == 0:
            pytest.skip("No directories available for testing")
        
        # Get all option texts
        option_texts = []
        for i in range(option_count):
            option_text = options.nth(i).text_content()
            if option_text:
                option_texts.append(option_text)
        
        # Verify that the options are sorted alphabetically
        sorted_texts = sorted(option_texts)
        
        # Compare the actual order with the sorted order
        assert option_texts == sorted_texts, f"Directory options are not sorted after refresh. Got: {option_texts}, Expected: {sorted_texts}"
        
        # Close the modal
        page.keyboard.press("Escape")
