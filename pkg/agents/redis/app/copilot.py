import json
import asyncio
import time
from typing import Dict, Any, Optional
from app.mcp_client import RedisMCPClient
from llm.client import get_llm_client

class RedisCopilot:
    def __init__(self):
        self.llm = get_llm_client()

    async def ask(self, question: str) -> str:
        """
        Orchestrates the process of tool loading, selection, execution, and response generation.
        """
        async with RedisMCPClient() as mcp_client:
            # Step 1: Load tools
            tools = await mcp_client.list_tools()
            
            # Discover database key schema patterns to prevent LLM key guessing & type checks
            schema_info = {}
            try:
                schema_json = await mcp_client.execute_tool("discover_schema", {"limit": 1000})
                schema_info = json.loads(schema_json)
            except Exception:
                pass

            # Step 2: Send question and tools to LLM for tool calls
            augmented_question = f"Question: {question}\n\nDiscovered database key schema patterns:\n{json.dumps(schema_info, indent=2)}"
            tool_calls = self.llm.get_tool_calls(augmented_question, tools)
            
            tool_results = []
            if tool_calls:
                async def execute_and_log(tc):
                    tool_name = tc.get("name")
                    arguments = tc.get("arguments", {})
                    try:
                        result = await mcp_client.execute_tool(tool_name, arguments)
                        return f"[Tool: {tool_name}, Args: {arguments}]\nResult: {result}"
                    except Exception as e:
                        return f"[Tool: {tool_name}, Args: {arguments}]\nError: {e}"
                
                tasks = [execute_and_log(tc) for tc in tool_calls]
                tool_results = await asyncio.gather(*tasks)
                tool_result = "\n\n".join(tool_results)
            else:
                tool_result = "No tools were selected or executed to answer this question."

            # Step 4: Generate answer
            answer = self.llm.generate_answer(question, tool_result)
            return answer
