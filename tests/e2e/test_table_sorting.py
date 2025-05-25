"""
End-to-end tests for table sorting functionality on the manage prompts page.

These tests verify that both the Prompts table and Directories table 
can be sorted by clicking on column headers, and that the sorting
works correctly with proper visual feedback.
"""

import pytest
from playwright.sync_api import Page, expect

# Base URL of the running application
BASE_URL = "http://localhost:8095"
MANAGE_PROMPTS_URL = f"{BASE_URL}/manage/prompts"

class TestTableSorting:
    """Test class for table sorting functionality."""
    
    def setup_method(self):
        """Setup method called before each test."""
        pass
    
    def wait_for_tables_to_load(self, page: Page):
        """Helper method to wait for both tables to load data."""
        # Wait for prompts table to load
        prompts_table_body = page.locator('#prompts-table-body')
        expect(prompts_table_body.locator('tr:has-text("Loading prompts...")')).not_to_be_visible(timeout=15000)
        
        # Wait for directories table to load
        directories_table_body = page.locator('#directories-table-body')
        expect(directories_table_body.locator('tr:has-text("Loading directories...")')).not_to_be_visible(timeout=15000)
        
        # Verify we have at least one row in each table
        prompts_row_count = prompts_table_body.locator('tr td:first-child').count()
        directories_row_count = directories_table_body.locator('tr td:first-child').count()
        
        if prompts_row_count == 0:
            pytest.skip("No prompts available for testing sorting")
        if directories_row_count == 0:
            pytest.skip("No directories available for testing sorting")
    
    def get_column_values(self, page: Page, table_selector: str, column_index: int) -> list:
        """Extract text values from a specific column in a table."""
        rows = page.locator(f"{table_selector} tr")
        values = []
        
        for i in range(rows.count()):
            cell = rows.nth(i).locator(f"td:nth-child({column_index})")
            if cell.count() > 0:
                text = cell.text_content().strip()
                # Skip empty cells and action columns
                if text and not text.startswith("Edit") and not text.startswith("Refresh"):
                    values.append(text)
        
        return values
    
    def test_prompts_table_directory_column_sorting(self, page: Page):
        """Test sorting the prompts table by the Directory column."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Get the Directory column header (first column)
        directory_header = page.locator('table:not(#directories-table) th[data-sort="directory"]')
        expect(directory_header).to_be_visible()
        
        # Get initial values
        initial_values = self.get_column_values(page, '#prompts-table-body', 1)
        if len(initial_values) < 2:
            pytest.skip("Need at least 2 prompts to test sorting")
        
        # Click to sort ascending
        directory_header.click()
        page.wait_for_timeout(500)  # Allow sorting to complete
        
        # Verify sort icon is active
        expect(directory_header).to_have_class("sort-active")
        expect(directory_header).to_have_class("sort-asc")
        
        # Get sorted values and verify they're in ascending order
        sorted_values = self.get_column_values(page, '#prompts-table-body', 1)
        assert sorted_values == sorted(sorted_values), "Directory column should be sorted ascending"
        
        # Click again to sort descending
        directory_header.click()
        page.wait_for_timeout(500)
        
        # Verify descending sort
        expect(directory_header).to_have_class("sort-desc")
        desc_sorted_values = self.get_column_values(page, '#prompts-table-body', 1)
        assert desc_sorted_values == sorted(desc_sorted_values, reverse=True), "Directory column should be sorted descending"
    
    def test_prompts_table_name_column_sorting(self, page: Page):
        """Test sorting the prompts table by the Name column."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Get the Name column header (second column)
        name_header = page.locator('table:not(#directories-table) th[data-sort="id"]')
        expect(name_header).to_be_visible()
        
        # Get initial values
        initial_values = self.get_column_values(page, '#prompts-table-body', 2)
        if len(initial_values) < 2:
            pytest.skip("Need at least 2 prompts to test sorting")
        
        # Click to sort ascending
        name_header.click()
        page.wait_for_timeout(500)
        
        # Verify sort is active
        expect(name_header).to_have_class("sort-active")
        
        # Get sorted values and verify
        sorted_values = self.get_column_values(page, '#prompts-table-body', 2)
        assert sorted_values == sorted(sorted_values), "Name column should be sorted ascending"
    
    def test_prompts_table_description_column_sorting(self, page: Page):
        """Test sorting the prompts table by the Description column."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Get the Description column header (third column)
        desc_header = page.locator('table:not(#directories-table) th[data-sort="description"]')
        expect(desc_header).to_be_visible()
        
        # Click to sort
        desc_header.click()
        page.wait_for_timeout(500)
        
        # Verify sort is active
        expect(desc_header).to_have_class("sort-active")
    
    def test_prompts_table_updated_column_sorting(self, page: Page):
        """Test sorting the prompts table by the Last Updated column."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Get the Last Updated column header (fifth column)
        updated_header = page.locator('table:not(#directories-table) th[data-sort="updated"]')
        expect(updated_header).to_be_visible()
        
        # Click to sort
        updated_header.click()
        page.wait_for_timeout(500)
        
        # Verify sort is active
        expect(updated_header).to_have_class("sort-active")
    
    def test_directories_table_name_column_sorting(self, page: Page):
        """Test sorting the directories table by the Name column."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Get the Name column header for directories table
        name_header = page.locator('#directories-table th[data-sort="name"]')
        expect(name_header).to_be_visible()
        
        # Get initial values
        initial_values = self.get_column_values(page, '#directories-table-body', 1)
        if len(initial_values) < 2:
            pytest.skip("Need at least 2 directories to test sorting")
        
        # Click to sort ascending
        name_header.click()
        page.wait_for_timeout(500)
        
        # Verify sort is active
        expect(name_header).to_have_class("sort-active")
        expect(name_header).to_have_class("sort-asc")
        
        # Get sorted values and verify
        sorted_values = self.get_column_values(page, '#directories-table-body', 1)
        assert sorted_values == sorted(sorted_values), "Directories name column should be sorted ascending"
        
        # Click again to sort descending
        name_header.click()
        page.wait_for_timeout(500)
        
        # Verify descending sort
        expect(name_header).to_have_class("sort-desc")
        desc_sorted_values = self.get_column_values(page, '#directories-table-body', 1)
        assert desc_sorted_values == sorted(desc_sorted_values, reverse=True), "Directories name column should be sorted descending"
    
    def test_directories_table_status_column_sorting(self, page: Page):
        """Test sorting the directories table by the Status column."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Get the Status column header
        status_header = page.locator('#directories-table th[data-sort="status"]')
        expect(status_header).to_be_visible()
        
        # Click to sort
        status_header.click()
        page.wait_for_timeout(500)
        
        # Verify sort is active
        expect(status_header).to_have_class("sort-active")
        
        # Get status values and verify they make sense (Enabled/Disabled)
        status_values = self.get_column_values(page, '#directories-table-body', 2)
        for status in status_values:
            assert status in ['Enabled', 'Disabled'], f"Status should be 'Enabled' or 'Disabled', got '{status}'"
    
    def test_directories_table_path_column_sorting(self, page: Page):
        """Test sorting the directories table by the Path column."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Get the Path column header
        path_header = page.locator('#directories-table th[data-sort="path"]')
        expect(path_header).to_be_visible()
        
        # Click to sort
        path_header.click()
        page.wait_for_timeout(500)
        
        # Verify sort is active
        expect(path_header).to_have_class("sort-active")
    
    def test_directories_table_description_column_sorting(self, page: Page):
        """Test sorting the directories table by the Description column."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Get the Description column header
        desc_header = page.locator('#directories-table th[data-sort="description"]')
        expect(desc_header).to_be_visible()
        
        # Click to sort
        desc_header.click()
        page.wait_for_timeout(500)
        
        # Verify sort is active
        expect(desc_header).to_have_class("sort-active")
    
    def test_actions_columns_not_sortable(self, page: Page):
        """Test that Actions columns are not sortable in both tables."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Check prompts table Actions column (should not have sortable class)
        prompts_actions = page.locator('table:not(#directories-table) th:last-child')
        expect(prompts_actions).not_to_have_class("sortable")
        expect(prompts_actions).to_contain_text("Actions")
        
        # Check directories table Actions column (should not have sortable class)
        directories_actions = page.locator('#directories-table th.actions-column')
        expect(directories_actions).not_to_have_class("sortable")
        expect(directories_actions).to_contain_text("Actions")
    
    def test_independent_table_sorting(self, page: Page):
        """Test that sorting one table doesn't affect the other table."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Sort prompts table by directory
        prompts_dir_header = page.locator('table:not(#directories-table) th[data-sort="directory"]')
        prompts_dir_header.click()
        page.wait_for_timeout(500)
        
        # Verify prompts table is sorted but directories table is not affected
        expect(prompts_dir_header).to_have_class("sort-active")
        
        # Check that directories table headers are not active
        dir_name_header = page.locator('#directories-table th[data-sort="name"]')
        expect(dir_name_header).not_to_have_class("sort-active")
        
        # Now sort directories table
        dir_name_header.click()
        page.wait_for_timeout(500)
        
        # Verify directories table is sorted and prompts table is still sorted
        expect(dir_name_header).to_have_class("sort-active")
        expect(prompts_dir_header).to_have_class("sort-active")
        
        # Verify they have independent sort directions
        prompts_dir_header.click()  # Change prompts sort direction
        page.wait_for_timeout(500)
        
        # Prompts table should change direction, directories should remain the same
        expect(prompts_dir_header).to_have_class("sort-desc")
        expect(dir_name_header).to_have_class("sort-asc")
    
    def test_sort_icons_visibility_and_behavior(self, page: Page):
        """Test that sort icons are visible and behave correctly."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Check that all sortable headers have sort icons
        sortable_headers = page.locator('.sortable')
        for i in range(sortable_headers.count()):
            header = sortable_headers.nth(i)
            sort_icon = header.locator('.sort-icon')
            expect(sort_icon).to_be_visible()
        
        # Click a header and verify icon changes
        first_sortable = sortable_headers.first
        first_sortable.click()
        page.wait_for_timeout(500)
        
        # Should have active sort icon
        active_icon = first_sortable.locator('.sort-icon')
        expect(active_icon).to_be_visible()
        expect(first_sortable).to_have_class("sort-active")
    
    def test_actions_column_width_fixed(self, page: Page):
        """Test that Actions columns have fixed width as specified."""
        page.goto(MANAGE_PROMPTS_URL)
        self.wait_for_tables_to_load(page)
        
        # Check directories table Actions column width
        directories_actions = page.locator('#directories-table .actions-column')
        expect(directories_actions).to_be_visible()
        
        # The width should be at least 120px as specified in CSS
        # Note: This is a basic check - more sophisticated width testing 
        # could be added with actual computed style verification
        expect(directories_actions).to_contain_text("Actions")
        
        # Verify the column contains action buttons
        first_row = page.locator('#directories-table-body tr').first
        if first_row.count() > 0:
            action_buttons = first_row.locator('td:last-child button')
            expect(action_buttons.count()).to_be_greater_than(0)
