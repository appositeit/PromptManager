import pytest
import time
from playwright.sync_api import Page, expect

# Base URL of the running application
BASE_URL = "http://localhost:8081"
MANAGE_PROMPTS_URL = f"{BASE_URL}/manage/prompts"

@pytest.fixture(scope="function", autouse=True)
def ensure_server_has_data(page: Page):
    """Fixture to ensure the server has at least one directory before tests run."""
    page.goto(MANAGE_PROMPTS_URL)
    # Check for at least one directory in the directories table
    first_directory_row = page.locator("#directories-table-body tr").first
    expect(first_directory_row).to_be_visible(timeout=10000) # Wait up to 10s
    # This fixture doesn't return anything, just ensures pre-condition

def test_create_and_delete_new_prompt(page: Page):
    """Test creating a new prompt and then deleting it."""
    page.goto(MANAGE_PROMPTS_URL)

    # --- Create a unique prompt ID for this test run ---
    timestamp = int(time.time())
    new_prompt_id = f"e2e_test_prompt_{timestamp}"
    new_prompt_description = f"E2E test description for {new_prompt_id}"
    new_prompt_tags = "e2e,test,temporary"

    # --- Click "New Prompt" button ---
    new_prompt_button = page.locator("button#new-prompt-btn")
    expect(new_prompt_button).to_be_visible()
    new_prompt_button.click()

    # --- Fill out the modal ---
    modal = page.locator("#newPromptModal")
    expect(modal).to_be_visible()

    # Prompt ID
    prompt_id_input = modal.locator("#promptId")
    expect(prompt_id_input).to_be_editable()
    prompt_id_input.fill(new_prompt_id)

    # Directory (select the first one)
    directory_select = modal.locator("#promptDirectory")
    expect(directory_select).to_be_visible()
    # Get the value of the first actual option (not the placeholder if any)
    # We need to make sure options are loaded into the select
    first_option_locator = directory_select.locator("option[value]:not([value=''])").first
    expect(first_option_locator).to_be_enabled(timeout=5000) # Wait for options to load
    first_option_value = first_option_locator.get_attribute("value")
    
    if not first_option_value:
        pytest.fail("No directories found in the new prompt modal dropdown.")
    directory_select.select_option(first_option_value)

    # Description
    description_input = modal.locator("#promptDescription")
    description_input.fill(new_prompt_description)

    # Tags
    tags_input = modal.locator("#promptTags")
    tags_input.fill(new_prompt_tags)

    # Click "Create"
    create_button = modal.locator("#createPromptBtn")
    expect(create_button).to_be_enabled()
    create_button.click()

    # --- Verify modal closes and prompt appears in the table ---
    expect(modal).not_to_be_visible(timeout=5000) # Modal should close

    # Search for the new prompt in the table
    # We need to be specific to avoid matching other prompts if the table is large
    # A good way is to find the row by a unique data attribute or by cell content
    # For now, let's try to find it by its ID in a cell. 
    # This assumes prompt ID is displayed and unique in a column.
    # Adjust locator based on how prompt ID is displayed in your table (e.g., in an <a> tag)
    
    # Wait for the table to potentially refresh and show the new prompt
    # A robust way is to look for the specific row for the new prompt ID.
    # We will look for a link with the prompt ID text within the prompts table body.
    new_prompt_link_in_table = page.locator(f"#prompts-table-body a:has-text('{new_prompt_id}')")
    
    # PAUSE here to inspect if the test fails at the next step
    # Make sure to run pytest with headed mode: pytest --headed tests/e2e/...
    # page.pause() # Uncomment this line to debug interactively

    expect(new_prompt_link_in_table).to_be_visible(timeout=10000) # Increased timeout for table update
    print(f"Prompt '{new_prompt_id}' found in the table.")

    # --- Navigate to the new prompt's edit page (optional verification) ---
    new_prompt_link_in_table.click()
    expect(page).to_have_url(f"{BASE_URL}/prompts/{new_prompt_id}", timeout=5000)
    expect(page).to_have_title(f"Edit: {new_prompt_id}") # Or however the title is formatted
    print(f"Successfully navigated to edit page for '{new_prompt_id}'.")
    page.go_back() # Go back to manage prompts page for cleanup
    expect(page).to_have_url(MANAGE_PROMPTS_URL, timeout=5000)

    # --- Clean up: Delete the created prompt ---
    # Find the row containing the new prompt again
    # This time, we need to find the row to click its delete button
    # Assuming the link is in a `td`, and its parent `tr` is the row.
    prompt_row = page.locator(f"#prompts-table-body tr:has(a:has-text('{new_prompt_id}'))")
    expect(prompt_row).to_be_visible()

    # Find and click the delete button for that row
    # This assumes a delete button with a specific class or structure within the row
    # Let's assume it's a button with class 'btn-delete-prompt' or similar, or a title
    delete_button_in_row = prompt_row.locator("button[title='Delete this prompt']") # More specific title
    if not delete_button_in_row.is_visible(): # Fallback if title isn't there
         delete_button_in_row = prompt_row.locator("button.btn-danger") 
    
    expect(delete_button_in_row).to_be_visible()
    delete_button_in_row.click()

    # Handle confirmation modal
    delete_confirm_modal = page.locator("#deletePromptModal")
    expect(delete_confirm_modal).to_be_visible()
    confirm_delete_button = delete_confirm_modal.locator("#confirm-delete-btn")
    expect(confirm_delete_button).to_be_enabled()
    confirm_delete_button.click()

    # --- Verify prompt is removed from the table ---
    expect(delete_confirm_modal).not_to_be_visible(timeout=5000)
    # The link to the prompt should no longer be visible
    expect(new_prompt_link_in_table).not_to_be_visible(timeout=10000)
    print(f"Prompt '{new_prompt_id}' successfully deleted.") 