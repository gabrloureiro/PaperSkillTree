import pytest
from src.core.graph_builder import GraphBuilder
from src.agents.pipeline_agents import PipelineAgents
from src.services.llm_service import LLMService
from src.core.config import Config

def test_graph_compilation():
    # We only test if it builds without error for now
    llm_service = LLMService(Config.MODEL_NAME, Config.TEMPERATURE)
    pipeline_agents = PipelineAgents(llm_service)
    builder = GraphBuilder(pipeline_agents)
    graph = builder.build()
    assert graph is not None
