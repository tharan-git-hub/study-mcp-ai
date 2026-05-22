import asyncio
import sys
import os
import json

# Setup sys path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from orchestrator.mcp_client import MCPClientManager

async def test_notes_server(manager: MCPClientManager):
    print("\n--- Testing Notes MCP Server ---")
    topic = "testing_topic"
    content = "This is a test note for verification."
    
    # Save a note
    save_result = await manager.save_note(topic, content)
    print(f"save_note result: {save_result}")
    
    # Get notes
    notes = await manager.get_notes(topic)
    print(f"get_notes result: {notes}")
    
    # Assert correctness
    if content in notes:
        print("[PASS] Notes Server test passed!")
    else:
        print("[FAIL] Notes Server test failed!")

async def test_web_server(manager: MCPClientManager):
    print("\n--- Testing Web Research MCP Server ---")
    query = "quantum computing history"
    
    # Perform search
    search_result = await manager.search_web(query)
    print(f"search_web output snippet (first 300 chars):\n{search_result[:300]}")
    
    if len(search_result) > 50:
        print("[PASS] Web Server search test passed!")
    else:
        print("[FAIL] Web Server search test failed!")

async def main():
    manager = MCPClientManager()
    try:
        await manager.start()
        await test_notes_server(manager)
        await test_web_server(manager)
    except Exception as e:
        print(f"[ERROR] Error running integration tests: {e}")
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
