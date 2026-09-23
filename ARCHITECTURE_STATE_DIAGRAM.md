# Agent <-> MCP State Machine & Architecture

```mermaid
sequenceDiagram
    autonumber
    actor User as Recruiter / Client
    participant Agent as LangGraph Agent (matching_agent.py)
    participant MCP as FastMCP Server (filesystem_mcp_server.py)
    participant Disk as Local Resumes (./resumes)

    User->>Agent: Submit Job Description
    Agent->>Agent: parse_jd_node: Extract skills
    Agent->>MCP: Call tool: batch_process("./resumes")
    MCP->>Disk: Scan & validate candidate files
    Disk-->>MCP: Candidate records
    MCP-->>Agent: {"status": "success", "processed_records": N}
    Agent->>MCP: Call tool: rag_search_resumes(query, top_k)
    MCP->>MCP: Skill overlap scoring & experience weighting
    MCP-->>Agent: JSON candidate leaderboard
    Agent->>Agent: rank_candidates_node: Generate Markdown report
    Agent-->>User: Display Leaderboard & MCP Logs
