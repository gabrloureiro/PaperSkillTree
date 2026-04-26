import json
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types

class LLMService:
    def __init__(self, model_name: str = "gemini-3.1-pro", temperature: float = 0.0):
        self.model_name = model_name
        self.temperature = temperature
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = genai.Client()
        return self._client

    def get_system_instruction(self, role: str, schema_model: Type[BaseModel]) -> str:
        schema_str = json.dumps(schema_model.model_json_schema(), indent=2)
        return (
            f"You are the {role}. Your sole function is to analyze the input and output "
            f"a raw JSON object strictly adhering to this schema:\n{schema_str}\n"
            f"Do not include markdown formatting, conversational filler, or hallucinated claims; "
            f"any deviation causes immediate pipeline failure."
        )

    def generate_json(self, system_instruction: str, prompt: str, schema_model: Type[BaseModel]) -> Dict[str, Any]:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=self.temperature,
                response_mime_type="application/json",
                response_schema=schema_model,
            )
        )
        # Use model_dump() if it's a Pydantic model returned by response.parsed
        # If response.parsed is already a dict, return it.
        if hasattr(response.parsed, "model_dump"):
            return response.parsed.model_dump()
        return response.parsed
