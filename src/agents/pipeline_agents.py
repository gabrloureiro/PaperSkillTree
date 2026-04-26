import json
from typing import Dict, Any, List, Union
from src.services.llm_service import LLMService
from src.models.schemas import (
    CartographerOutputModel, ExpertOutputModel, 
    ValidatorOutputModel, SynthesizerOutputModel
)
from src.models.state import PaperState, BranchState

class PipelineAgents:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def cartographer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Cartographer", CartographerOutputModel)
        system_instruction += (
            "\n\nTHOROUGHNESS DIRECTIVE:\n"
            "Your goal is to create an exhaustive map of the paper's knowledge. "
            "Do not skip technical nuances, specific algorithms, or niche terminology. "
            "A thorough map should contain a dense collection of interconnected concepts."
        )
        prompt = (
            "Analyze ALL provided text sections to extract a comprehensive list of concepts and terms.\n"
            "For each extracted concept, explicitly tie it to the exact section header it originated from in the 'source_section_header' field.\n"
            "Also, provide a generic 'icon_name' for the concept (PascalCase Lucide icon name).\n"
            "Ensure you capture high-level themes (e.g., 'Transformer Architecture') and granular details (e.g., 'Multi-Head Attention').\n"
            "Raw text sections:\n" + json.dumps(state.get("raw_text", []), indent=2)
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, CartographerOutputModel)
        nodes = result.get("nodes", [])
        return {"unprocessed_nodes": nodes}

    async def expert(self, state: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Expert", ExpertOutputModel)
        node = state.get("current_node_under_review") or {}
        raw_text = state.get("current_raw_text_under_review") or ""
        available_nodes = state.get("available_nodes") or []
        
        # Create a mapping of node IDs to names for the LLM to reference
        node_catalog = [f"{n.get('node_id')}: {n.get('concept_name')}" for n in available_nodes]
        
        if not raw_text.strip():
            raw_text = "[General Context Provided for Analysis]"

        prompt = (
            f"Analyze the following node and its relevant text chunk to draft a thorough and comprehensive technical explanation.\n"
            f"Node:\n{json.dumps(node, indent=2)}\n\n"
            f"Relevant Text Chunk:\n{raw_text}\n\n"
            f"--- PREREQUISITE SELECTION ---\n"
            f"You MUST select prerequisites ONLY from the following list of available nodes. "
            f"Do not reference any ID that is not in this list.\n"
            f"Available Nodes:\n{json.dumps(node_catalog, indent=2)}\n\n"
            f"IMPORTANT: Use the exact concept_name and icon_name provided in the node JSON."
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, ExpertOutputModel)
        
        # --- BULLETPROOF METADATA PRESERVATION ---
        result["node_id"] = node.get("node_id")
        result["concept_name"] = node.get("concept_name")
        result["icon_name"] = node.get("icon_name")
        result["source_section_header"] = node.get("source_section_header") # PRESERVE FOR FRONTEND CLUSTERING
        
        # Post-filter: Ensure prerequisites actually exist in the available list
        valid_ids = {n.get("node_id") for n in available_nodes}
        result["prerequisite_node_ids"] = [pid for pid in result.get("prerequisite_node_ids", []) if pid in valid_ids]
        
        return {"draft_analysis": result}

    async def validator(self, state: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Validator", ValidatorOutputModel)
        system_instruction += (
            "\nSpecific instruction: You are a thorough fact-checker. Your goal is to verify if the Expert's explanation is factually correct. "
            "Flag any claim that is not explicitly stated in the Source Text, including contradictions, misinterpretations, and hallucinations."
        )
        draft = state.get("draft_analysis") or {}
        raw_text = state.get("current_raw_text_under_review") or ""
        prompt = (
            f"Compare the Expert's draft strictly against the raw source text. Flag any claim not explicitly supported.\n"
            f"Draft Analysis:\n{json.dumps(draft, indent=2)}\n\n"
            f"Source Text:\n{raw_text}"
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, ValidatorOutputModel)
        
        is_valid = result.get("is_valid", False)
        output = {
            "critique_feedback": result,
            "validation_status": is_valid
        }
        if is_valid:
            output["skill_tree_nodes"] = [draft]
            
        return output

    async def resolution(self, state: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Resolution", ExpertOutputModel)
        node = state.get("current_node_under_review") or {}
        draft = state.get("draft_analysis") or {}
        critique = state.get("critique_feedback") or {}
        raw_text = state.get("current_raw_text_under_review") or ""
        prompt = (
            f"The Validator found issues with the draft. Rewrite it to be 100% accurate to the source.\n"
            f"Issues: {json.dumps(critique, indent=2)}\n"
            f"Original Draft: {json.dumps(draft, indent=2)}\n"
            f"Source: {raw_text}\n\n"
            f"IMPORTANT: Preserve the exact concept_name and icon_name."
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, ExpertOutputModel)
        
        # --- BULLETPROOF METADATA PRESERVATION ---
        result["node_id"] = node.get("node_id")
        result["concept_name"] = node.get("concept_name")
        result["icon_name"] = node.get("icon_name")
        result["source_section_header"] = node.get("source_section_header") # PRESERVE FOR FRONTEND CLUSTERING
        
        output = {
            "draft_analysis": result,
            "revision_count": state.get("revision_count", 0) + 1
        }
        return output

    async def synthesizer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Synthesizer", SynthesizerOutputModel)
        system_instruction += (
            "\n\nREADABILITY & TOPOLOGY DIRECTIVE:\n"
            "1. Construct a Directed Acyclic Graph (DAG) that represents a clear learning path.\n"
            "2. Avoid redundant edges: if A -> B and B -> C exist, do NOT add A -> C.\n"
            "3. Minimize edge crossings by ensuring concepts flow logically from fundamental to advanced.\n"
            "4. Only include edges between nodes that exist in the input list.\n"
            "5. Ensure the graph is interpretable: avoid 'spaghetti' connections."
        )
        nodes = state.get("skill_tree_nodes") or []
        prompt = (
            f"Synthesize a clean, logical DAG from these validated nodes.\n"
            f"Validated Nodes:\n{json.dumps(nodes, indent=2)}\n\n"
            f"Instructions:\n"
            f"- Use the 'prerequisite_node_ids' as primary signals, but feel free to prune or refine them to ensure a clean hierarchical structure.\n"
            f"- Each edge should represent a necessary 'step' in understanding."
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, SynthesizerOutputModel)
        
        # Post-process: Filter out edges referencing missing nodes
        valid_ids = {n.get("node_id") for n in nodes}
        edges = result.get("directed_acyclic_graph", [])
        filtered_edges = [
            e for e in edges 
            if e.get("source") in valid_ids and e.get("target") in valid_ids
        ]
        
        # Remove direct duplicates
        seen_edges = set()
        final_edges = []
        for e in filtered_edges:
            pair = (e.get("source"), e.get("target"))
            if pair not in seen_edges and e.get("source") != e.get("target"):
                seen_edges.add(pair)
                final_edges.append(e)
        
        return {"final_dag": {"directed_acyclic_graph": final_edges}}
