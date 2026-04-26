import asyncio
import os
import json
from src.services.llm_service import LLMService
from src.services.ingestion_service import PDFIngester
from src.agents.pipeline_agents import PipelineAgents
from src.core.graph_builder import GraphBuilder
from src.services.graph_service import GraphService
from src.core.config import Config
from dotenv import load_dotenv

load_dotenv()

async def raw_dump():
    print("--- Raw Event Dump ---")
    llm = LLMService(Config.MODEL_NAME, Config.TEMPERATURE)
    agents = PipelineAgents(llm)
    builder = GraphBuilder(agents)
    graph = builder.build()
    
    initial_state = {
        "raw_text": [{"raw_text": "Sample text", "section_header": "Intro"}],
        "skill_tree_nodes": [],
        "current_node_under_review": None,
        "current_raw_text_under_review": "",
        "draft_analysis": None,
        "critique_feedback": None,
        "validation_status": False,
        "unprocessed_nodes": [],
        "revision_count": 0,
        "final_dag": None
    }

    async for event in graph.astream_events(initial_state, version="v2"):
        print(f"Event: {event['event']} | Name: {event['name']}")
        # if event['event'] == "on_chain_end":
        #    print(f"      Data: {event.get('data', {}).get('output')}")

if __name__ == "__main__":
    asyncio.run(raw_dump())
