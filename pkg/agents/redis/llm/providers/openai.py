import json
from typing import List, Dict, Any, Optional
from llm.base import BaseLLM

class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", base_url: Optional[str] = None):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def get_tool_calls(self, question: str, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted_tools = []
        for t in tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["inputSchema"]
                }
            })

        system_prompt = (
            "You are an expert Redis administrator assistant. Based on the user's question, "
            "select the most relevant tool(s) to run. If multiple tools are needed to get the required "
            "data, you can call multiple tools. If no tools are required, do not call any tool.\n"
            "GUIDELINES:\n"
            "- User queries will often refer to keys by short IDs or relative names. Match these against the "
            "'Discovered database key schema patterns' (which group keys by namespace prefix patterns, e.g. 'namespace:sub_namespace:*') "
            "and construct the fully qualified Redis key by applying the correct prefix namespace before querying.\n"
            "- Dedicated Redis tools (e.g., get, hgetall, smembers, lrange, zrange, xrange) should always be preferred over fallback tools.\n"
            "- The 'execute_readonly_command' fallback tool should ONLY be used when no dedicated Redis MCP tool exists for the requested operation.\n"
            "- You must NEVER invent or hallucinate tool names. Choose ONLY from the provided list.\n"
            "- You must NEVER attempt write operations through the 'execute_readonly_command' fallback tool; it only supports read-only commands."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=formatted_tools if formatted_tools else None,
            tool_choice="auto" if formatted_tools else None
        )

        message = response.choices[0].message
        results = []
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                results.append({
                    "name": tc.function.name,
                    "arguments": args
                })
        return results

    def generate_answer(self, question: str, tool_result: str) -> str:
        system_prompt = (
            "You are a helpful Redis Copilot. Summarize the tool result to answer the user's natural language question. "
            "Keep the response professional, clean, and directly answers the question based on the tool result."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}\nTool Result: {tool_result}"}
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content
