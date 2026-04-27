from pydantic import BaseModel
from typing import List, Dict, Optional

class CartographerNodeModel(BaseModel):
    node_id: str
    concept_name: str
    icon_name: str
    source_section_header: str

class DAGEdgeModel(BaseModel):
    source: str
    target: str

class CartographerOutputModel(BaseModel):
    nodes: List[CartographerNodeModel]
    skeleton_dag: List[DAGEdgeModel]

class ExpertOutputModel(BaseModel):
    node_id: str
    concept_name: str
    icon_name: str
    explanation: str
    prerequisite_node_ids: List[str]

class HallucinationFlagModel(BaseModel):
    claim: str
    issue_description: str

class ValidatorOutputModel(BaseModel):
    is_valid: bool
    hallucination_flags: List[HallucinationFlagModel]

class SynthesizerOutputModel(BaseModel):
    directed_acyclic_graph: List[DAGEdgeModel]

class ExaminerResponseModel(BaseModel):
    passed: bool
    letter_grade: str
    response: str

class TutorResponseModel(BaseModel):
    response: str

class AuditedResponseModel(BaseModel):
    response: str

class StructuralAuditorOutputModel(BaseModel):
    is_valid: bool
    reasoning: str
    suggested_changes: List[str]

class RecruiterOutputModel(BaseModel):
    field_of_study: str
    specialists: List[str]

class CouncilMemberResponseModel(BaseModel):
    message: str
    role: str

class CouncilDesignOutputModel(BaseModel):
    progression_strategy: str
    cartographer_instructions: str
    expert_instructions: str
    evaluator_instructions_template: str
    revision_rationale: Optional[str] = None

class CouncilAuditModel(BaseModel):
    is_approved: bool
    critique: Optional[str] = None

class CouncilReviewOutputModel(BaseModel):

    is_acceptable: bool
    critique: str

class EvaluatorRubricModel(BaseModel):
    instructions: str
    rubric_a_plus: str
    rubric_a: str
    rubric_a_minus: str
    rubric_b_plus: str
    rubric_b: str
    rubric_b_minus: str
    rubric_c_plus: str
    rubric_c: str
    rubric_c_minus: str
    rubric_d_plus: str
    rubric_d: str
    rubric_d_minus: str
    rubric_f: str

class NodeEvaluatorRubricsModel(BaseModel):
    # Mapping of node_id to their specific rubric
    rubrics: List[Dict[str, EvaluatorRubricModel]]

