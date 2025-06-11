"""
MCP Server for Prompt Manager.

This module provides a Model Context Protocol (MCP) server that exposes
prompt management functionality to MCP clients.
"""

from .server import PromptManagerMCPServer

__all__ = ['PromptManagerMCPServer']
