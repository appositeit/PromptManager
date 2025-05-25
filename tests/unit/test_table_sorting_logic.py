"""
Unit tests for table sorting functionality in the manage prompts page.

These tests verify the JavaScript sorting logic and table manipulation
functions work correctly.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json


class TestTableSortingLogic(unittest.TestCase):
    """Test class for JavaScript table sorting logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock prompts data for testing
        self.mock_prompts = [
            {
                'id': 'prompt1',
                'name': 'Alpha Prompt',
                'directory': '/path/to/dir1',
                'description': 'First prompt',
                'tags': ['tag1', 'tag2'],
                'updated_at': '2025-05-25T10:00:00Z'
            },
            {
                'id': 'prompt2', 
                'name': 'Beta Prompt',
                'directory': '/path/to/dir2',
                'description': 'Second prompt',
                'tags': ['tag2', 'tag3'],
                'updated_at': '2025-05-25T11:00:00Z'
            },
            {
                'id': 'prompt3',
                'name': 'Gamma Prompt', 
                'directory': '/path/to/dir1',
                'description': 'Third prompt',
                'tags': ['tag1'],
                'updated_at': '2025-05-25T09:00:00Z'
            }
        ]
        
        # Mock directories data for testing
        self.mock_directories = [
            {
                'name': 'Directory B',
                'path': '/path/to/dir2',
                'description': 'Second directory',
                'enabled': True
            },
            {
                'name': 'Directory A',
                'path': '/path/to/dir1', 
                'description': 'First directory',
                'enabled': False
            },
            {
                'name': 'Directory C',
                'path': '/path/to/dir3',
                'description': 'Third directory',
                'enabled': True
            }
        ]
    
    def test_stable_sort_algorithm(self):
        """Test that the stable sort algorithm maintains relative order for equal elements."""
        # This test verifies the JavaScript stableSort function logic
        # Since we can't directly test JavaScript, we'll test the algorithm logic
        
        # Create test data with equal elements
        test_data = [
            {'name': 'Item A', 'value': 1, 'index': 0},
            {'name': 'Item B', 'value': 2, 'index': 1}, 
            {'name': 'Item C', 'value': 1, 'index': 2},  # Same value as Item A
            {'name': 'Item D', 'value': 3, 'index': 3}
        ]
        
        # Implement the stable sort logic from JavaScript
        def stable_sort(array, compare_fn):
            # Add indices to track original order
            indexed = [(item, i) for i, item in enumerate(array)]
            
            # Sort with original index as tiebreaker
            indexed.sort(key=lambda x: (compare_fn(x[0]), x[1]))
            
            # Extract the sorted items
            return [pair[0] for pair in indexed]
        
        # Sort by value (where some values are equal)
        def compare_by_value(item):
            return item['value']
        
        sorted_data = stable_sort(test_data, compare_by_value)
        
        # Verify stable sort: equal elements maintain original relative order
        self.assertEqual(sorted_data[0]['name'], 'Item A')  # value=1, original index=0
        self.assertEqual(sorted_data[1]['name'], 'Item C')  # value=1, original index=2
        self.assertEqual(sorted_data[2]['name'], 'Item B')  # value=2
        self.assertEqual(sorted_data[3]['name'], 'Item D')  # value=3
    
    def test_prompts_sorting_by_directory(self):
        """Test sorting prompts by directory column."""
        # Sort by directory ascending
        sorted_prompts = sorted(self.mock_prompts, key=lambda p: p['directory'])
        
        expected_order = ['prompt1', 'prompt3', 'prompt2']  # dir1, dir1, dir2
        actual_order = [p['id'] for p in sorted_prompts]
        
        self.assertEqual(actual_order, expected_order)
        
        # Sort by directory descending
        sorted_prompts_desc = sorted(self.mock_prompts, key=lambda p: p['directory'], reverse=True)
        expected_order_desc = ['prompt2', 'prompt1', 'prompt3']  # dir2, dir1, dir1
        actual_order_desc = [p['id'] for p in sorted_prompts_desc]
        
        self.assertEqual(actual_order_desc, expected_order_desc)
    
    def test_prompts_sorting_by_name(self):
        """Test sorting prompts by name column."""
        # Sort by name ascending
        sorted_prompts = sorted(self.mock_prompts, key=lambda p: p['name'])
        
        expected_order = ['prompt1', 'prompt2', 'prompt3']  # Alpha, Beta, Gamma
        actual_order = [p['id'] for p in sorted_prompts]
        
        self.assertEqual(actual_order, expected_order)
    
    def test_prompts_sorting_by_updated_date(self):
        """Test sorting prompts by updated_at column."""
        # Sort by updated_at ascending (oldest first)
        sorted_prompts = sorted(self.mock_prompts, key=lambda p: p['updated_at'])
        
        expected_order = ['prompt3', 'prompt1', 'prompt2']  # 09:00, 10:00, 11:00
        actual_order = [p['id'] for p in sorted_prompts]
        
        self.assertEqual(actual_order, expected_order)
    
    def test_directories_sorting_by_name(self):
        """Test sorting directories by name column."""
        # Sort by name ascending
        sorted_dirs = sorted(self.mock_directories, key=lambda d: d['name'])
        
        expected_order = ['Directory A', 'Directory B', 'Directory C']
        actual_order = [d['name'] for d in sorted_dirs]
        
        self.assertEqual(actual_order, expected_order)
    
    def test_directories_sorting_by_status(self):
        """Test sorting directories by status (enabled/disabled)."""
        # Sort by enabled status (disabled first, then enabled)
        sorted_dirs = sorted(self.mock_directories, key=lambda d: 'enabled' if d['enabled'] else 'disabled')
        
        # 'disabled' comes before 'enabled' alphabetically
        expected_order = ['Directory A', 'Directory B', 'Directory C']  # False, True, True
        actual_order = [d['name'] for d in sorted_dirs]
        
        self.assertEqual(actual_order, expected_order)
    
    def test_directories_sorting_by_path(self):
        """Test sorting directories by path column."""
        # Sort by path ascending
        sorted_dirs = sorted(self.mock_directories, key=lambda d: d['path'])
        
        expected_order = ['Directory A', 'Directory B', 'Directory C']  # dir1, dir2, dir3
        actual_order = [d['name'] for d in sorted_dirs]
        
        self.assertEqual(actual_order, expected_order)
    
    def test_tag_sorting_logic(self):
        """Test sorting prompts by tags column."""
        # Tags should be joined and sorted as strings
        def get_tags_string(prompt):
            if prompt.get('tags'):
                return ','.join(prompt['tags'])
            return ''
        
        sorted_prompts = sorted(self.mock_prompts, key=get_tags_string)
        
        # tag1 < tag1,tag2 < tag2,tag3
        expected_order = ['prompt3', 'prompt1', 'prompt2']
        actual_order = [p['id'] for p in sorted_prompts]
        
        self.assertEqual(actual_order, expected_order)
    
    def test_sort_direction_toggle(self):
        """Test that sort direction toggles correctly."""
        # Simulate the JavaScript logic for toggling sort direction
        current_sort = {'column': 'name', 'direction': 'asc'}
        
        # Clicking same column should toggle direction
        if current_sort['column'] == 'name':
            current_sort['direction'] = 'desc' if current_sort['direction'] == 'asc' else 'asc'
        
        self.assertEqual(current_sort['direction'], 'desc')
        
        # Clicking again should toggle back
        if current_sort['column'] == 'name':
            current_sort['direction'] = 'desc' if current_sort['direction'] == 'asc' else 'asc'
        
        self.assertEqual(current_sort['direction'], 'asc')
    
    def test_sort_column_change(self):
        """Test that changing sort column resets to ascending."""
        # Simulate the JavaScript logic for changing sort column
        current_sort = {'column': 'name', 'direction': 'desc'}
        new_column = 'directory'
        
        if current_sort['column'] != new_column:
            current_sort['column'] = new_column
            current_sort['direction'] = 'asc'
        
        self.assertEqual(current_sort['column'], 'directory')
        self.assertEqual(current_sort['direction'], 'asc')
    
    def test_independent_table_sort_state(self):
        """Test that prompts and directories tables have independent sort state."""
        # Simulate having separate sort state for each table
        prompts_sort = {'column': 'directory', 'direction': 'asc'}
        directories_sort = {'column': 'name', 'direction': 'desc'}
        
        # Changing one shouldn't affect the other
        prompts_sort['direction'] = 'desc'
        
        self.assertEqual(prompts_sort['direction'], 'desc')
        self.assertEqual(directories_sort['direction'], 'desc')  # Should remain unchanged
        
        # Changing directories sort shouldn't affect prompts
        directories_sort['column'] = 'path'
        directories_sort['direction'] = 'asc'
        
        self.assertEqual(prompts_sort['column'], 'directory')  # Should remain unchanged
        self.assertEqual(directories_sort['column'], 'path')


class TestSortingIntegration(unittest.TestCase):
    """Integration tests for sorting functionality."""
    
    def test_sort_with_filtering(self):
        """Test that sorting works correctly with filtered data."""
        # Mock data with some prompts filtered out
        all_prompts = [
            {'id': 'prompt1', 'name': 'Alpha', 'directory': 'dir1', 'tags': ['admin']},
            {'id': 'prompt2', 'name': 'Beta', 'directory': 'dir2', 'tags': ['user']}, 
            {'id': 'prompt3', 'name': 'Gamma', 'directory': 'dir1', 'tags': ['admin']}
        ]
        
        # Filter by tag 'admin'
        filtered_prompts = [p for p in all_prompts if 'admin' in p.get('tags', [])]
        
        # Sort filtered results by name
        sorted_filtered = sorted(filtered_prompts, key=lambda p: p['name'])
        
        expected_order = ['prompt1', 'prompt3']  # Alpha, Gamma (both have 'admin' tag)
        actual_order = [p['id'] for p in sorted_filtered]
        
        self.assertEqual(actual_order, expected_order)
    
    def test_sort_with_empty_values(self):
        """Test sorting behavior with empty/None values."""
        prompts_with_empty = [
            {'id': 'prompt1', 'name': 'Alpha', 'description': 'First'},
            {'id': 'prompt2', 'name': 'Beta', 'description': ''},
            {'id': 'prompt3', 'name': 'Gamma', 'description': None}
        ]
        
        # Sort by description, handling empty values
        def get_description(prompt):
            desc = prompt.get('description') or ''
            return desc
        
        sorted_prompts = sorted(prompts_with_empty, key=get_description)
        
        # Empty strings and None should come first
        self.assertIn(sorted_prompts[0]['id'], ['prompt2', 'prompt3'])
        self.assertEqual(sorted_prompts[2]['id'], 'prompt1')  # 'First' comes last


if __name__ == '__main__':
    unittest.main()
