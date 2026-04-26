import json
from typing import Dict, Any, List
from src.services.llm_service import LLMService
from src.models.schemas import (
    CartographerOutputModel, ExpertOutputModel, 
    ValidatorOutputModel, SynthesizerOutputModel
)
from src.models.state import PaperState

class PipelineAgents:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    def cartographer(self, state: PaperState) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Cartographer", CartographerOutputModel)
        prompt = (
            "Extract terms and structure from the following abstract, intro, and conclusion sections.\n"
            "For each extracted concept, explicitly tie it to the exact section header it originated from in the 'source_section_header' field.\n"
            "Also, provide a generic 'icon_name' for the concept (PascalCase Lucide icon name).\n"
            "Raw text sections:\n" + json.dumps(state.get("raw_text", []), indent=2)
        )
        result = self.llm_service.generate_json(system_instruction, prompt, CartographerOutputModel)
        return {"unprocessed_nodes": result.get("nodes", [])}

    def expert(self, state: PaperState) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Expert", ExpertOutputModel)
        node = state.get("current_node_under_review", {})
        raw_text = state.get("current_raw_text_under_review", "")
        prompt = (
            f"Analyze the following node and its relevant text chunk to draft an explanation and identify prerequisites.\n"
            f"Node:\n{json.dumps(node, indent=2)}\n\n"
            f"Relevant Text Chunk:\n{raw_text}"
        )
        result = self.llm_service.generate_json(system_instruction, prompt, ExpertOutputModel)
        return {"draft_analysis": result}

    def validator(self, state: PaperState) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Validator", ValidatorOutputModel)
        system_instruction += (
            "\nSpecific instruction: You are a hostile reviewer. Your only goal is to find claims in the Draft "
            "that are not explicitly stated in the Source Text."
        )
        draft = state.get("draft_analysis", {})
        raw_text = state.get("current_raw_text_under_review", "")
        prompt = (
            f"Compare the Expert's draft strictly against the raw source text. Flag any claim not explicitly supported.\n"
            f"Draft Analysis:\n{json.dumps(draft, indent=2)}\n\n"
            f"Source Text:\n{raw_text}"
        )
        result = self.llm_service.generate_json(system_instruction, prompt, ValidatorOutputModel)
        return {
            "critique_feedback": result,
            "validation_status": result.get("is_valid", False)
        }

    def resolution(self, state: PaperState) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Resolution", ExpertOutputModel)
        draft = state.get("draft_analysis", {})
        critique = state.get("critique_feedback", {})
        raw_text = state.get("current_raw_text_under_review", "")
        prompt = (
            f"Rewrite the draft to strictly remove flags raised by the Validator.\n"
            f"Original Draft:\n{json.dumps(draft, indent=2)}\n\n"
            f"Validator Critique:\n{json.dumps(critique, indent=2)}\n\n"
            f"Source Text:\n{raw_text}"
        )
        result = self.llm_service.generate_json(system_instruction, prompt, ExpertOutputModel)
        revision_count = state.get("revision_count", 0) + 1
        return {
            "draft_analysis": result,
            "revision_count": revision_count
        }

    def synthesizer(self, state: PaperState) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Synthesizer", SynthesizerOutputModel)
        nodes = state.get("skill_tree_nodes", [])
        prompt = (
            f"Format the final validated nodes into a Directed Acyclic Graph (DAG) structure.\n"
            f"Validated Nodes:\n{json.dumps(nodes, indent=2)}"
        )
        result = self.llm_service.generate_json(system_instruction, prompt, SynthesizerOutputModel)
        return {"final_dag": result}
