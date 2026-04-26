import json
from typing import Dict, Any, List, Union
from src.services.llm_service import LLMService
from src.models.schemas import (
    CartographerOutputModel, ExpertOutputModel, 
    ValidatorOutputModel, SynthesizerOutputModel,
    StructuralAuditorOutputModel
)
from src.models.state import PaperState, BranchState

class PipelineAgents:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def cartographer(self, state: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Cartographer", CartographerOutputModel)
        system_instruction += (
            "\n\nTHOROUGHNESS & FLOW DIRECTIVE:\n"
            "Your goal is to create an exhaustive map of the paper's knowledge. "
            "Do not skip technical nuances, specific algorithms, or niche terminology. "
            "A thorough map should contain a dense collection of interconnected concepts, but no node should have too many (more than 3) prerequisites. "
            "It should reflect a logical progression of the ideas. "
            "It does not need to strictly adhere to the paper's narrative progression, but rather a logical flow of the ideas."
        )
        prompt = (
            "Analyze ALL provided text sections to extract a comprehensive list of concepts. "
            "Propose a 'skeleton_dag' map that distributes concepts evenly. "
            "If any given concept has more than 3 prerequisites, break it down or distribute prerequisites into a sequential chain of intermediary nodes. "
            "For each extracted concept, explicitly tie it to the exact section header it originated from in the 'source_section_header' field. "
            "Also, provide a generic 'icon_name' for the concept (PascalCase Lucide icon name). "
            "Ensure you capture high-level themes (e.g., 'Transformer Architecture') and granular details (e.g., 'Multi-Head Attention').\n"
            "Raw text sections:\n" + json.dumps(state.get("raw_text", []), indent=2)
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, CartographerOutputModel)
        nodes = result.get("nodes", [])
        skeleton = result.get("skeleton_dag", [])
        return {"unprocessed_nodes": nodes, "skeleton_dag": skeleton}

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
            "6. Merge the Cartographer's Skeleton DAG with the Expert's technical dependencies.\n"
            "7. MAINTAIN EVEN DENSITY: Prune redundant edges and avoid 'bottleneck' nodes with too many inputs. Two inputs is a good average, the number should never go above 3.\n"
            "8. Ensure the graph is a Directed Acyclic Graph (DAG) with a clear pedagogical flow.\n"
            "9. If Expert dependencies conflict with the Skeleton, prioritize logical comprehension over paper narrative.\n"
            "10. Use the 'audit_feedback' if provided to correct structural imbalances."
        )
        nodes = state.get("skill_tree_nodes") or []
        skeleton = state.get("skeleton_dag") or []
        feedback = state.get("audit_feedback")
        
        prompt = (
            f"Synthesize a clean, balanced, and logical DAG from these validated nodes and the skeleton DAG.\n"
            f"Validated Nodes:\n{json.dumps(nodes, indent=2)}\n\n"
            f"Initial Skeleton DAG:\n{json.dumps(skeleton, indent=2)}\n\n"
            f"Structural Audit Feedback:\n{json.dumps(feedback, indent=2) if feedback else 'None'}\n\n"
            f"Instructions:\n"
            f"- Use the 'prerequisite_node_ids' as primary signals, but feel free to prune or refine them to ensure a clean hierarchical structure.\n"
            f"- Each edge should represent a necessary 'step' in understanding.\n"
            f"- Avoid creating 'bottleneck' nodes (nodes with too many incoming edges).\n"
            f"- Integrate technical dependencies while preserving the optimized density of the skeleton.\n"
            f"- Ensure every node is reachable from a root node (start of the paper/concepts)."
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
        
        # --- SINGLE SOURCE of TRUTH SYNCHRONIZATION ---
        # Update the prerequisite_node_ids of each node to exactly match the finalized DAG edges.
        edge_map = {}
        for e in final_edges:
            source = e.get("source")
            target = e.get("target")
            if target not in edge_map:
                edge_map[target] = []
            if source not in edge_map[target]:
                edge_map[target].append(source)

        updated_nodes = []
        for n in nodes:
            n_copy = n.copy()
            # The node's internal prerequisite list MUST match the DAG structure exactly.
            n_copy["prerequisite_node_ids"] = edge_map.get(n.get("node_id"), [])
            updated_nodes.append(n_copy)
        
        return {
            "final_dag": {"directed_acyclic_graph": final_edges},
            "skill_tree_nodes": updated_nodes
        }

    async def structural_auditor(self, state: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("StructuralAuditor", StructuralAuditorOutputModel)
        system_instruction += (
            "\n\nAUDIT DIRECTIVE:\n"
            "1. CIRCULARITY: Verify all prerequisite relationships to ensure no cycles exist. This includes verifying that there are nodes with no prerequisites, as well as nodes with no target nodes.\n"
            "2. CONNECTIVITY: Ensure the graph is fully connected. Every node should be part of the flow.\n"
            "3. TOPOLOGICAL BALANCE: Identify 'bottlenecks' (nodes with > 3 prerequisites). Suggest splitting or redistribution.\n"
            "4. COMPREHENSION FLOW: Verify that prerequisites logically aid in understanding the target concept.\n"
            "5. ALIGNMENT: Ensure the graph represents the paper's internal logic and comprehension pipeline."
            "6. CRITICAL DENSITY CHECK: Verify that no node has more than 3 prerequisite nodes. If any node has more than 3 prerequisites, it is an indicator of poor structural balance."
        )
        nodes = state.get("skill_tree_nodes") or []
        dag = state.get("final_dag", {}).get("directed_acyclic_graph", [])
        skeleton = state.get("skeleton_dag") or []
        
        prompt = (
            f"Audit the following skill tree structure for logical and topological integrity.\n"
            f"Compare the 'Current DAG' against the 'Initial Skeleton' to identify inversions or lost logical flow.\n\n"
            f"Nodes:\n{json.dumps(nodes, indent=2)}\n\n"
            f"Initial Skeleton Flow:\n{json.dumps(skeleton, indent=2)}\n\n"
            f"Current DAG Edges:\n{json.dumps(dag, indent=2)}\n"
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, StructuralAuditorOutputModel)
        
        return {
            "audit_feedback": result,
            "audit_revision_count": state.get("audit_revision_count", 0) + 1
        }
