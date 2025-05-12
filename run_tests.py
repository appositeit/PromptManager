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


def discover_and_run_tests():
    """Discover and run all tests."""
    # Discover tests in the tests directory
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return success/failure
    return result.wasSuccessful()


if __name__ == "__main__":
    setup_environment()
    success = discover_and_run_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
