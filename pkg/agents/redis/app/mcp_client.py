import os
import sys
import asyncio
from typing import List, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class RedisMCPClient:
    def __init__(self):
        # Determine script command
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        server_script = os.path.join(base_dir, "app", "mcp_server.py")
        
        # We start the server script directly via python
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script],
            env=os.environ.copy()
        )
        self._session = None
        self._client_context = None

    async def __aenter__(self):
        self._client_context = stdio_client(self.server_params)
        read_stream, write_stream = await self._client_context.__aenter__()
        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
        if self._client_context:
            await self._client_context.__aexit__(exc_type, exc_val, exc_tb)

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools on the MCP server."""
        if not self._session:
            raise RuntimeError("MCP Client session not started. Use 'async with' context manager.")
        response = await self._session.list_tools()
        # The response holds a list of tools. Each tool has name, description, inputSchema.
        # We convert the Tool objects to a serializable dictionary format for the LLM
        tools_list = []
        for t in response.tools:
            tools_list.append({
                "name": t.name,
                "description": t.description,
                "inputSchema": t.inputSchema
            })
        return tools_list

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a specific tool on the MCP server."""
        if not self._session:
            raise RuntimeError("MCP Client session not started. Use 'async with' context manager.")
        response = await self._session.call_tool(tool_name, arguments)
        # Combine text content from the response
        results = []
        for content in response.content:
            if hasattr(content, "text"):
                results.append(content.text)
            elif isinstance(content, dict) and "text" in content:
                results.append(content["text"])
        return "\n".join(results)
