import os
import json
import csv
import argparse

# Resolve paths to match the Notes MCP Server structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")

def load_notes() -> dict:
    """Load notes from the JSON file, initializing if not present."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(NOTES_FILE):
        return {}
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_notes(notes: dict):
    """Save the notes dictionary to the JSON file with clean formatting."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

def add_note_in_memory(notes: dict, topic: str, content: str):
    """Add a note to a topic in memory, ensuring uniqueness."""
    topic_key = topic.strip().lower()
    if not topic_key or not content.strip():
        return
    if topic_key not in notes:
        notes[topic_key] = []
    
    clean_content = content.strip()
    # Avoid exact duplicate notes in the database
    if clean_content not in notes[topic_key]:
        notes[topic_key].append(clean_content)

def import_from_json(json_path: str):
    """Import notes from another JSON file (either dict or list format)."""
    print(f"Importing from JSON: {json_path}")
    if not os.path.exists(json_path):
        print(f"Error: File '{json_path}' does not exist.")
        return
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        notes = load_notes()
        count = 0
        if isinstance(data, dict):
            # Format 1: {"topic_name": ["note 1", "note 2"]} or {"topic_name": "single note content"}
            for topic, contents in data.items():
                if isinstance(contents, list):
                    for content in contents:
                        add_note_in_memory(notes, topic, str(content))
                        count += 1
                elif isinstance(contents, str):
                    add_note_in_memory(notes, topic, contents)
                    count += 1
        elif isinstance(data, list):
            # Format 2: [{"topic": "science", "content": "..."}]
            for item in data:
                if isinstance(item, dict):
                    topic = item.get("topic") or item.get("category")
                    content = item.get("content") or item.get("text") or item.get("note")
                    if topic and content:
                        add_note_in_memory(notes, str(topic), str(content))
                        count += 1
                        
        save_notes(notes)
        print(f"Success: Imported {count} notes from JSON into '{NOTES_FILE}'!")
    except Exception as e:
        print(f"Error reading JSON file: {e}")

def import_from_csv(csv_path: str, topic_col: str, content_col: str):
    """Import notes from a CSV file using mapped headers."""
    print(f"Importing from CSV: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"Error: File '{csv_path}' does not exist.")
        return
    try:
        notes = load_notes()
        count = 0
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if not headers:
                print("Error: CSV has no headers.")
                return
            
            # Match headers case-insensitively
            t_col = next((h for h in headers if h.lower() == topic_col.lower()), headers[0])
            c_col = next((h for h in headers if h.lower() == content_col.lower()), headers[1] if len(headers) > 1 else headers[0])
            
            print(f"Reading CSV columns: Topic='{t_col}', Content='{c_col}'")
            
            for row in reader:
                topic = row.get(t_col)
                content = row.get(c_col)
                if topic and content:
                    add_note_in_memory(notes, topic, content)
                    count += 1
        save_notes(notes)
        print(f"Success: Imported {count} notes from CSV into '{NOTES_FILE}'!")
    except Exception as e:
        print(f"Error reading CSV file: {e}")

def import_from_dir(dir_path: str):
    """Import a directory of text/markdown files (filenames become topics)."""
    print(f"Importing from directory: {dir_path}")
    if not os.path.isdir(dir_path):
        print(f"Error: Directory '{dir_path}' does not exist.")
        return
    
    notes = load_notes()
    count = 0
    for root, _, files in os.walk(dir_path):
        for file in files:
            if file.endswith((".txt", ".md")):
                file_path = os.path.join(root, file)
                topic = os.path.splitext(file)[0]
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if content.strip():
                        add_note_in_memory(notes, topic, content)
                        count += 1
                except Exception as e:
                    print(f"Error reading file '{file}': {e}")
    save_notes(notes)
    print(f"Success: Imported {count} files as notes under their filenames into '{NOTES_FILE}'!")

def import_single_file(file_path: str, topic: str):
    """Import a single text file's contents under a specified topic."""
    print(f"Importing single file: {file_path} under topic '{topic}'")
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return
    try:
        notes = load_notes()
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        if content.strip():
            add_note_in_memory(notes, topic, content)
            save_notes(notes)
            print(f"Success: Imported content of '{file_path}' under topic '{topic}'!")
        else:
            print("Warning: File was empty. No note saved.")
    except Exception as e:
        print(f"Error reading file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Bulk Import Utility for StudyMCP AI Assistant Notes Database")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json", help="Path to a JSON file to import")
    group.add_argument("--csv", help="Path to a CSV file to import")
    group.add_argument("--dir", help="Path to a directory of text/markdown files to import")
    group.add_argument("--file", help="Path to a single text/markdown file to import (requires --topic)")
    
    parser.add_argument("--topic", help="Topic to use for --file import")
    parser.add_argument("--topic-col", default="topic", help="Column name for topic in CSV import (default: 'topic')")
    parser.add_argument("--content-col", default="content", help="Column name for content in CSV import (default: 'content')")
    
    args = parser.parse_args()
    
    if args.file and not args.topic:
        parser.error("--file requires --topic to specify which category to store the note under.")
        
    if args.json:
        import_from_json(args.json)
    elif args.csv:
        import_from_csv(args.csv, args.topic_col, args.content_col)
    elif args.dir:
        import_from_dir(args.dir)
    elif args.file:
        import_single_file(args.file, args.topic)

if __name__ == "__main__":
    main()
