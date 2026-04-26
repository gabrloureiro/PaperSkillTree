import operator
from typing import TypedDict, Annotated, List, Optional, Any, Dict

def reduce_nodes(current: List[Any], updates: List[Any]) -> List[Any]:
    """
    Merges node lists by node_id. If a node exists, it is updated. 
    This allows parallel branches to add nodes and the Synthesizer to refine them.
    """
    if not current:
        return updates
    if not updates:
        return current
        
    node_map = {n.get("node_id"): n for n in current if n.get("node_id")}
    for n in updates:
        node_id = n.get("node_id")
        if node_id:
            node_map[node_id] = n
            
    return list(node_map.values())

class PaperChunkInput(TypedDict):
    raw_text: str
    section_header: str

class CartographerNode(TypedDict):
    node_id: str
    concept_name: str
    icon_name: str
    source_section_header: str

class ExpertOutput(TypedDict):
    node_id: str
    concept_name: str
    icon_name: str
    explanation: str
    prerequisite_node_ids: List[str]
    # Added for frontend clustering/layout optimization
    source_section_header: str

class HallucinationFlag(TypedDict):
    claim: str
    issue_description: str

class ValidatorOutput(TypedDict):
    is_valid: bool
    hallucination_flags: List[HallucinationFlag]

class DAGEdge(TypedDict):
    source: str
    target: str

class SynthesizerOutput(TypedDict):
    directed_acyclic_graph: List[DAGEdge]

class StructuralAuditOutput(TypedDict):
    is_valid: bool
    reasoning: str
    suggested_changes: List[str]

class PaperState(TypedDict):
    # Use Annotated with 'last one wins' reducer to allow parallel branches 
    # to return these fields without conflict, as they are mostly static.
    raw_text: Annotated[List[PaperChunkInput], lambda x, y: y]
    skill_tree_nodes: Annotated[List[ExpertOutput], reduce_nodes]
    unprocessed_nodes: Annotated[List[CartographerNode], lambda x, y: y]
    skeleton_dag: Annotated[List[DAGEdge], lambda x, y: y]
    final_dag: Annotated[Optional[SynthesizerOutput], lambda x, y: y]
    audit_feedback: Annotated[Optional[StructuralAuditOutput], lambda x, y: y]
    audit_revision_count: Annotated[int, operator.add]

class BranchState(TypedDict):
    current_node_under_review: CartographerNode
    current_raw_text_under_review: str
    draft_analysis: Optional[ExpertOutput]
    critique_feedback: Optional[ValidatorOutput]
    validation_status: bool
    revision_count: int
    raw_text: List[PaperChunkInput]
    # List of all node IDs/names found by Cartographer to avoid hallucinated prerequisites
    available_nodes: List[CartographerNode]
    # The output we want to merge back to parent
    skill_tree_nodes: List[ExpertOutput]
