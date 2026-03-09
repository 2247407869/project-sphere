# Project Sphere 🧠

> A local-first AI assistant with a three-tier memory architecture — designed to remember, reflect, and evolve alongside you.

**Tech Stack**: Python · FastAPI · DeepSeek V3 · Gemini Flash · WebDAV · Docker

---

## 🏗️ Architecture: Triple Memory System

```
┌──────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│              (Responsive Web UI · Mobile-Ready)              │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│                    FastAPI Core Server                       │
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

### Memory Layers Defined

| Layer | Name | Description |
|-------|------|-------------|
| **M1** | Working Memory | In-request conversation context. Purely local to the current active session. |
| **M2** | Dynamic Summary | Reflective compression of past dialogues. Unlike mechanical chunking, M2 simulates human sleep-phase memory consolidation—extracting daily insights, emotional tones, and actionable directives, producing synthesis rather than mere summarization. |
| **M3** | Long-Term Memory | Persistent, auto-sharding Markdown files stored on a personal WebDAV cloud. The `MemoryPatcher` agent actively filters for high-entropy information (decision rationales, nuanced preferences, strategic goals) and organically creates new topic files as knowledge domains expand. |

---

## ✨ Key Features

- **🔄 Automatic Daily Context Integration**: Each session is automatically consolidated into an M2 summary, while key facts are extracted to M3 without any manual prompting.
- **🛠️ Self-Driven Agent Loop**: Features a built-in tool dispatcher where the LLM can autonomously invoke `fetch_memory` and `patch_memory` to read and write to its long-term knowledge base mid-conversation.
- **👁️ Multimodal Routing**: Automatically routes vision tasks (image analysis) to Gemini 3 Flash for optimal cost-performance, while delegating heavy text reasoning to DeepSeek V3.
- **☁️ Data Sovereignty**: All long-term memories (M3) are stored as raw Markdown files on user-controlled WebDAV infrastructure (e.g., InfiniCloud). No vendor lock-in, no third-party vector databases.
- **🐳 Docker Native**: Ships with a ready-to-use `docker-compose.yml` for instant isolated deployment.

---

## 🚀 Quick Start (Docker)

The fastest way to get Project Sphere running is via Docker.

```bash
git clone https://github.com/2247407869/memory-v1.git
cd memory-v1

# Copy and configure environment variables
cp .env.example .env
```

Edit your `.env` file to include your API keys and WebDAV credentials:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key
INFINICLOUD_URL=https://your-webdav-server.com/dav
INFINICLOUD_USER=your_username
INFINICLOUD_PASS=your_password
```

Boot the ecosystem:
```bash
docker-compose up -d
```
Access the responsive web interface at `http://localhost:8000`.

---

## 📂 Project Structure

```text
memory-v1/
├── main.py                 # Core FastAPI server & Agent routing loop
├── src/
│   ├── agents/
│   │   ├── dispatcher.py         # Autonomous tool routing
│   │   ├── memory_patcher.py     # M3 write agent (Knowledge extraction)
│   │   ├── memory_tools.py       # M3 read agent (Retrieval)
│   │   ├── daily_archive.py      # M2 consolidation agent
│   │   └── thinking_tool_stream.py # Streaming response handler
│   ├── storage/            # WebDAV synchronization manager
│   └── utils/
├── frontend/
│   ├── index.html          # Vanilla JS/HTML mobile-ready chat UI
│   └── debug.html          # Introspection panel for checking M1/M2/M3 states
├── Dockerfile
└── docker-compose.yml
```

---

## 💡 The "State Hydration" Problem

This architecture was specifically engineered to solve the **"State Hydration Penalty"** inherent in serverless AI agents. Constantly retrieving massive, unstructured conversation logs from cold storage introduces unbearable latency.

By decoupling memory into M1/M2/M3:
1. **M1** is kept instantly available in local memory.
2. **M2** acts as a highly compressed, predictive prefetch cache.
3. **M3** is lazy-loaded via explicit tool calls only when the agent realizes it needs deep historical context.

*(This exact architecture serves as the experimental blueprint for my ongoing research into predictive state prefetching for resource-constrained clusters.)*

---

## 📄 License
MIT License