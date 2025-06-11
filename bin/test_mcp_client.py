#!/usr/bin/env python3
"""
Simple test client for the Prompt Manager MCP Server.

AI-generated on 2025-06-07
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


async def test_mcp_server(host='localhost', port=8083):
    """Test the MCP server functionality."""
    print(f"Connecting to MCP server at {host}:{port}...")
    
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print("✓ Connected to MCP server")
        
        # Test 1: Initialize
        print("\n1. Testing initialization...")
        request = {
            'id': '1',
            'jsonrpc': '2.0',
            'method': 'initialize',
            'params': {}
        }
        await send_request(writer, request)
        response = await read_response(reader)
        print(f"Initialize response: {response}")
        
        # Test 2: List tools
        print("\n2. Testing tools list...")
        request = {
            'id': '2',
            'jsonrpc': '2.0',
            'method': 'tools/list',
            'params': {}
        }
        await send_request(writer, request)
        response = await read_response(reader)
        print(f"Tools list: {len(response.get('result', {}).get('tools', []))} tools found")
        
        # Test 3: List prompts
        print("\n3. Testing list prompts...")
        request = {
            'id': '3',
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'params': {
                'name': 'list_prompts',
                'arguments': {}
            }
        }
        await send_request(writer, request)
        response = await read_response(reader)
        prompts = response.get('result', {}).get('prompts', [])
        print(f"Found {len(prompts)} prompts")
        for prompt in prompts[:3]:  # Show first 3
            print(f"  - {prompt.get('id', 'unknown')} in {prompt.get('directory', 'unknown')}")
        
        # Test 4: Search prompts (if any exist)
        if prompts:
            print("\n4. Testing search prompts...")
            request = {
                'id': '4',
                'jsonrpc': '2.0',
                'method': 'tools/call',
                'params': {
                    'name': 'search_prompts',
                    'arguments': {
                        'query': 'test'
                    }
                }
            }
            await send_request(writer, request)
            response = await read_response(reader)
            search_results = response.get('result', {}).get('prompts', [])
            print(f"Search for 'test' found {len(search_results)} prompts")
        
        # Test 5: Ping
        print("\n5. Testing ping...")
        request = {
            'id': '5',
            'jsonrpc': '2.0',
            'method': 'ping',
            'params': {}
        }
        await send_request(writer, request)
        response = await read_response(reader)
        print(f"Ping response: {response.get('result', {})}")
        
        print("\n✓ All tests completed successfully!")
        
    except ConnectionRefusedError:
        print(f"✗ Connection refused - is the MCP server running on {host}:{port}?")
        print("Try running: ./bin/start_mcp_server.sh")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass
    
    return True


async def send_request(writer, request):
    """Send a JSON-RPC request."""
    message = json.dumps(request) + '\n'
    writer.write(message.encode())
    await writer.drain()


async def read_response(reader):
    """Read a JSON-RPC response."""
    data = await reader.readline()
    if not data:
        raise ConnectionError("Connection closed")
    return json.loads(data.decode().strip())


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test the Prompt Manager MCP Server')
    parser.add_argument('--host', default='localhost', help='MCP server host')
    parser.add_argument('--port', type=int, default=8083, help='MCP server port')
    
    args = parser.parse_args()
    
    success = await test_mcp_server(args.host, args.port)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    asyncio.run(main())
