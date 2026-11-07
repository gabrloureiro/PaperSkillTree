import json
from typing import Dict, Any, List, Union
from src.services.llm_service import LLMService
from src.models.schemas import (
    CartographerOutputModel, ExpertOutputModel, 
    ValidatorOutputModel, SynthesizerOutputModel,
    StructuralAuditorOutputModel, RecruiterOutputModel,
    CouncilDesignOutputModel, CouncilReviewOutputModel,
    NodeEvaluatorRubricsModel, EvaluatorRubricModel,
    CouncilMemberResponseModel, CouncilAuditModel
)
from src.models.state import PaperState, BranchState

class PipelineAgents:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def recruiter(self, state: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Recruiter", RecruiterOutputModel)
        system_instruction += (
            "\n\nROLE:\n"
            "You are the organizer of a teaching council for an important lecture series. Your task is to analyze the provided research paper "
            "and determine its primary field of study. Then, you must identify a set of specialist expert roles (e.g., 'Quantum Physicist', "
            "'Machine Learning Researcher', 'Linguistic Philosopher') who are best suited to discuss and teach the concepts in this paper. "
            "Ensure the roles are diverse and represent different technical angles of the paper to ensure a multi-dimensional audit.\n\n"
            "COUNCIL SIZE: You MUST identify between 3 and 5 specialists. Do not exceed 5 roles."
        )
        prompt = (
            "Analyze the following paper text and identify the field of study and the best specialists to teach it.\n\n"
            "Paper Text (excerpts):\n" + json.dumps([c.get("raw_text", "")[:2000] for c in state.get("raw_text", [])[:5]], indent=2)
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, RecruiterOutputModel)
        specialists = result.get("specialists", [])
        return {
            "field_of_study": result.get("field_of_study"),
            "specialists": specialists,
            "current_specialist_index": 0,
            "current_council_role": specialists[0] if specialists else "Expert",
            "council_phase": "brainstorm"
        }

    async def council_member(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolidated specialist agent that persists throughout the pipeline.
        Tasks: Brainstorming, Plan Auditing, Final DAG Review.
        """
        role = state.get("current_council_role", "Expert")
        phase = state.get("council_phase", "brainstorm")
        history = state.get("council_chat_history", [])
        field = state.get("field_of_study", "Academic")
        
        # Adjust model and instruction based on phase
        output_model = CouncilMemberResponseModel
        if phase == "plan_audit":
            output_model = CouncilAuditModel
            
        system_instruction = self.llm_service.get_system_instruction(f"Council_{role}", output_model)
        system_instruction += f"\n\nIDENTITY: You are the {role} member of the Teaching Council.\n"
        
        if phase == "brainstorm":
            target_range = "5-8 nodes" if state.get("complexity") == "simple" else "20-30 nodes"
            system_instruction += (
                f"TASK: As the {role}, identify MUST-HAVE technical concepts, formulas, and specific details from this paper "
                f"that fall strictly within your domain of expertise in '{field}'.\n"
                "CRITICAL: Do NOT provide a general summary. Do NOT repeat points already made by other council members. "
                "Instead, focus on the unique technical nuances that ONLY someone with your specific background would notice. "
                "Be a 'devil's advocate' for technical depth—ensure the Pedagogical Expert does not skip challenging concepts.\n\n"
                f"SCALE TARGET: We are aiming for a learning map of {target_range}. Identify specific sub-concepts that "
                "contribute to this level of granularity."
            )
            prompt = (
                f"From your perspective as a {role}, what are the technical non-negotiables for this paper?\n\n"
                f"Previous Discussion:\n{json.dumps(history, indent=2)}\n\n"
                f"Full Paper Context:\n" + json.dumps(state.get("raw_text", []), indent=2)
            )
        elif phase == "plan_audit":
            system_instruction += (
                "TASK: Audit the Pedagogical Expert's proposed plan strictly for FACTUAL ACCURACY and COMPLETENESS.\n"
                "Reject if it misses key formulas or misuses technical terms. Provide specific critique if rejecting."
            )
            prompt = (
                f"Proposed Plan:\n{json.dumps(state.get('proposed_plan', {}), indent=2)}\n\n"
                f"Full Paper Context:\n" + json.dumps(state.get("raw_text", []), indent=2)
            )
        else: # final_dag_review
            system_instruction += (
                "TASK: This is the FINAL review of the generated Skill Tree (DAG).\n"
                "Compare the nodes and connections against the paper. Are the prerequisites technically sound?\n"
                "Provide your final feedback."
            )
            prompt = (
                f"Skill Tree Nodes:\n{json.dumps(state.get('skill_tree_nodes', []), indent=2)}\n\n"
                f"DAG Edges:\n{json.dumps(state.get('final_dag', {}).get('directed_acyclic_graph', []), indent=2)}\n\n"
                f"Full Paper Context:\n" + json.dumps(state.get("raw_text", []), indent=2)
            )

        result = await self.llm_service.generate_json(system_instruction, prompt, output_model)
        
        specialists = state.get("specialists", [])
        
        # Calculate next state
        next_index = 0
        if phase == "final_dag_review":
            next_index = state.get("final_council_index", 0) + 1
        else:
            next_index = state.get("current_specialist_index", 0) + 1
            
        next_role = ""
        if next_index < len(specialists):
            next_role = specialists[next_index]
        else:
            next_role = "Pedagogical Expert"

        output = {
            "current_role_snapshot": role,
            "current_council_role": next_role
        }
        
        if phase == "plan_audit":
            output["current_specialist_index"] = next_index
            if not result.get("is_approved"):
                output["council_critiques"] = [f"{role}: {result.get('critique')}"]
        elif phase == "final_dag_review":
            output["final_council_index"] = next_index
            output["final_council_review_history"] = [{"role": role, "message": result.get("message")}]
        else: # brainstorm
            output["current_specialist_index"] = next_index
            output["council_chat_history"] = [{"role": role, "message": result.get("message")}]
            
        return output

    async def pedagogical_expert(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Consolidated lead educator agent.
        Tasks: Plan Design/Revision, Final DAG Verdict, Rubric Generation.
        """
        phase = state.get("council_phase")
        complexity = state.get("complexity", "simple")
        
        if phase == "rubric_generation":
            output_model = NodeEvaluatorRubricsModel
        elif phase == "final_dag_review":
            output_model = CouncilReviewOutputModel
        else: # design or revision
            output_model = CouncilDesignOutputModel
            
        system_instruction = self.llm_service.get_system_instruction("PedagogicalExpert", output_model)
        system_instruction += (
            "\n\nIDENTITY: You are the Lead Pedagogical Expert. You synthesize technical specialist requirements "
            "into an engaging, factual, and logically sequenced learning progression.\n"
        )
        
        if phase == "rubric_generation":
            template = state.get("council_instructions", {}).get("evaluator_template", "")
            nodes = state.get("skill_tree_nodes", [])
            system_instruction += (
                f"TASK: Generate specific instructions and granular grading rubrics for each node based on the strategy.\n"
                f"You MUST provide a rubric for every grade: A+, A, A-, B+, B, B-, C+, C, C-, D+, D, D-, and F.\n"
                f"General Template: {template}"
            )
            prompt = f"Nodes to process:\n" + json.dumps([{"node_id": n.get("node_id"), "concept_name": n.get("concept_name"), "explanation": n.get("explanation")} for n in nodes], indent=2)
            result = await self.llm_service.generate_json(system_instruction, prompt, NodeEvaluatorRubricsModel)
            return {
                "node_evaluator_rubrics": result.get("rubrics", {}),
                "current_role_snapshot": "Pedagogical Expert"
            }

        elif phase == "final_dag_review":
            system_instruction += (
                "TASK: Make the FINAL assessment of the Skill Tree. Review specialists' feedback and ensure "
                "the DAG meets the pedagogical goals."
            )
            prompt = (
                f"Specialist Feedback:\n{json.dumps(state.get('final_council_review_history', []), indent=2)}\n\n"
                f"Nodes:\n{json.dumps(state.get('skill_tree_nodes', []), indent=2)}\n\n"
                f"DAG Edges:\n{json.dumps(state.get('final_dag', {}).get('directed_acyclic_graph', []), indent=2)}"
            )
            result = await self.llm_service.generate_json(system_instruction, prompt, CouncilReviewOutputModel)
            return {
                "council_review": result,
                "current_role_snapshot": "Pedagogical Expert",
                "council_phase": "rubric_generation",
                "current_council_role": "Pedagogical Expert"
            }

        else: # Design or Revision
            iteration = state.get("council_iteration_count", 0)
            system_instruction += (
                f"TASK: Design/Revise the learning plan. Complexity: {complexity.upper()}.\n"
                "Factual accuracy must satisfy specialists. Engagement must be high."
            )
            prompt = (
                f"Discussion History:\n{json.dumps(state.get('council_chat_history', []), indent=2)}\n\n"
                f"Previous Plan: {json.dumps(state.get('proposed_plan', {}), indent=2)}\n\n"
                f"Unresolved Critiques: {json.dumps(state.get('council_critiques', []), indent=2)}\n\n"
                f"Full Paper Context:\n" + json.dumps(state.get("raw_text", []), indent=2)
            )
            result = await self.llm_service.generate_json(system_instruction, prompt, CouncilDesignOutputModel)
            specialists = state.get("specialists", [])
            return {
                "proposed_plan": result,
                "council_iteration_count": 1,
                "council_critiques": [],
                "council_phase": "plan_audit",
                "current_specialist_index": 0,
                "current_council_role": specialists[0] if specialists else "Expert"
            }

    async def council_handoff(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Final planning speaker delivers the consensus plan downstream.
        """
        plan = state.get("proposed_plan", {})
        return {
            "learning_progression_strategy": plan.get("progression_strategy"),
            "council_instructions": {
                "cartographer": plan.get("cartographer_instructions"),
                "expert": plan.get("expert_instructions"),
                "evaluator_template": plan.get("evaluator_instructions_template")
            }
        }

    async def cartographer(self, state: Dict[str, Any]) -> Dict[str, Any]:

        system_instruction = self.llm_service.get_system_instruction("Cartographer", CartographerOutputModel)
        council_instr = state.get("council_instructions", {}).get("cartographer", "")
        complexity = state.get("complexity", "simple")
        
        node_count_limit = "5 to 15 nodes at most. Keep it linear and high-level." if complexity == "simple" else "20 to 30 nodes. You MUST be exhaustive, breaking down complex sections into many granular sub-concepts."

        system_instruction += (
            f"\n\nCOUNCIL DIRECTIVES:\n{council_instr}\n\n"
            f"THOROUGHNESS & FLOW DIRECTIVE:\n"
            f"User Complexity Choice: {complexity.upper()}\n"
            f"Node Count Requirement: {node_count_limit}\n"
            f"Your goal is to create a map of the paper's knowledge based on the council's strategy. "
            "It should reflect a logical progression of the ideas. "
        )
        prompt = (
            "Analyze ALL provided text sections to extract a comprehensive list of concepts. "
            "Propose a 'skeleton_dag' map that distributes concepts evenly. "
            "If any given concept has more than 3 prerequisites, break it down or distribute prerequisites into a sequential chain of intermediary nodes. "
            "CONNECTIVITY (MANDATORY): Every node MUST be connected to the graph. There should be no 'islands' or isolated nodes. "
            "Every node must have at least one incoming prerequisite (unless it's the very first node) and eventually lead to higher-level understanding. "
            "Ensure a clear 'path of comprehension' from simple concepts to the paper's final conclusions.\n"
            "SOURCE TRACING: Maintain the 'source_section_header' for each node."
            "Also, provide a generic 'icon_name' for the concept (PascalCase Lucide icon name). "
            "Ensure you capture high-level themes (e.g., 'Transformer Architecture') and granular details (e.g., 'Multi-Head Attention').\n"
            "Raw text sections:\n" + json.dumps(state.get("raw_text", []), indent=2)
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, CartographerOutputModel)
        nodes = result.get("nodes", [])
        
        # --- ROBUST ID GENERATION ---
        for i, node in enumerate(nodes):
            if not node.get("node_id"):
                # Fallback to concept name or index
                clean_name = node.get("concept_name", f"node_{i}").lower().replace(" ", "_")
                node["node_id"] = f"{clean_name}_{i}"
                
        skeleton = result.get("skeleton_dag", [])
        return {"unprocessed_nodes": nodes, "skeleton_dag": skeleton}

    async def expert(self, state: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Expert", ExpertOutputModel)
        council_instr = state.get("node_expert_instructions", "")
        node = state.get("current_node_under_review") or {}
        raw_text = state.get("current_raw_text_under_review") or ""
        available_nodes = state.get("available_nodes") or []
        
        system_instruction += (
            f"\n\nCOUNCIL DIRECTIVES:\n{council_instr}\n\n"
            "STYLE: Engaging but factual. Do not hallucinate. Check all claims against the canonical document."
        )

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
            "Flag any claim that is not explicitly stated in the Source Text, including contradictions, misinterpretations, and hallucinations. "
            "STRICT GROUNDING: If the Expert uses external knowledge NOT found in the Source Text, mark it as a hallucination."
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
        # Emit the draft once it is valid OR the revision budget is exhausted. This
        # mirrors the exit condition in GraphBuilder._route_after_validator: without
        # the second clause a node the Validator never approves is dropped silently.
        if is_valid or state.get("revision_count", 0) >= 3:
            output["skill_tree_nodes"] = [draft]

        return output

    async def resolution(self, state: Dict[str, Any]) -> Dict[str, Any]:
        system_instruction = self.llm_service.get_system_instruction("Resolution", ExpertOutputModel)
        node = state.get("current_node_under_review") or {}
        draft = state.get("draft_analysis") or {}
        critique = state.get("critique_feedback") or {}
        raw_text = state.get("current_raw_text_under_review") or ""
        
        prompt = (
            f"The Validator found issues with the draft. Rewrite it to be 100% accurate to the source text.\n"
            f"STRICT GROUNDING REQUIREMENT: Use ONLY the information provided in the 'Source' text below. Do NOT use any external knowledge or make additive claims not found in the paper.\n"
            f"Issues: {json.dumps(critique, indent=2)}\n"
            f"Original Draft: {json.dumps(draft, indent=2)}\n"
            f"Source: {raw_text}\n\n"
            f"IMPORTANT: Preserve the exact concept_name and icon_name."
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, ExpertOutputModel)
        
        # Preserve metadata
        result["node_id"] = node.get("node_id")
        result["concept_name"] = node.get("concept_name")
        result["icon_name"] = node.get("icon_name")
        result["source_section_header"] = node.get("source_section_header")
        
        return {
            "draft_analysis": result,
            "revision_count": state.get("revision_count", 0) + 1
        }

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
            "10. Use the 'audit_feedback' if provided to correct structural imbalances.\n"
            "11. NO DISCONNECTED SUBGRAPHS: Every single node MUST be reachable from the start of the paper. If a node is isolated, you MUST link it to its most logical prerequisite."
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
            f"- Ensure every node is reachable from a root node (start of the paper/concepts). NO DISCONNECTED SUBGRAPHS."
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
            "1. NO CYCLES (CRITICAL): The skill tree MUST be a Directed Acyclic Graph (DAG). If any circular dependencies exist (e.g., A -> B -> C -> A), the visualization will CRASH. You MUST break all cycles by identifying the 'entry point' and 'exit point' of loops.\n"
            "2. TOTAL CONNECTIVITY (CRITICAL): There MUST be NO disconnected subgraphs. Every single node MUST be reachable from the 'start' of the tree. If you find isolated nodes, link them to the most relevant parent node.\n"
            "3. TOPOLOGICAL BALANCE: Identify 'bottlenecks' (nodes with > 3 prerequisites). Suggest splitting or redistribution.\n"
            "4. COMPREHENSION FLOW: Verify that prerequisites logically aid in understanding the target concept.\n"
            "5. ALIGNMENT: Ensure the graph represents the paper's internal logic and comprehension pipeline."
            "6. CRITICAL DENSITY CHECK: Verify that no node has more than 3 prerequisite nodes. If any node has more than 3 prerequisites, it is an indicator of poor structural balance."
        )
        nodes = state.get("skill_tree_nodes") or []
        dag = state.get("final_dag", {}).get("directed_acyclic_graph", [])
        skeleton = state.get("skeleton_dag") or []
        
        # --- REACHABILITY AUDIT ---
        # Build adjacency list. Use .get() throughout: a malformed edge or a node
        # missing an id must not take the whole audit down with a KeyError.
        adj = {}
        for e in dag:
            s, t = e.get("source"), e.get("target")
            if not s or not t:
                continue
            adj.setdefault(s, []).append(t)

        node_ids = [n.get("node_id") for n in nodes if n.get("node_id")]
        targets = {e.get("target") for e in dag}

        # Find roots (nodes with no prerequisites)
        roots = [nid for nid in node_ids if nid not in targets]

        # BFS for reachability
        reachable = set()
        queue = list(roots)
        while queue:
            curr = queue.pop(0)
            if curr not in reachable:
                reachable.add(curr)
                queue.extend(adj.get(curr, []))

        islands = [nid for nid in node_ids if nid not in reachable]
        island_msg = ""
        if islands:
            island_msg = f"\n\nCRITICAL ERROR: The following nodes are DISCONNECTED 'islands' and cannot be reached from the start of the paper: {', '.join(islands)}. You MUST add prerequisites to these nodes to connect them to the main tree."

        prompt = (
            f"Audit the following skill tree structure for logical and topological integrity.\n"
            f"Compare the 'Current DAG' against the 'Initial Skeleton' to identify inversions or lost logical flow.\n\n"
            f"Nodes:\n{json.dumps(nodes, indent=2)}\n\n"
            f"Initial Skeleton Flow:\n{json.dumps(skeleton, indent=2)}\n\n"
            f"Current DAG Edges:\n{json.dumps(dag, indent=2)}\n\n"
            f"{island_msg}"
        )
        result = await self.llm_service.generate_json(system_instruction, prompt, StructuralAuditorOutputModel)
        
        # audit_revision_count reduces with operator.add, so return the increment
        # itself (1), not the running total -- returning the total makes the reducer
        # add a cumulative value and the count grows 1, 3, 7, ...
        revision_count = state.get("audit_revision_count", 0) + 1
        output = {
            "audit_feedback": result,
            "audit_revision_count": 1
        }

        if result.get("is_valid") or revision_count >= 3:
            specialists = state.get("specialists", [])
            output["final_council_index"] = 0
            output["council_phase"] = "final_dag_review"
            output["current_council_role"] = specialists[0] if specialists else "Expert"
            
        return output
