import os
import json
from fastmcp import FastMCP

# Create the MCP server named "NotesServer"
mcp = FastMCP("NotesServer")

# Resolve the absolute path to the data directory and notes.json file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")

def load_notes() -> dict:
    """Load notes from the JSON file. Initialize if not present."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
        
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Fallback in case of corrupted JSON
        return {}

def save_notes(notes: dict):
    """Save the notes dictionary to the JSON file."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

@mcp.tool()
def save_note(topic: str, content: str) -> str:
    """
    Save a note under a specific topic.
    
    Args:
        topic: The subject matter or category of the note (e.g. 'physics', 'history').
        content: The detailed note content to save.
    """
    if not topic or not content:
        return "Error: Topic and content cannot be empty."
        
    notes = load_notes()
    topic_key = topic.strip().lower()
    
    if topic_key not in notes:
        notes[topic_key] = []
        
    notes[topic_key].append(content.strip())
    save_notes(notes)
    return f"Successfully saved note under topic '{topic}'."

@mcp.tool()
def get_notes(topic: str) -> list[str]:
    """
    Retrieve all saved notes for a specific topic.
    
    Args:
        topic: The topic/category to look up (case-insensitive).
    """
    if not topic:
        return []
        
    notes = load_notes()
    topic_key = topic.strip().lower()
    return notes.get(topic_key, [])

if __name__ == "__main__":
    mcp.run()
