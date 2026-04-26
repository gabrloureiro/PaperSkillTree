from pydantic import BaseModel
from typing import List

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
