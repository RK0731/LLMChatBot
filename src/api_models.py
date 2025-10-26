from pydantic import BaseModel
from typing import Optional, List, Union

class SimpleChatQuery(BaseModel):
    """
    Simple chat with LLM agent (Shared memory, without RAG). This endpoint should only be used for testing.
    Attributes:
        query (str): The query to be sent to the LLM agent
    """
    query: str
    session_id: Optional[str] = None

class SimpleChatResponse(BaseModel):
    """
    Simplest chat response model
    Attributes:
        message (str): Response from simple chat endpoint
    """
    message: str
    session_id: Optional[str] = None