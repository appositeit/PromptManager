#!/usr/bin/env python3
"""
Script to run all tests for the prompt manager.
"""

import os
import sys
import unittest


def setup_environment():
    """Set up the environment for tests."""
    # Add the project root to the Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Ensure pytest is installed
    try:
        pass  # Pytest is used in the subprocess call
    except ImportError:
        print("Installing pytest and pytest-asyncio...")
        os.system(f"{sys.executable} -m pip install pytest pytest-asyncio websockets httpx")


def discover_and_run_tests():
    """Discover and run all tests."""
    import pytest
    
    # First run unittest-based tests
    print("Running unittest-based tests...")
    test_loader = unittest.TestLoader()
    
    # Discover non-websocket tests
    test_pattern = "test_*.py"
    test_suite = test_loader.discover('tests', pattern=test_pattern)
    
    # Filter out websocket tests
    filtered_suite = unittest.TestSuite()
    for suite in test_suite:
        for test_case in suite:
            if not str(test_case).lower().find('websocket') >= 0:
                filtered_suite.addTest(test_case)
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    unittest_result = test_runner.run(filtered_suite)
    
    # Then run pytest-based tests for WebSocket
    print("\nRunning pytest-based WebSocket tests...")
    pytest_args = [
        "-xvs",
        "tests/unit/test_websocket_*.py",
        "tests/unit/test_websocket_*.py"
    ]
    pytest_result = pytest.main(pytest_args)
    
    # Return success only if both test suites passed
    return unittest_result.wasSuccessful() and pytest_result == 0


if __name__ == "__main__":
    setup_environment()
    success = discover_and_run_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
