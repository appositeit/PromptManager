#!/usr/bin/env python3
"""
Manual cleanup script for test artifacts.
Run this to clean up any test files that may have been left behind.
"""

import os
import glob
import sys
from pathlib import Path

# Test directory
TEST_PROMPTS_DIR = "/mnt/data/jem/development/prompt_manager/tests/test_prompts"

def cleanup_test_artifacts():
    """Clean up all test artifacts."""
    print("🧹 Cleaning up test artifacts...")
    
    if not os.path.exists(TEST_PROMPTS_DIR):
        print(f"❌ Test directory not found: {TEST_PROMPTS_DIR}")
        return False
    
    # Permanent test fixtures that should NOT be deleted
    permanent_fixtures = {
        'simple_test.md',
        'test_composite.md', 
        'tagged_test.md',
        'dependency_test.md',
        'included_text.md'
    }
    
    # Patterns for test artifacts
    test_patterns = [
        f"{TEST_PROMPTS_DIR}/test_api_prompt*.md",
        f"{TEST_PROMPTS_DIR}/test_update_prompt*.md", 
        f"{TEST_PROMPTS_DIR}/test_delete_prompt*.md",
        f"{TEST_PROMPTS_DIR}/test_rename_*.md",
        f"{TEST_PROMPTS_DIR}/test_large_content*.md",
        f"{TEST_PROMPTS_DIR}/test_route_prompt*.md",
        f"{TEST_PROMPTS_DIR}/test-with-*.md",
        f"{TEST_PROMPTS_DIR}/test_with_*.md",
        f"{TEST_PROMPTS_DIR}/test.with.*.md",
        f"{TEST_PROMPTS_DIR}/integration_test_prompt*.md",
    ]
    
    files_deleted = 0
    errors = []
    
    for pattern in test_patterns:
        for filepath in glob.glob(pattern):
            filename = os.path.basename(filepath)
            
            # Skip permanent fixtures
            if filename in permanent_fixtures:
                print(f"⏭️  Skipping permanent fixture: {filename}")
                continue
                
            try:
                os.remove(filepath)
                print(f"🗑️  Deleted: {filename}")
                files_deleted += 1
            except Exception as e:
                error_msg = f"Error deleting {filename}: {e}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
    
    # Also look for any other test files (more aggressive cleanup)
    all_md_files = glob.glob(f"{TEST_PROMPTS_DIR}/*.md")
    for filepath in all_md_files:
        filename = os.path.basename(filepath)
        
        # Skip permanent fixtures
        if filename in permanent_fixtures:
            continue
            
        # Check if it looks like a test artifact
        test_indicators = [
            'test_api', 'test_update', 'test_delete', 'test_rename',
            'test_large', 'test_route', 'test-with', 'test_with',
            'test.with', 'integration_test'
        ]
        
        if any(indicator in filename for indicator in test_indicators):
            try:
                os.remove(filepath)
                print(f"🗑️  Deleted test artifact: {filename}")
                files_deleted += 1
            except Exception as e:
                error_msg = f"Error deleting {filename}: {e}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
    
    print(f"\n📊 Summary:")
    print(f"   Files deleted: {files_deleted}")
    print(f"   Errors: {len(errors)}")
    
    if errors:
        print(f"\n❌ Errors encountered:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print(f"✅ Cleanup completed successfully!")
        return True


def list_current_files():
    """List current files in the test directory."""
    print(f"📁 Current files in {TEST_PROMPTS_DIR}:")
    
    if not os.path.exists(TEST_PROMPTS_DIR):
        print(f"❌ Directory not found: {TEST_PROMPTS_DIR}")
        return
    
    md_files = glob.glob(f"{TEST_PROMPTS_DIR}/*.md")
    if not md_files:
        print("   (no .md files found)")
        return
        
    permanent_fixtures = {
        'simple_test.md', 'test_composite.md', 'tagged_test.md',
        'dependency_test.md', 'included_text.md'
    }
    
    for filepath in sorted(md_files):
        filename = os.path.basename(filepath)
        if filename in permanent_fixtures:
            print(f"   📌 {filename} (permanent fixture)")
        else:
            print(f"   📄 {filename}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_current_files()
    else:
        print("Test Cleanup Script")
        print("==================")
        print()
        
        list_current_files()
        print()
        
        cleanup_success = cleanup_test_artifacts()
        
        print()
        list_current_files()
        
        sys.exit(0 if cleanup_success else 1)
