import json
from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
from src.models.schemas import ExaminerResponseModel, TutorResponseModel

class ExaminerAgent(BaseAgent):
    async def interact(self, concept_name: str, explanation: str, raw_text: str, message: str, chat_history: List[Dict[str, str]], passing_grade: str = "B-") -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Examiner", ExaminerResponseModel)
        system_instruction += (
            "\nYou are a strict and thorough examiner. The user is trying to explain the concept. "
            "Assess if their explanation is accurate based on the Grounded Explanation. "
            "Grade the user's explanation on an A-F scale and provide it in `letter_grade`. "
            f"If they pass (grade {passing_grade} or higher), set `passed` to true. If they fail, set `passed` to false. "
            "Keep your response to a maximum of 3 sentences."
        )
        
        prompt = (
            f"Concept: {concept_name}\n"
            f"Grounded Explanation (Ground Truth):\n{explanation}\n\n"
            f"Chat History:\n{json.dumps(chat_history, indent=2)}\n\n"
            f"User Message:\n{message}"
        )
        
        result = await self.llm_service.generate_json(system_instruction, prompt, ExaminerResponseModel)
        
        if raw_text:
            result["response"] = await self._audit_response(result["response"], raw_text)
        
        return result

class TutorAgent(BaseAgent):
    async def interact(self, concept_name: str, explanation: str, raw_text: str, message: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Tutor", TutorResponseModel)
        system_instruction += (
            "\nYou are a direct and helpful tutor. Clarify the user's confusions about the concept based on the Grounded Explanation. "
            "Keep your response to a maximum of 3 sentences."
        )
        
        prompt = (
            f"Concept: {concept_name}\n"
            f"Grounded Explanation (Ground Truth):\n{explanation}\n\n"
            f"Chat History:\n{json.dumps(chat_history, indent=2)}\n\n"
            f"User Message:\n{message}"
        )
        
        result = await self.llm_service.generate_json(system_instruction, prompt, TutorResponseModel)
        
        if raw_text:
            result["response"] = await self._audit_response(result["response"], raw_text)
        
        return result
