from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLM(ABC):
    @abstractmethod
    def get_tool_calls(self, question: str, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Determines which tools to call based on the user's question.
        Returns a list of dictionaries, each containing 'name' and 'arguments'.
        """
        pass

    @abstractmethod
    def generate_answer(self, question: str, tool_result: str) -> str:
        """
        Generates the final human-readable answer from the question and tool execution output.
        """
        pass
