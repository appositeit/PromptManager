from playwright.sync_api import Page, expect

# Base URL of the running application
# Make sure your Prompt Manager server is running on http://localhost:8081
BASE_URL = "http://localhost:8081"
MANAGE_PROMPTS_URL = f"{BASE_URL}/manage/prompts"

def test_app_loads_and_has_initial_data(page: Page):
    """Test that the main page loads, has correct title, and initial directory/prompt data."""
    try:
        page.goto(MANAGE_PROMPTS_URL)
        
        # Check the title of the page
        expect(page).to_have_title("Manage Prompts")
        
        # Check that the "Prompts" card title header is visible
        prompts_header = page.locator("h5.card-title:has-text('Prompts')")
        expect(prompts_header).to_be_visible()

        # Check that the "Directories" card title header is visible
        directories_header = page.locator("h5.card-title:has-text('Directories')")
        expect(directories_header).to_be_visible()

        # Wait for prompts table to potentially load data (e.g., remove loading spinner)
        # A robust way is to wait for the loading spinner to disappear or for a row to appear.
        # Assuming the loading row has a specific class or is removed.
        # For now, let's wait for at least one row to appear in each table.
        # This implicitly handles the loading state for this test case.

        # Check for at least one directory in the directories table
        # Locator for a row within the directories table body
        first_directory_row = page.locator("#directories-table-body tr").first
        expect(first_directory_row).to_be_visible(timeout=10000) # Wait up to 10s for data to load
        print("At least one directory found in the table.")

        # Check for at least one prompt in the prompts table
        # Locator for a row within the prompts table body
        first_prompt_row = page.locator("#prompts-table-body tr").first
        expect(first_prompt_row).to_be_visible(timeout=10000) # Wait up to 10s for data to load
        print("At least one prompt found in the table.")
        
    except Exception as e:
        # If a playwright._impl._api_types.Error (or similar) occurs, 
        # it might be due to the missing libicu dependency. 
        # We'll print the error to help diagnose.
        print(f"Playwright test failed: {e}")
        print("This might be due to missing system dependencies like libicu74.")
        print("Ensure the server is running at " + BASE_URL + " and has initial data.")
        raise # Re-raise the exception to fail the test

# To run this test:
# 1. Make sure your Prompt Manager server is running on http://localhost:8081
#    and is configured with some default/initial directories and prompts.
# 2. Run pytest from your project root: pytest tests/e2e/test_app_loads.py
#    Or, if you add it to a Makefile: make test-e2e 