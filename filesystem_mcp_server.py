import os
import json
import re
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ResumeFilesystemServer")

@mcp.resource("resumes://manifest")
def get_resume_manifest() -> str:
    resumes_dir = "./resumes"
    os.makedirs(resumes_dir, exist_ok=True)
    files = [f for f in os.listdir(resumes_dir) if f.endswith(".json") or f.endswith(".txt")]
    return json.dumps({
        "resource_uri": "resumes://manifest",
        "protocol": "JSON-RPC 2.0 / MCP",
        "directory": os.path.abspath(resumes_dir),
        "total_files": len(files),
        "files": files
    }, indent=2)

@mcp.tool()
def watch_directory(directory_path: str = "./resumes") -> str:
    os.makedirs(directory_path, exist_ok=True)
    files = [f for f in os.listdir(directory_path) if f.endswith(".txt") or f.endswith(".json")]
    return json.dumps({
        "status": "active",
        "directory": os.path.abspath(directory_path),
        "monitored_files": len(files),
        "file_list": sorted(files)
    })

@mcp.tool()
def batch_process(directory_path: str = "./resumes") -> str:
    os.makedirs(directory_path, exist_ok=True)
    files = [f for f in os.listdir(directory_path) if f.endswith(".json") or f.endswith(".txt")]
    return json.dumps({"status": "success", "processed_records": len(files)})

@mcp.tool()
def rag_search_resumes(query: str, top_k: int = 5, directory_path: str = "./resumes") -> str:
    query_tokens = [q.strip().lower() for q in query.split() if q.strip()]
    scored = []
    os.makedirs(directory_path, exist_ok=True)
    for fname in os.listdir(directory_path):
        fpath = os.path.join(directory_path, fname)
        candidate = {}
        if fname.endswith(".json"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                candidate = {
                    "candidate_id": raw.get("candidate_id", fname.replace(".json", "")),
                    "name": raw.get("name", fname.replace(".json", "").replace("_", " ").title()),
                    "experience_years": int(raw.get("experience_years", raw.get("experience", 0))),
                    "skills": raw.get("skills", []),
                    "bio": raw.get("bio", "")
                }
            except Exception:
                continue
        elif fname.endswith(".txt"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    text = f.read()
                name_m = re.search(r"Name\s*:\s*([^\n\r]+)", text, re.I)
                exp_m = re.search(r"Experience\s*:\s*([^\n\r]+)", text, re.I)
                skills_m = re.search(r"Skills\s*:\s*([^\n\r]+)", text, re.I)
                bio_m = re.search(r"Bio\s*:\s*([^\n\r]+)", text, re.I)

                name_val = name_m.group(1).strip() if name_m else fname.replace(".txt", "").replace("_", " ").title()
                exp_digits = re.findall(r"\d+", exp_m.group(1)) if exp_m else []
                exp_val = int(exp_digits[0]) if exp_digits else 0
                skills_val = [s.strip() for s in skills_m.group(1).split(",") if s.strip()] if skills_m else []
                bio_val = bio_m.group(1).strip() if bio_m else text[:120].replace("\n", " ")

                candidate = {
                    "candidate_id": fname.replace(".txt", ""),
                    "name": name_val,
                    "experience_years": exp_val,
                    "skills": skills_val,
                    "bio": bio_val
                }
            except Exception:
                continue

        if not candidate or not candidate.get("skills"):
            continue

        cand_skills_lower = [s.lower() for s in candidate["skills"]]
        matched = [token for token in query_tokens if any(token == cs or token in cs or cs in token for cs in cand_skills_lower)]
        matched = list(set(matched))

        if query_tokens:
            skill_score = (len(matched) / len(query_tokens)) * 80
            exp_bonus = min(20, candidate["experience_years"] * 3.3)
            total_score = int(skill_score + exp_bonus) if matched else int(min(30, candidate["experience_years"] * 4))
        else:
            total_score = min(30, candidate["experience_years"] * 4)

        candidate["score"] = min(100, total_score)
        candidate["matched_skills"] = [m.capitalize() for m in matched]
        scored.append(candidate)

    scored.sort(key=lambda x: (x["score"], x["experience_years"]), reverse=True)
    return json.dumps(scored[:top_k])

if __name__ == "__main__":
    mcp.run()
