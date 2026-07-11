"""
backend/main.py

AutoLaunch AI Agent — main entry point.
Runs the full pipeline: Analyze -> GitHub -> Vercel Deploy -> PRD + Content

Run with:
    uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from backend.github.analyzer import analyze, AnalyzerError
from backend.github.github_client import GitHubClient, GitHubClientError, github_client
from backend.deployment.vercel_client import vercel_client, VercelClientError
from backend.ai.project_summary import build_summary, ProjectSummaryError
from backend.ai.ai_engine import engine, AIEngineError
from backend.schemas import GenerateRequest, GenerateResponse
from backend.config import settings

app = FastAPI(title="AutoLaunch AI Agent")

allowed_origins = [origin.strip() for origin in settings.cors_origins if origin.strip()]
if not allowed_origins or allowed_origins == ["*"]:
    allowed_origins = [
        "https://autolaunch-ai-agent.vercel.app",
        "https://www.autolaunch-ai-agent.vercel.app",
    ]
else:
    allowed_origins.extend([
        "https://autolaunch-ai-agent.vercel.app",
        "https://www.autolaunch-ai-agent.vercel.app",
    ])

allowed_origins = list(dict.fromkeys(allowed_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PipelineRequest(BaseModel):
    project_path: str
    repo_name: str
    github_username: str
    make_private: bool = False
    include_content: bool = True


@app.get("/")
def root():
    return {"status": "AutoLaunch AI Agent is running"}


@app.post("/pipeline/run")
def run_pipeline(req: PipelineRequest):
    result = {"status": "started"}

    # Step 1: Analyze the project
    try:
        analysis = analyze(req.project_path)
        result["analysis"] = analysis
        result["status"] = "analyzed"
    except AnalyzerError as e:
        raise HTTPException(status_code=400, detail=f"Analysis failed: {e}")

    # Step 2: Push to GitHub (best effort only; deployment should still proceed)
    github_url = None
    client = github_client
    if client is None:
        try:
            client = GitHubClient()
        except GitHubClientError:
            client = None

    if client is not None:
        try:
            github_url = client.push_project(
                project_path=req.project_path,
                repo_name=req.repo_name,
                username=req.github_username,
                private=req.make_private,
            )
            result["github_url"] = github_url
        except GitHubClientError as e:
            result["github_url"] = None
            result["github_error"] = str(e)

    # Step 3: Deploy to Vercel
    live_url = None
    if vercel_client is not None:
        try:
            live_url = vercel_client.deploy(
                repo_name=req.repo_name,
                github_username=req.github_username,
            )
            result["live_url"] = live_url
            result["status"] = "deployed"
        except VercelClientError as e:
            result["live_url"] = None
            result["status"] = f"deploy_failed: {e}"
    else:
        result["status"] = "vercel_client_unavailable"

    # Step 4: Generate PRD + content
    try:
        summary = build_summary(
            project_name=req.repo_name,
            analysis=analysis["ai_summary"],
            github_url=github_url,
            live_url=live_url,
            include_content=req.include_content,
        )
        result["summary"] = summary.to_dict()
        result["status"] = "complete"
    except ProjectSummaryError as e:
        result["summary"] = None
        result["status"] = f"summary_failed: {e}"

    return result


@app.post("/analyze")
def analyze_only(project_path: str):
    try:
        return analyze(project_path)
    
    except AnalyzerError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/generate", response_model=GenerateResponse)
def generate_content(req: GenerateRequest):
    if engine is None:
        raise HTTPException(status_code=500, detail="AI engine unavailable")
    try:
        result = engine.ask(req.prompt)
        return GenerateResponse(result=result)
    except AIEngineError as e:
        raise HTTPException(status_code=400, detail=str(e))