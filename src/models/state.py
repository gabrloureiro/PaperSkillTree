from typing import TypedDict, Annotated, List, Optional
import operator

class PaperChunkInput(TypedDict):
    raw_text: str
    section_header: str

class CartographerNode(TypedDict):
    node_id: str
    concept_name: str
    source_section_header: str

class ExpertOutput(TypedDict):
    node_id: str
    explanation: str
    prerequisite_node_ids: List[str]

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
    raw_text: List[PaperChunkInput]
    skill_tree_nodes: Annotated[List[ExpertOutput], operator.add]
    current_node_under_review: Optional[CartographerNode]
    current_raw_text_under_review: str
    draft_analysis: Optional[ExpertOutput]
    critique_feedback: Optional[ValidatorOutput]
    validation_status: bool
    unprocessed_nodes: List[CartographerNode]
    revision_count: int
    final_dag: Optional[SynthesizerOutput]
