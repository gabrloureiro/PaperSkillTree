import json
import asyncio
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types
from src.core.config import Config

class LLMService:
    def __init__(self, model_name: Optional[str] = None, temperature: Optional[float] = None, api_key: Optional[str] = None):
        self.model_name = model_name or Config.MODEL_NAME
        self.temperature = temperature if temperature is not None else Config.TEMPERATURE
        self.api_key = api_key or Config.GOOGLE_API_KEY
        self._client = None
        # Limit concurrency to 12 simultaneous requests
        self._semaphore = asyncio.Semaphore(12)

    @property
    def client(self):
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def get_system_instruction(self, role: str, schema_model: Type[BaseModel]) -> str:
        schema_str = json.dumps(schema_model.model_json_schema(), indent=2)
        return (
            f"You are the {role}. Your sole function is to analyze the input and output "
            f"a raw JSON object strictly adhering to this schema:\n{schema_str}\n"
            f"Do not include markdown formatting, conversational filler, or hallucinated claims; "
            f"any deviation causes immediate pipeline failure."
        )

    async def generate_json(self, system_instruction: str, prompt: str, schema_model: Type[BaseModel]) -> Dict[str, Any]:
        async with self._semaphore:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=self.temperature,
                    response_mime_type="application/json",
                    response_schema=schema_model,
                )
            )
            
            if hasattr(response.parsed, "model_dump"):
                return response.parsed.model_dump()
            return response.parsed
