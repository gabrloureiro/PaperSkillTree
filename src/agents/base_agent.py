import json
from typing import Dict, Any, List, Type
from pydantic import BaseModel
from src.services.llm_service import LLMService
from src.models.schemas import ValidatorOutputModel, AuditedResponseModel

class BaseAgent:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def _audit_response(self, draft_response: str, raw_text: str) -> str:
        """Audits a draft response against raw text, and rewrites it if hallucinations are found."""
        # 1. Validation
        validator_prompt = (
            f"Compare the Draft Response strictly against the raw source text. Flag any claim not explicitly supported.\n"
            f"Draft Response:\n{draft_response}\n\n"
            f"Source Text:\n{raw_text}"
        )
        validator_system = self.llm_service.get_system_instruction("Validator", ValidatorOutputModel)
        validator_system += (
            "\nSpecific instruction: You are a hostile reviewer. Your only goal is to find claims in the Draft "
            "that are not explicitly stated in the Source Text. You do not care about readability; you care only "
            "about factual grounding."
        )
        
        validation_result = self.llm_service.generate_json(validator_system, validator_prompt, ValidatorOutputModel)
        
        if validation_result.get("is_valid", False):
            return draft_response
            
        # 2. Resolution
        resolution_prompt = (
            f"Rewrite the draft response to strictly remove flags raised by the Validator.\n"
            f"Keep the tone conversational but factual. Maximum 3 sentences.\n"
            f"Original Draft:\n{draft_response}\n\n"
            f"Validator Critique:\n{json.dumps(validation_result.get('hallucination_flags', []), indent=2)}\n\n"
            f"Source Text:\n{raw_text}"
        )
        resolution_system = self.llm_service.get_system_instruction("Resolution", AuditedResponseModel)
        resolution_result = self.llm_service.generate_json(resolution_system, resolution_prompt, AuditedResponseModel)
        
        return resolution_result.get("response", draft_response)
