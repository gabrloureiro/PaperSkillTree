from typing import TypedDict, Annotated, List, Optional, Any
import operator

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

class PaperState(TypedDict):
    # Use Annotated with 'last one wins' reducer to allow parallel branches 
    # to return these fields without conflict, as they are mostly static.
    raw_text: Annotated[List[PaperChunkInput], lambda x, y: y]
    skill_tree_nodes: Annotated[List[ExpertOutput], operator.add]
    unprocessed_nodes: Annotated[List[CartographerNode], lambda x, y: y]
    final_dag: Annotated[Optional[SynthesizerOutput], lambda x, y: y]

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
