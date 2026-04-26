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

async def diagnostic():
    print("--- Starting Detailed Concept Trace ---")
    llm = LLMService(Config.MODEL_NAME, Config.TEMPERATURE)
    agents = PipelineAgents(llm)
    builder = GraphBuilder(agents)
    service = GraphService(PDFIngester(), builder)
    
    pdf_path = "./dummy_test.pdf"
    if not os.path.exists(pdf_path):
        print("No test PDF found.")
        return

    async for event in service.process_paper_stream(pdf_path):
        etype = event["type"]
        node = event.get("node", "N/A")
        
        if etype == "node_end" and node == "cartographer":
            output = event.get("output", {})
            # Handle both dict and list outputs
            nodes = output.get("unprocessed_nodes", []) if isinstance(output, dict) else []
            print(f"[Cartographer] Found {len(nodes)} concepts.")
            for n in nodes:
                print(f"  - {n.get('concept_name')} (Section: {n.get('source_section_header')})")
        
        if etype == "node_end" and node == "validator":
            output = event.get("output", {})
            if isinstance(output, dict):
                is_valid = output.get("validation_status")
                if is_valid:
                    print(f"[Validator] Node PASSED.")
                else:
                    print(f"[Validator] Node REJECTED. Flags: {len(output.get('critique_feedback', {}).get('hallucination_flags', []))}")

        if etype == "node_end" and node == "synthesizer":
            output = event.get("output", {})
            if isinstance(output, dict):
                dag = output.get("final_dag", {}).get("directed_acyclic_graph", [])
                print(f"[Synthesizer] Final DAG created with {len(dag)} edges.")

if __name__ == "__main__":
    asyncio.run(diagnostic())
