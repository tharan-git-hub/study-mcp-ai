# 🎓 StudyMCP AI Assistant

StudyMCP is a modern AI-powered study assistant built using the **Model Context Protocol (MCP)**.

It combines:

- 📚 Personal knowledge from local notes/files
- 🌐 Real-time web research
- 🤖 LLM-powered synthesis (Gemini/OpenAI)
- 🎨 Interactive Gradio interface

The system demonstrates **multi-server MCP orchestration**, where multiple MCP servers collaborate to generate intelligent, structured learning responses.

---

# ✨ Features

## 🧠 Dual MCP Server Architecture
StudyMCP integrates two independent MCP servers:

| Server | Purpose |
|---|---|
| MCP Server 1 | Local notes & saved knowledge retrieval |
| MCP Server 2 | Web research & external information gathering |

---

## 🔍 Smart Topic Extraction
Automatically extracts the core study topic from natural language queries.

Example:

```txt
"Explain quantum entanglement in simple terms"
```

→ Extracted Topic:

```txt
Quantum Entanglement
```

---

## 🌐 Web Research with Fallback Support
- DuckDuckGo-based web search
- Wikipedia fallback mechanism
- Reliable retrieval for educational topics

---

## ⚙️ Dynamic LLM Configuration
Supports multiple LLM providers:

- Google Gemini
- OpenAI

Configure directly from the UI without editing code.

---

## 📝 Notes Management System
Built-in note management features:

- Browse stored notes
- View saved topics
- Delete notes
- Add custom notes manually

---

## 💾 Auto-Save Learning Memory
Generated study answers can be automatically saved for future learning sessions.

---

# 🏗️ System Architecture

```txt
User (Gradio UI)
      ↓
Orchestrator (Python Backend)
      ↓
--------------------------------------
| MCP Server 1: Notes Server         |
| MCP Server 2: Web Research Server  |
--------------------------------------
      ↓
LLM Context Aggregator
(Gemini / OpenAI)
      ↓
Structured Markdown Response
```

---

# 🛠️ Tech Stack

| Technology | Usage |
|---|---|
| Python | Backend |
| MCP | Server-Client orchestration |
| Gradio | User Interface |
| Gemini API | LLM provider |
| OpenAI API | Alternative LLM provider |
| DuckDuckGo Search | Web retrieval |
| Markdown | Structured response formatting |

---

# 📂 Project Structure

```txt
study-mcp-ai/
│
├── orchestrator/
│   ├── main.py
│   └── ...
│
├── servers/
│   ├── notes_server/
│   ├── web_research_server/
│   └── ...
│
├── ui/
│   └── gradio_app.py
│
├── memory/
├── notes/
├── requirements.txt
├── README.md
└── test_mcp_system.py
```

---

# 🚀 Installation

## 1️⃣ Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/study-mcp-ai.git
cd study-mcp-ai
```

---

## 2️⃣ Create Virtual Environment

### Windows

```powershell
python -m venv venv
.\venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Configure API Keys

Create a `.env` file in the project root:

```env
LLM_PROVIDER=gemini

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL_NAME=gemini-1.5-flash

# OpenAI Alternative
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_openai_api_key
# OPENAI_MODEL_NAME=gpt-4o-mini
```

---

# ▶️ Run the Application

Launch the Gradio UI:

```bash
python ui/gradio_app.py
```

Application runs at:

```txt
http://127.0.0.1:7860
```

---

# 🧪 Testing

## MCP Integration Test

```bash
python test_mcp_system.py
```

---

## Run Orchestrator Directly

```bash
python orchestrator/main.py "Explain quantum entanglement" --save
```

---

# 📸 Example Workflow

1. User asks a study question
2. MCP Notes Server searches personal knowledge
3. MCP Web Server gathers online context
4. LLM synthesizes both sources
5. Structured markdown study response is generated

---

# 🎯 Example Queries

```txt
Explain transformers in deep learning
```

```txt
What is quantum computing?
```

```txt
Create a study plan for operating systems
```

```txt
Summarize reinforcement learning
```

---

# 🌟 Why This Project Matters

StudyMCP demonstrates:

- Practical MCP architecture
- Multi-agent/tool orchestration
- AI-assisted learning systems
- Real-world LLM integration
- Retrieval-augmented educational workflows

This project is ideal for learning:

- MCP development
- AI orchestration systems
- Gradio app deployment
- Tool-calling workflows
- Educational AI systems

---

# 🤝 Contributing

Contributions are welcome.

You can contribute by:

- Improving MCP orchestration
- Adding new tools/servers
- Enhancing UI/UX
- Optimizing retrieval systems
- Adding memory/vector search support

---

# 📜 License

MIT License

---

# 👨‍💻 Author

Tharan A
