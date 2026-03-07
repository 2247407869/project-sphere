# Project Sphere 🧠

> A local-first AI assistant with a three-tier memory architecture — designed to remember, reflect, and evolve alongside you.

**Tech Stack**: Python · FastAPI · DeepSeek V3 · Gemini Flash · WebDAV · Docker

---

## Architecture: Triple Memory System

```
┌──────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│              (Responsive Web UI · Mobile-Ready)              │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    FastAPI Core Server                        │
│   Function Calling Loop · Tool Dispatcher · Stream Router    │
└──────┬───────────────────┬──────────────────────┬────────────┘
       │                   │                      │
┌──────▼───────┐  ┌────────▼──────────┐  ┌───────▼──────────┐
│  M1: Working │  │  M2: Dynamic      │  │  M3: Long-Term   │
│    Memory    │  │    Summary        │  │    Memory        │
│              │  │                   │  │                  │
│  Current     │  │  Reflective       │  │  Persistent      │
│  conversation│  │  consolidation    │  │  Markdown files  │
│  context     │  │  of past sessions │  │  on WebDAV cloud │
└──────────────┘  └───────────────────┘  └──────────────────┘
```

### Memory Layers

| Layer | Name | Description |
|-------|------|-------------|
| **M1** | Working Memory | In-request conversation context |
| **M2** | Dynamic Summary | Reflective compression of past dialogues — simulating human sleep-phase memory consolidation |
| **M3** | Long-Term Memory | Persistent, topic-sharded Markdown files stored on personal WebDAV cloud |

---

## Key Features

- **🔄 Automatic Daily Archive**: Each session is automatically consolidated into an M2 summary and key facts are extracted to M3 — no manual effort required
- **🛠️ Function Calling Agent Loop**: Built-in memory tools (`fetch_memory`, `patch_memory`) called by the LLM to read/write long-term knowledge
- **👁️ Multimodal Support**: Image analysis via Gemini Flash, text reasoning via DeepSeek V3
- **☁️ Privacy-First Storage**: All long-term memory stored on user-controlled WebDAV (InfiniCloud), not third-party databases
- **📱 Mobile-Ready UI**: Responsive frontend with streaming responses and session management
- **🐳 Docker Ready**: Full containerized deployment with Docker Compose

---

## Project Structure

```
project-sphere/
├── main.py                 # FastAPI server, API routes, agent loop
├── src/
│   ├── agents/
│   │   ├── dispatcher.py         # Tool call routing
│   │   ├── memory_patcher.py     # M3 memory write agent
│   │   ├── memory_tools.py       # M3 memory read tools
│   │   ├── daily_archive.py      # M2 consolidation agent
│   │   ├── knowledge_agent.py    # Knowledge retrieval
│   │   └── thinking_tool_stream.py  # Streaming inference
│   ├── storage/            # WebDAV sync manager
│   └── utils/
├── frontend/
│   ├── index.html          # Main chat interface
│   └── debug.html          # Memory debug panel
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/2247407869/project-sphere.git
cd project-sphere
cp .env.example .env
# Fill in your API keys in .env
docker-compose up -d
```

Open `http://localhost:8000` in your browser.

### Option 2: Local Development

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys
uvicorn main:app --reload --port 8000
```

---

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```env
# LLM
DEEPSEEK_API_KEY=your_deepseek_api_key

# Long-term memory storage (WebDAV)
INFINICLOUD_URL=https://your-webdav-server.com/dav
INFINICLOUD_USER=your_username
INFINICLOUD_PASS=your_password
```

---

## Design Motivation

Most AI assistants reset with every conversation. Project Sphere is designed differently:

- **M2 (Dynamic Summary)** uses a *reflective consolidation* model — rather than mechanically compressing text, it simulates how humans integrate and re-prioritize experiences during sleep, producing new insight each day
- **M3 (Long-Term Memory)** supports *auto-sharding* — the system automatically creates new topic-specific files as knowledge domains expand, enabling organic growth of the knowledge base
- The entire memory stack runs **locally or on user-owned infrastructure**, preserving data sovereignty

---

## Background

This project grew from a personal frustration: every time I started a new chat session, the AI had forgotten everything. I wanted a system that genuinely *remembered* — not just context-window tricks, but structured, persistent, searchable memory.

Built and iterated on through 2025-2026 as a personal infrastructure project.

---

## License

MIT