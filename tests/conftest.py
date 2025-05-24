import sys
import os
import asyncio
import pytest
import nest_asyncio

# Ensure src/ is on sys.path for all tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Session-scoped event loop for pytest-asyncio 0.21.x compatibility
@pytest.fixture(scope="session")
def event_loop():
    """
    Creates a session-scoped event loop with nest_asyncio support.
    
    This fixes "RuntimeError: This event loop is already running" errors
    by allowing nested event loops using nest_asyncio.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close() 