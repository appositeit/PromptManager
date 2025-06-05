"""
Test cleanup utilities to ensure all test files are properly deleted.
"""

import os
import glob
import asyncio
import httpx
from pathlib import Path
from typing import List, Set
import pytest


class TestCleanupManager:
    """Manages cleanup of test files created during integration tests."""
    
    def __init__(self, test_prompts_dir: str = None):
        self.test_prompts_dir = test_prompts_dir or "/mnt/data/jem/development/prompt_manager/tests/test_prompts"
        self.created_files: Set[str] = set()
        self.created_prompts: Set[str] = set()
        
    def register_file(self, filepath: str):
        """Register a file that should be cleaned up."""
        self.created_files.add(filepath)
        
    def register_prompt(self, prompt_id: str):
        """Register a prompt that should be cleaned up via API."""
        self.created_prompts.add(prompt_id)
        
    async def cleanup_via_api(self, base_url: str = "http://localhost:8095/api"):
        """Clean up prompts via API calls."""
        cleanup_errors = []
        
        if not self.created_prompts:
            return cleanup_errors
            
        async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
            for prompt_id in self.created_prompts:
                try:
                    response = await client.delete(f"/prompts/{prompt_id}")
                    if response.status_code not in [200, 404]:  # 404 is OK (already deleted)
                        cleanup_errors.append(f"Failed to delete prompt {prompt_id}: {response.status_code}")
                except Exception as e:
                    cleanup_errors.append(f"Error deleting prompt {prompt_id}: {str(e)}")
                    
        return cleanup_errors
        
    def cleanup_filesystem(self):
        """Clean up files directly from filesystem."""
        cleanup_errors = []
        
        # Clean up registered files
        for filepath in self.created_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                cleanup_errors.append(f"Error deleting file {filepath}: {str(e)}")
                
        # Clean up any test files that match common test patterns
        test_patterns = [
            f"{self.test_prompts_dir}/test_*.md",
            f"{self.test_prompts_dir}/*_test*.md",
        ]
        
        for pattern in test_patterns:
            for filepath in glob.glob(pattern):
                # Only delete files that look like test files (not permanent test fixtures)
                if self._is_test_artifact(filepath):
                    try:
                        os.remove(filepath)
                    except Exception as e:
                        cleanup_errors.append(f"Error deleting test artifact {filepath}: {str(e)}")
                        
        return cleanup_errors
        
    def _is_test_artifact(self, filepath: str) -> bool:
        """Determine if a file is a test artifact that should be cleaned up."""
        filename = os.path.basename(filepath)
        
        # Don't delete permanent test fixtures
        permanent_fixtures = {
            'simple_test.md',
            'test_composite.md', 
            'tagged_test.md',
            'dependency_test.md',
            'included_text.md'
        }
        
        if filename in permanent_fixtures:
            return False
            
        # Delete files that match test patterns
        test_indicators = [
            'test_api_prompt',
            'test_update_prompt',
            'test_delete_prompt', 
            'test_rename_',
            'test_large_content',
            'test_route_prompt',
            'test-with-',
            'test_with_',
            'test.with.',
            'integration_test_prompt'
        ]
        
        return any(indicator in filename for indicator in test_indicators)
        
    async def full_cleanup(self, base_url: str = "http://localhost:8095/api"):
        """Perform both API and filesystem cleanup."""
        api_errors = await self.cleanup_via_api(base_url)
        fs_errors = self.cleanup_filesystem()
        
        all_errors = api_errors + fs_errors
        
        # Clear the registered items
        self.created_files.clear()
        self.created_prompts.clear()
        
        return all_errors


@pytest.fixture(scope="function")
def cleanup_manager():
    """Provide a cleanup manager for each test function."""
    manager = TestCleanupManager()
    yield manager
    
    # Cleanup after the test
    errors = manager.cleanup_filesystem()
    if errors:
        print(f"Cleanup warnings: {errors}")


@pytest.fixture(scope="function") 
async def async_cleanup_manager():
    """Provide an async cleanup manager for each test function."""
    manager = TestCleanupManager()
    yield manager
    
    # Cleanup after the test
    errors = await manager.full_cleanup()
    if errors:
        print(f"Cleanup warnings: {errors}")


@pytest.fixture(scope="class")
def class_cleanup_manager():
    """Provide a cleanup manager for each test class."""
    manager = TestCleanupManager()
    yield manager
    
    # Cleanup after all tests in the class
    errors = manager.cleanup_filesystem()
    if errors:
        print(f"Class cleanup warnings: {errors}")


def cleanup_all_test_artifacts():
    """Clean up all test artifacts - useful for manual cleanup."""
    manager = TestCleanupManager()
    errors = manager.cleanup_filesystem()
    return errors


async def async_cleanup_all_test_artifacts():
    """Async version of cleanup_all_test_artifacts."""
    manager = TestCleanupManager()
    errors = await manager.full_cleanup()
    return errors


if __name__ == "__main__":
    # Manual cleanup script
    print("🧹 Cleaning up all test artifacts...")
    errors = cleanup_all_test_artifacts()
    
    if errors:
        print(f"❌ Cleanup completed with warnings:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Cleanup completed successfully!")
