# Autonomous MCP Resume Screening & Ranking Agent

An autonomous candidate screening system powered by the **Model Context Protocol (MCP)** and **LangGraph**.

## Features
- **FastMCP Server**: Implements `watch_directory()`, `batch_process()`, and `rag_search_resumes()`.
- **JSON-RPC 2.0 Resource Discovery**: Exposes manifest metadata via `resumes://manifest`.
- **LangGraph Orchestrator**: Extracts requirements, queries the MCP tools dynamically, and scores candidate overlap.
- **Physical Disk Storage**: Reads structured candidate files directly from `./resumes`.

## Deliverables Included
- `filesystem_mcp_server.py`: FastMCP server implementation.
- `matching_agent.py`: LangGraph state machine with MCP client integration.
- `ARCHITECTURE_STATE_DIAGRAM.md`: System sequence diagram and workflow specification.
- `resumes/`: Candidate resume repository containing `.txt` and `.json` profiles.

## Setup & Execution
```bash
# 1. Install dependencies
pip install "mcp<2" langgraph langchain nest_asyncio gradio

# 2. Run the agent
python matching_agent.py
