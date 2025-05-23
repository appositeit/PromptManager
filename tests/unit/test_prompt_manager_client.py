import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mcp_server/src')))

import pytest
from unittest.mock import AsyncMock, patch
from prompt_manager_client import PromptManagerClient, PromptManagerClientError

@pytest.mark.asyncio
async def test_fuzzy_directory_match_exact():
    client = PromptManagerClient()
    directories = [
        {"name": "Alpha", "path": "/alpha"},
        {"name": "Beta", "path": "/beta"},
    ]
    with patch.object(client, 'list_all_directories', AsyncMock(return_value=directories)):
        result = await client.fuzzy_directory_match("Alpha")
        assert result == "/alpha"

@pytest.mark.asyncio
async def test_fuzzy_directory_match_fuzzy_name():
    client = PromptManagerClient()
    directories = [
        {"name": "Alpha", "path": "/alpha"},
        {"name": "Beta", "path": "/beta"},
    ]
    with patch.object(client, 'list_all_directories', AsyncMock(return_value=directories)):
        result = await client.fuzzy_directory_match("Alph")
        assert result == "/alpha"

@pytest.mark.asyncio
async def test_fuzzy_directory_match_fuzzy_path():
    client = PromptManagerClient()
    directories = [
        {"name": "Alpha", "path": "/alpha"},
        {"name": "Beta", "path": "/beta"},
    ]
    with patch.object(client, 'list_all_directories', AsyncMock(return_value=directories)):
        result = await client.fuzzy_directory_match("/alp")
        assert result == "/alpha"

@pytest.mark.asyncio
async def test_fuzzy_directory_match_no_match():
    client = PromptManagerClient()
    directories = [
        {"name": "Alpha", "path": "/alpha"},
        {"name": "Beta", "path": "/beta"},
    ]
    with patch.object(client, 'list_all_directories', AsyncMock(return_value=directories)):
        with pytest.raises(PromptManagerClientError):
            await client.fuzzy_directory_match("Gamma")

@pytest.mark.asyncio
async def test_fuzzy_directory_match_case_insensitive():
    client = PromptManagerClient()
    directories = [
        {"name": "Alpha", "path": "/alpha"},
        {"name": "Beta", "path": "/beta"},
    ]
    with patch.object(client, 'list_all_directories', AsyncMock(return_value=directories)):
        result = await client.fuzzy_directory_match("alpha")
        assert result == "/alpha"

@pytest.mark.asyncio
async def test_fuzzy_directory_match_multiple_best():
    client = PromptManagerClient()
    directories = [
        {"name": "Alpha", "path": "/alpha"},
        {"name": "Alphabeta", "path": "/alphabeta"},
    ]
    with patch.object(client, 'list_all_directories', AsyncMock(return_value=directories)):
        result = await client.fuzzy_directory_match("Alph")
        # Should pick the closest match (implementation-dependent, but should not error)
        assert result in ["/alpha", "/alphabeta"] 