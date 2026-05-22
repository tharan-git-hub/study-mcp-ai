import asyncio
import os
import sys

# Add the parent directory to system path to import modules correctly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from orchestrator.llm import LLMHelper
from orchestrator.mcp_client import MCPClientManager

async def extract_topic(query: str, llm: LLMHelper) -> str:
    """Use LLM to extract a single clean topic from a user's question."""
    prompt = (
        f"You are a topic extractor. Identify the primary educational/study subject or topic from the following question. "
        f"Output ONLY the topic name (1-3 words, lowercase, e.g., 'photosynthesis', 'newton laws', 'french revolution', 'mitosis') "
        f"and absolutely nothing else. Do not use quotes or punctuation.\n\n"
        f"Question: '{query}'"
    )
    try:
        topic = llm.generate(prompt=prompt, system_instruction="Identify the core academic topic. Return only the topic.")
        topic = topic.strip().strip("'\".").lower()
        print(f"Extracted Topic: '{topic}' from Query: '{query}'", file=sys.stderr)
        return topic
    except Exception as e:
        print(f"Failed to extract topic via LLM, falling back to simplified query: {e}", file=sys.stderr)
        # Fallback to query cleanup
        words = [w for w in query.lower().split() if w not in ["what", "is", "explain", "how", "does", "why", "the", "a", "an", "about", "?"]]
        return " ".join(words[:2]) if words else "general"

async def orchestrate_study_helper(
    query: str, 
    client_manager: MCPClientManager, 
    llm: LLMHelper, 
    auto_save_note: bool = False
) -> tuple[str, str, str]:
    """
    Orchestrate the dual MCP servers to fetch notes and web research, 
    and synthesize a final response using the LLM.
    
    Returns:
        tuple (synthesized_response, extracted_topic, save_status_message)
    """
    # 1. Extract topic
    topic = await extract_topic(query, llm)
    
    # 2. Get local notes from Notes MCP Server
    local_notes = await client_manager.get_notes(topic)
    notes_context = ""
    if local_notes:
        notes_context = "\n".join([f"- {note}" for note in local_notes])
    else:
        notes_context = "No personal notes saved for this topic yet."
        
    # 3. Get web search summary from Web Research MCP Server
    web_summary = await client_manager.summarize_results(query)
    
    # 4. Merge contexts and draft prompt for LLM aggregator
    prompt = (
        f"You are a helpful study assistant. Synthesize a comprehensive, student-friendly answer for the query: '{query}' "
        f"using the provided local notes and web summaries.\n\n"
        f"TOPIC: {topic}\n\n"
        f"LOCAL NOTES FOUND:\n{notes_context}\n\n"
        f"WEB SUMMARY FOUND:\n{web_summary}\n\n"
        f"Strictly format your response in markdown using the following structure:\n"
        f"## Explanation\n"
        f"(Provide a simple 2-5 line explanation of the topic)\n\n"
        f"## Key Points\n"
        f"- (Key Point 1)\n"
        f"- (Key Point 2)\n"
        f"- (Key Point 3)\n\n"
        f"## From Your Notes\n"
        f"{notes_context if local_notes else '- No existing notes'}\n\n"
        f"## Web Summary\n"
        f"- (Web point 1)\n"
        f"- (Web point 2)\n"
        f"- (Web point 3)\n\n"
        f"## Exam Revision Notes\n"
        f"- (Short, crisp revision bullet points for quick memory recall)\n"
    )
    
    system_instruction = "You are a professional academic study assistant. Compile notes and web knowledge into a unified, structured summary."
    
    # 5. Synthesize final answer
    synthesized_response = llm.generate(prompt=prompt, system_instruction=system_instruction)
    
    # 6. Auto-save synthesized answer to Notes MCP if requested
    save_status = ""
    if auto_save_note:
        # Extract explanation block or save a condensed version
        # Let's save a summary of this query to notes
        summary_to_save = f"Synthesized answer to: '{query}'\n{synthesized_response[:300]}..."
        save_status = await client_manager.save_note(topic, summary_to_save)
        
    return synthesized_response, topic, save_status

# Standalone execution for integration testing
async def main():
    import argparse
    parser = argparse.ArgumentParser(description="StudyMCP Orchestrator CLI")
    parser.add_argument("query", type=str, help="The question to ask")
    parser.add_argument("--save", action="store_true", help="Auto-save answer to notes")
    args = parser.parse_args()
    
    client_manager = MCPClientManager()
    llm = LLMHelper()
    
    try:
        await client_manager.start()
        ans, topic, save_status = await orchestrate_study_helper(args.query, client_manager, llm, args.save)
        print("\n=== RESPONSE ===\n")
        print(ans)
        if save_status:
            print(f"\n[Notes Server]: {save_status}")
    except Exception as e:
        print(f"Orchestrator error: {e}", file=sys.stderr)
    finally:
        await client_manager.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(main())
    else:
        print("Usage: python main.py \"your study question\" [--save]", file=sys.stderr)
