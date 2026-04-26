import asyncio
import json
import os
from dotenv import load_dotenv
from src.services.llm_service import LLMService
from src.agents.pipeline_agents import PipelineAgents

load_dotenv()

async def test_cartographer():
    llm_service = LLMService()
    agents = PipelineAgents(llm_service)
    
    state = {
        "raw_text": [
            {
                "section_header": "Abstract",
                "raw_text": "This paper introduces the Attention Is All You Need architecture, a novel sequence transduction model based entirely on attention mechanisms, dispensing with recurrence and convolutions entirely."
            },
            {
                "section_header": "Introduction",
                "raw_text": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms."
            },
            {
                "section_header": "Model Architecture",
                "raw_text": "Most competitive neural sequence transduction models have an encoder-decoder structure. The encoder maps an input sequence of symbol representations to a sequence of continuous representations. The decoder then generates an output sequence of symbols one element at a time. The Transformer follows this overall architecture using stacked self-attention and point-wise, fully connected layers for both the encoder and decoder."
            }
        ]
    }
    
    print("Running Cartographer...")
    result = await agents.cartographer(state)
    print("\nCartographer Results:")
    print(json.dumps(result, indent=2))
    
    nodes = result.get("unprocessed_nodes", [])
    print(f"\nTotal nodes found: {len(nodes)}")
    
    # Check if nodes come from sections other than Abstract/Intro/Conclusion if they exist
    headers = set(node.get("source_section_header") for node in nodes)
    print(f"Headers captured: {headers}")

if __name__ == "__main__":
    asyncio.run(test_cartographer())
