import json
import httpx
from typing import List, Dict, Any, Optional
from llm.base import BaseLLM

class OllamaLLM(BaseLLM):
    def __init__(self, api_key: str = "ollama", model: str = "llama3", base_url: str = "http://localhost:11434/v1"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        self.is_native_ollama = self.base_url.endswith("/api/chat")
        if self.is_native_ollama or self.base_url.endswith("/chat/completions"):
            self.url = self.base_url
        else:
            self.url = f"{self.base_url}/chat/completions"

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

        payload = {
            "model": self.model,
            "messages": messages,
            "tools": formatted_tools if formatted_tools else None,
            "tool_choice": "auto" if formatted_tools else None,
            "stream": False
        }

        try:
            response = httpx.post(self.url, json=payload, headers=self.headers, timeout=300.0)
            response.raise_for_status()
            data = response.json()
            
            if self.is_native_ollama:
                message = data.get("message", {})
            else:
                message = data.get("choices", [{}])[0].get("message", {})

            results = []
            if "tool_calls" in message and message["tool_calls"]:
                for tc in message["tool_calls"]:
                    func = tc["function"]
                    args_str = func.get("arguments", "{}")
                    if isinstance(args_str, str):
                        try:
                            args = json.loads(args_str)
                        except Exception:
                            args = {}
                    else:
                        args = args_str
                    results.append({
                        "name": func["name"],
                        "arguments": args
                    })
                return results
        except Exception as e:
            print(f"Error calling Ollama API: {e}")
        return []

    def generate_answer(self, question: str, tool_result: str) -> str:
        system_prompt = (
            "You are a helpful Redis Copilot. Summarize the tool result to answer the user's natural language question. "
            "Keep the response professional, clean, and directly answers the question based on the tool result."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}\nTool Result: {tool_result}"}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        try:
            response = httpx.post(self.url, json=payload, headers=self.headers, timeout=300.0)
            response.raise_for_status()
            data = response.json()
            
            if self.is_native_ollama:
                return data.get("message", {}).get("content", "")
            else:
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            return f"Error generating answer: {e}"
