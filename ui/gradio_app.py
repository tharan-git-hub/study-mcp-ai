import asyncio
import os
import sys
import json
import time
import gradio as gr
from dotenv import load_dotenv

# Add project root to python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from orchestrator.llm import LLMHelper
from orchestrator.mcp_client import MCPClientManager
from orchestrator.main import orchestrate_study_helper

# Load environment variables
load_dotenv()

# Initialize global MCP client manager
client_manager = MCPClientManager()

# Helper to read topics for Notes Tab dropdown
def get_all_topics():
    notes_file = os.path.join(BASE_DIR, "data", "notes.json")
    if not os.path.exists(notes_file):
        return []
    try:
        with open(notes_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return sorted(list(data.keys()))
    except Exception:
        return []

# Helper to get notes content for a topic
def get_notes_for_topic(topic):
    if not topic:
        return "Please select a topic."
    notes_file = os.path.join(BASE_DIR, "data", "notes.json")
    if not os.path.exists(notes_file):
        return "No notes found."
    try:
        with open(notes_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            notes_list = data.get(topic.strip().lower(), [])
            if not notes_list:
                return f"No notes found under topic '{topic}'."
            formatted = []
            for idx, note in enumerate(notes_list, 1):
                formatted.append(f"### Note #{idx}\n{note}\n---\n")
            return "\n".join(formatted)
    except Exception as e:
        return f"Error loading notes: {e}"

# UI Theme CSS
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

body, .gradio-container {
    font-family: 'Outfit', sans-serif !important;
    background: radial-gradient(circle at top right, #150f2e, #07040e) !important;
    color: #e2e8f0 !important;
}

.header-container {
    text-align: center;
    padding: 2rem 1rem;
    margin-bottom: 1.5rem;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
}

.header-title {
    font-size: 2.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #f43f5e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    letter-spacing: -0.04em;
}

.header-subtitle {
    font-size: 1.05rem;
    color: #94a3b8;
}

.glass-panel {
    background: rgba(24, 20, 39, 0.5) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.25) !important;
}

.primary-btn {
    background: linear-gradient(135deg, #8b5cf6, #ec4899) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.2rem !important;
    transition: transform 0.2s, box-shadow 0.2s !important;
    cursor: pointer;
}

.primary-btn:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4) !important;
}

.secondary-btn {
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #f8fafc !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.2rem !important;
    transition: background-color 0.2s !important;
}

.secondary-btn:hover {
    background: rgba(255, 255, 255, 0.15) !important;
}

.status-box {
    padding: 0.75rem;
    border-radius: 8px;
    font-size: 0.9rem;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.status-online {
    background: rgba(16, 185, 129, 0.1);
    color: #34d399;
}

.status-offline {
    background: rgba(239, 68, 68, 0.1);
    color: #f87171;
}

.markdown-output {
    background: rgba(10, 8, 20, 0.4);
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.03);
}
"""

async def ask_question(question, auto_save):
    """Orchestrate study assistant response generation."""
    if not question.strip():
        return "Please enter a valid study question.", "N/A", "N/A", "Please ask a question first."
        
    start_time = time.time()
    
    # Check server status
    if not client_manager.is_running:
        try:
            await client_manager.start()
        except Exception as e:
            return (
                f"Error initializing MCP Servers: {e}\n\nPlease check API configuration and reload connection in the Settings tab.",
                "N/A",
                "N/A",
                "Connection failed."
            )
            
    try:
        llm = LLMHelper()
        response, topic, save_status = await orchestrate_study_helper(
            query=question,
            client_manager=client_manager,
            llm=llm,
            auto_save_note=auto_save
        )
        duration = f"{time.time() - start_time:.2f} seconds"
        
        save_info = "Not saved"
        if auto_save:
            save_info = save_status or "Saved to Notes successfully."
            
        return response, topic, duration, save_info
    except Exception as e:
        return (
            f"An error occurred while generating study notes:\n\n{e}\n\n"
            "This is usually caused by a missing API Key. Please add one in the Settings tab.",
            "N/A",
            f"{time.time() - start_time:.2f}s",
            f"Failed: {e}"
        )

# Settings configuration functions
def check_server_status():
    if client_manager.is_running:
        return (
            "🟢 Connected & Ready", 
            "🟢 Online (save_note, get_notes)", 
            "🟢 Online (search_web, summarize_results)"
        )
    return "🔴 Offline (Reconnect required)", "🔴 Offline", "🔴 Offline"

def load_settings():
    load_dotenv()
    provider = os.environ.get("LLM_PROVIDER", "gemini")
    
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    
    current_key = openai_key if provider == "openai" else gemini_key
    gemini_model = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")
    openai_model = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")
    
    return provider, current_key, gemini_model, openai_model

async def save_settings_and_reload(provider, api_key, gemini_model, openai_model):
    env_path = os.path.join(BASE_DIR, ".env")
    lines = []
    
    # Read existing env file if present
    existing_env = {}
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    existing_env[k.strip()] = v.strip()
                    
    # Update values
    existing_env["LLM_PROVIDER"] = provider
    if provider == "openai":
        existing_env["OPENAI_API_KEY"] = api_key
        existing_env["OPENAI_MODEL_NAME"] = openai_model
        # Preserve gemini key if existed
    else:
        existing_env["GEMINI_API_KEY"] = api_key
        existing_env["GEMINI_MODEL_NAME"] = gemini_model
        
    # Write to env
    for k, v in existing_env.items():
        lines.append(f"{k}={v}")
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
        
    # Set in os.environ for current process
    os.environ["LLM_PROVIDER"] = provider
    if provider == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_MODEL_NAME"] = openai_model
    else:
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GEMINI_MODEL_NAME"] = gemini_model
        
    # Restart the client manager
    try:
        await client_manager.start()
        return "🟢 Settings saved. MCP Servers reconnected successfully!", *check_server_status()
    except Exception as e:
        return f"🔴 Saved config, but failed to start MCP servers: {e}", *check_server_status()

# Notes tab operations
async def add_manual_note(topic, note_content):
    if not topic.strip() or not note_content.strip():
        return "Topic and content cannot be empty.", gr.update(choices=get_all_topics())
    
    # Use client manager if running
    if client_manager.is_running:
        status = await client_manager.save_note(topic, note_content)
    else:
        # Fallback to direct write if server not active
        notes_file = os.path.join(BASE_DIR, "data", "notes.json")
        try:
            data = {}
            if os.path.exists(notes_file):
                with open(notes_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            
            t_key = topic.strip().lower()
            if t_key not in data:
                data[t_key] = []
            data[t_key].append(note_content.strip())
            
            with open(notes_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            status = f"Saved manually to notes.json under '{topic}'."
        except Exception as e:
            status = f"Failed to save note: {e}"
            
    # Return status and refresh topics dropdown list
    return status, gr.update(choices=get_all_topics(), value=topic.strip().lower())

def delete_topic_notes(topic):
    if not topic:
        return "Please select a topic to delete.", gr.update(choices=get_all_topics(), value=None)
    notes_file = os.path.join(BASE_DIR, "data", "notes.json")
    if not os.path.exists(notes_file):
        return "No notes file found.", gr.update(choices=get_all_topics())
    try:
        with open(notes_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        t_key = topic.strip().lower()
        if t_key in data:
            del data[t_key]
            with open(notes_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return f"Deleted all notes for topic '{topic}'.", gr.update(choices=get_all_topics(), value=None)
        return f"Topic '{topic}' not found in database.", gr.update(choices=get_all_topics())
    except Exception as e:
        return f"Error deleting topic: {e}", gr.update(choices=get_all_topics())

# Build the Gradio interface
def build_ui():
    init_provider, init_key, init_gemini_model, init_openai_model = load_settings()
    
    with gr.Blocks(title="StudyMCP AI Assistant") as app:
        # Header HTML
        gr.HTML(
            """
            <div class="header-container">
                <h1 class="header-title">⚡ StudyMCP AI Assistant</h1>
                <p class="header-subtitle">Orchestrated personal notes and live web research using Model Context Protocol (MCP)</p>
            </div>
            """
        )
        
        with gr.Tabs():
            # TAB 1: Study Assistant
            with gr.Tab("Study Assistant"):
                with gr.Row():
                    with gr.Column(scale=2):
                        with gr.Group(elem_classes="glass-panel"):
                            gr.Markdown("### 🔍 Ask Your Question")
                            question_input = gr.Textbox(
                                label="Enter your question or study topic",
                                placeholder="e.g. Explain photosynthesis and how chlorophyll works",
                                lines=3
                            )
                            auto_save_chk = gr.Checkbox(
                                label="Auto-save synthesized notes to local database",
                                value=True
                            )
                            ask_btn = gr.Button("Ask Assistant", elem_classes="primary-btn")
                            
                        with gr.Group(elem_classes="glass-panel", visible=True):
                            gr.Markdown("### 📊 Metadata & Performance")
                            with gr.Row():
                                meta_topic = gr.Textbox(label="Identified Topic", interactive=False)
                                meta_time = gr.Textbox(label="Execution Time", interactive=False)
                            meta_save = gr.Textbox(label="Database Save Status", interactive=False)
                            
                    with gr.Column(scale=3):
                        with gr.Group(elem_classes="glass-panel"):
                            gr.Markdown("### 🎓 Synthesized Study Materials")
                            output_markdown = gr.Markdown(
                                value="*Your aggregated study notes will appear here. Ask a question to begin.*",
                                elem_classes="markdown-output"
                            )
                            
                # Connect events
                ask_btn.click(
                    fn=ask_question,
                    inputs=[question_input, auto_save_chk],
                    outputs=[output_markdown, meta_topic, meta_time, meta_save]
                )
                
            # TAB 2: Notes Database Manager
            with gr.Tab("Notes Database"):
                with gr.Row():
                    with gr.Column(scale=2):
                        with gr.Group(elem_classes="glass-panel"):
                            gr.Markdown("### 📂 Saved Topics")
                            topic_dropdown = gr.Dropdown(
                                choices=get_all_topics(),
                                label="Select topic to view",
                                interactive=True,
                                value=None
                            )
                            refresh_btn = gr.Button("Refresh List", elem_classes="secondary-btn")
                            delete_btn = gr.Button("Delete Topic & Notes", variant="stop")
                            
                        with gr.Group(elem_classes="glass-panel"):
                            gr.Markdown("### ➕ Add New Note Manually")
                            new_topic = gr.Textbox(
                                label="Topic name", 
                                placeholder="e.g. physics, cell division"
                            )
                            new_note_content = gr.Textbox(
                                label="Note Content", 
                                placeholder="Enter facts, definitions, or study notes...",
                                lines=5
                            )
                            save_note_btn = gr.Button("Save Note", elem_classes="primary-btn")
                            note_save_status = gr.Textbox(label="Action Status", interactive=False)
                            
                    with gr.Column(scale=3):
                        with gr.Group(elem_classes="glass-panel"):
                            gr.Markdown("### 📝 Notes List")
                            notes_view = gr.Markdown(
                                value="*Select a topic from the list to view its contents.*",
                                elem_classes="markdown-output"
                            )
                            
                # Connect database events
                topic_dropdown.change(
                    fn=get_notes_for_topic,
                    inputs=[topic_dropdown],
                    outputs=[notes_view]
                )
                
                refresh_btn.click(
                    fn=lambda: gr.update(choices=get_all_topics()),
                    inputs=[],
                    outputs=[topic_dropdown]
                )
                
                save_note_btn.click(
                    fn=add_manual_note,
                    inputs=[new_topic, new_note_content],
                    outputs=[note_save_status, topic_dropdown]
                )
                
                delete_btn.click(
                    fn=delete_topic_notes,
                    inputs=[topic_dropdown],
                    outputs=[note_save_status, topic_dropdown]
                )
                
            # TAB 3: Configuration & Server Management
            with gr.Tab("API Configuration"):
                with gr.Group(elem_classes="glass-panel"):
                    gr.Markdown("### 🔌 Model Context Protocol Server Status")
                    with gr.Row():
                        status_mcp = gr.Textbox(label="Client Connection", value="Initializing...", interactive=False)
                        status_notes = gr.Textbox(label="Notes Server", value="Initializing...", interactive=False)
                        status_web = gr.Textbox(label="Web Server", value="Initializing...", interactive=False)
                    check_status_btn = gr.Button("Refresh Connection Status", elem_classes="secondary-btn")
                    
                with gr.Group(elem_classes="glass-panel"):
                    gr.Markdown("### 🔑 LLM Provider & API Keys")
                    
                    provider_radio = gr.Radio(
                        choices=["gemini", "openai"],
                        label="LLM Provider",
                        value=init_provider
                    )
                    
                    api_key_input = gr.Textbox(
                        label="API Key",
                        value=init_key,
                        placeholder="Paste your Gemini or OpenAI API Key here...",
                        type="password"
                    )
                    
                    with gr.Row():
                        gemini_model_input = gr.Textbox(
                            label="Gemini Model Name",
                            value=init_gemini_model,
                            placeholder="e.g. gemini-2.5-flash"
                        )
                        openai_model_input = gr.Textbox(
                            label="OpenAI Model Name",
                            value=init_openai_model,
                            placeholder="e.g. gpt-4o-mini"
                        )
                        
                    save_config_btn = gr.Button("Save Config & Restart MCP Servers", elem_classes="primary-btn")
                    config_save_msg = gr.Textbox(label="Status Message", interactive=False)
                    
                # Settings events
                check_status_btn.click(
                    fn=check_server_status,
                    inputs=[],
                    outputs=[status_mcp, status_notes, status_web]
                )
                
                save_config_btn.click(
                    fn=save_settings_and_reload,
                    inputs=[provider_radio, api_key_input, gemini_model_input, openai_model_input],
                    outputs=[config_save_msg, status_mcp, status_notes, status_web]
                )
                
                # Update key input label based on provider change
                def update_key_label(prov):
                    env_val = ""
                    if prov == "openai":
                        env_val = os.environ.get("OPENAI_API_KEY", "")
                        return gr.update(label="OpenAI API Key", value=env_val, placeholder="sk-...")
                    else:
                        env_val = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
                        return gr.update(label="Gemini API Key", value=env_val, placeholder="AIzaSy...")
                        
                provider_radio.change(
                    fn=update_key_label,
                    inputs=[provider_radio],
                    outputs=[api_key_input]
                )
                
        # Handle onload event to initialize MCP client connection
        async def on_load():
            try:
                await client_manager.start()
                return check_server_status()
            except Exception as e:
                print(f"Error on application load: {e}", file=sys.stderr)
                return "🔴 Connection Error", "🔴 Offline", "🔴 Offline"
                
        app.load(
            fn=on_load,
            inputs=[],
            outputs=[status_mcp, status_notes, status_web]
        )
        
    return app

if __name__ == "__main__":
    app = build_ui()
    # Run locally on default port 7860
    app.queue().launch(server_name="127.0.0.1", server_port=7860, share=False, css=custom_css)
