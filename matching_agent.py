import asyncio
import json
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from filesystem_mcp_server import mcp as server_app

def extract_payload(res: Any) -> Any:
    if isinstance(res, tuple) and len(res) > 0:
        res = res[0]
    if isinstance(res, list) and len(res) > 0:
        item = res[0]
        text = getattr(item, "text", getattr(item, "content", str(item)))
    else:
        text = getattr(res, "text", getattr(res, "content", str(res)))
    try:
        return json.loads(text)
    except Exception:
        return text

async def mcp_call(tool_name: str, arguments: dict):
    raw = await server_app.call_tool(tool_name, arguments)
    return extract_payload(raw)

class AgentState(TypedDict):
    job_description: str
    requirements: Dict[str, Any]
    candidate_pool: List[Dict[str, Any]]
    ranking_report: str
    feedback: str
    mcp_logs: List[str]

def parse_jd_node(state: AgentState) -> Dict[str, Any]:
    jd = state.get("job_description", "").lower()
    skill_catalog = ["kubernetes", "terraform", "docker", "langgraph", "fastapi", "chromadb", "pytorch", "postgresql", "react", "flask", "langchain", "python"]
    detected = [s for s in skill_catalog if s in jd]
    if not detected:
        detected = ["python"]
    return {
        "requirements": {"skills": detected},
        "mcp_logs": state.get("mcp_logs", []) + [f"[LangGraph] Parsed skills: {[d.capitalize() for d in detected]}"]
    }

def mcp_search_resumes_node(state: AgentState) -> Dict[str, Any]:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    reqs = state.get("requirements", {})
    query = " ".join(reqs.get("skills", ["python"]))
    _ = loop.run_until_complete(mcp_call("batch_process", {"directory_path": "./resumes"}))
    candidates = loop.run_until_complete(mcp_call("rag_search_resumes", {"query": query, "top_k": 5}))
    if isinstance(candidates, str):
        try:
            candidates = json.loads(candidates)
        except Exception:
            candidates = []
    return {
        "candidate_pool": candidates,
        "mcp_logs": state.get("mcp_logs", []) + [f"[MCP Server] Query '{query}' returned {len(candidates)} records."]
    }

def rank_candidates_node(state: AgentState) -> Dict[str, Any]:
    candidates = state.get("candidate_pool", [])
    if isinstance(candidates, str):
        try:
            candidates = json.loads(candidates)
        except Exception:
            candidates = []
    lines = [
        "| Rank | Candidate | Experience | Match Score | Matched Skills | Verdict |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]
    for idx, c in enumerate(candidates, 1):
        score = c.get("score", 0)
        verdict = "Strong Hire" if score >= 75 else ("Hire" if score >= 50 else "Not Suitable")
        matched = ", ".join(c.get("matched_skills", [])) or "None"
        lines.append(f"| #{idx} | **{c.get('name', 'Unknown')}** | {c.get('experience_years', 0)} yrs | **{score}/100** | {matched} | `{verdict}` |")
    return {
        "ranking_report": "\n".join(lines),
        "mcp_logs": state.get("mcp_logs", []) + ["[LangGraph] Generated executive markdown leaderboard."]
    }

workflow = StateGraph(AgentState)
workflow.add_node("parse_jd", parse_jd_node)
workflow.add_node("mcp_search_resumes", mcp_search_resumes_node)
workflow.add_node("rank_candidates", rank_candidates_node)
workflow.add_edge(START, "parse_jd")
workflow.add_edge("parse_jd", "mcp_search_resumes")
workflow.add_edge("mcp_search_resumes", "rank_candidates")
workflow.add_edge("rank_candidates", END)
screening_agent = workflow.compile()
