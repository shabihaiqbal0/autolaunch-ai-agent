import os
import sys
import zipfile
import tempfile
import shutil
import time
from datetime import datetime
import streamlit as st
import pandas as pd

# Path setup to ensure imports work correctly
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import backend modules
from backend.github.analyzer import analyze, AnalyzerError
import backend.github.github_client as github_client_mod
import backend.deployment.vercel_client as vercel_client_mod
import backend.ai.ai_engine as ai_engine
import backend.ai.content_writer as content_writer_mod
from backend.ai.project_summary import build_summary, ProjectSummaryError
from backend.screenshot.capture import capture_screenshots

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DevLaunch AI — Desktop Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dynamic Reinitialization Helper ───────────────────────────────────────────
def reinit_clients(groq_key: str, github_token: str, vercel_token: str = None):
    """Binds UI key inputs directly to the backend client singletons."""
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
        try:
            ai_engine.engine = ai_engine.AIEngine(api_key=groq_key)
            content_writer_mod.writer = content_writer_mod.ContentWriter()
            import backend.screenshot.formatter as formatter_mod
            formatter_mod.formatter = formatter_mod.Formatter()
        except Exception as e:
            st.sidebar.error(f"AI Engine Error: {e}")
            
    if github_token:
        os.environ["GITHUB_TOKEN"] = github_token
        try:
            github_client_mod.github_client = github_client_mod.GitHubClient(token=github_token)
        except Exception as e:
            st.sidebar.error(f"GitHub Client Error: {e}")
            
    if vercel_token:
        os.environ["VERCEL_TOKEN"] = vercel_token
        try:
            vercel_client_mod.vercel_client = vercel_client_mod.VercelClient(token=vercel_token)
        except Exception:
            pass

# ── Premium Theme CSS ─────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Dark sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090d16 0%, #111827 100%) !important;
        border-right: 1px solid #1f2937;
    }
    section[data-testid="stSidebar"] * {
        color: #e5e7eb !important;
    }

    /* Custom main app body background */
    .stApp {
        background-color: #0b0f19;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.6rem 1.8rem;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #818cf8 0%, #6366f1 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
    }

    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #111827 0%, #0f172a 100%);
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 1.5rem;
        color: #f3f4f6;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #f3f4f6 !important;
    }
    
    /* Highlighted link tabs */
    a.link-btn {
        display: inline-block;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white !important;
        text-decoration: none;
        padding: 0.5rem 1.2rem;
        border-radius: 6px;
        font-weight: 600;
        margin-right: 10px;
        transition: all 0.2s;
    }
    a.link-btn:hover {
        background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar Configurations ────────────────────────────────────────────────────
st.sidebar.markdown(
    """
    <div style="text-align:center;padding:1rem 0;">
        <div style="font-size:2.5rem">🚀</div>
        <div style="font-weight:700;font-size:1.3rem;color:#f3f4f6;letter-spacing:1px;">
            DevLaunch AI
        </div>
        <div style="font-size:0.8rem;color:#9ca3af;margin-top:0.2rem;">Workspace Desktop Agent</div>
    </div>
    <hr style="border-color:#1f2937;margin:0.5rem 0 1.5rem;">
    """,
    unsafe_allow_html=True,
)

# Load env defaults
env_groq = os.getenv("GROQ_API_KEY", "")
env_github = os.getenv("GITHUB_TOKEN", "")
env_vercel = os.getenv("VERCEL_TOKEN", "")

st.sidebar.subheader("🔑 API Configurations")
groq_key = st.sidebar.text_input("Groq API Key", value=env_groq, type="password", help="Used to analyze project and generate PRD/Marketing copy")
github_token = st.sidebar.text_input("GitHub Token", value=env_github, type="password", help="Used to create repository and push files")
github_username = st.sidebar.text_input("GitHub Username", value=os.getenv("GITHUB_USERNAME", ""), placeholder="e.g. shabihaiqbal0")
vercel_token = st.sidebar.text_input("Vercel Token (Optional)", value=env_vercel, type="password", help="Used to trigger deployments")

# Apply dynamic reinitialization
reinit_clients(groq_key, github_token, vercel_token)

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #1e1b4b 0%, #0b0f19 50%, #030712 100%);
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    ">
        <h1 style="font-size:2.8rem; margin:0; font-weight: 700; background: linear-gradient(to right, #a5b4fc, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🚀 DevLaunch AI Workspace Agent
        </h1>
        <p style="color:#9ca3af; font-size:1.15rem; margin-top:0.6rem; max-width:800px;">
            A complete automation agent: scans your project, pushes to GitHub, deploys a live preview, and generates high-fidelity Product Requirements (PRD), README, and cross-platform marketing content.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Main Flow Form ────────────────────────────────────────────────────────────
col_left, col_right = st.columns([2, 3])

with col_left:
    st.subheader("📁 Project Input")
    project_source = st.radio("Select Project Source", ["Upload ZIP File", "Local Path"], horizontal=True)
    
    local_path = ""
    uploaded_file = None
    
    if project_source == "Local Path":
        local_path = st.text_input("Local Folder Path", placeholder="e.g. C:/Users/DELL/Desktop/MyProject")
    else:
        uploaded_file = st.file_uploader("Upload Project ZIP File", type="zip")
        
    st.subheader("⚙️ Deployment Settings")
    repo_name = st.text_input("Repository Name", placeholder="e.g. my-cool-project")
    make_private = st.checkbox("Make GitHub Repository Private", value=False)
    include_content = st.checkbox("Generate Marketing & Publishing Content", value=True)
    capture_screenshot = st.checkbox("Capture App Screenshots (Playwright)", value=False)
    
    run_pipeline_btn = st.button("🚀 Launch Automation Pipeline", use_container_width=True)

with col_right:
    st.subheader("📋 Execution & Live Console")
    console_placeholder = st.empty()
    console_placeholder.info("Ready. Set configuration and click 'Launch Automation Pipeline' to begin.")
    
    if run_pipeline_btn:
        # Validate keys
        if not groq_key:
            st.error("❌ Groq API Key is required. Please set it in the sidebar.")
        elif not github_token or not github_username:
            st.error("❌ GitHub Token and Username are required to initialize the repository.")
        elif not repo_name:
            st.error("❌ Please provide a Repository Name.")
        elif project_source == "Local Path" and not local_path:
            st.error("❌ Please provide a Local Folder Path.")
        elif project_source == "Upload ZIP File" and uploaded_file is None:
            st.error("❌ Please upload a project ZIP file.")
        else:
            # We are ready to run
            console_log = []
            
            def add_log(msg: str, status="info"):
                console_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
                log_text = "\n".join(console_log)
                if status == "info":
                    console_placeholder.code(log_text)
                elif status == "success":
                    console_placeholder.code(log_text + "\n\nPipeline execution finished successfully!")
            
            add_log("Starting Automation Pipeline...")
            
            # Create a workspace directory to work in
            work_dir = ""
            temp_dir_obj = None
            
            if project_source == "Upload ZIP File" and uploaded_file is not None:
                add_log("Extracting uploaded project archive...")
                temp_dir_obj = tempfile.TemporaryDirectory()
                extract_path = os.path.join(temp_dir_obj.name, "extracted")
                os.makedirs(extract_path, exist_ok=True)
                
                # Write zip to temp file
                zip_path = os.path.join(temp_dir_obj.name, "project.zip")
                with open(zip_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Extract
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                
                # Locate true root in case zip contains a nested folder
                work_dir = extract_path
                contents = os.listdir(extract_path)
                if len(contents) == 1 and os.path.isdir(os.path.join(extract_path, contents[0])):
                    work_dir = os.path.join(extract_path, contents[0])
                    
                add_log(f"Project extracted to temporary workspace: {work_dir}")
            else:
                work_dir = os.path.abspath(local_path)
                if not os.path.isdir(work_dir):
                    st.error(f"❌ Local Path is not a valid directory: {work_dir}")
                    st.stop()
                add_log(f"Using local folder path: {work_dir}")
                
            # Pipeline logic
            try:
                # Step 1: Scan & Analyze
                add_log("Step 1: Scanning project file tree and parsing key configurations...")
                analysis = analyze(work_dir)
                add_log("Successfully completed scanning. AI Model analysis in progress...")
                add_log(f"Detected project type: {analysis['ai_summary'].get('project_type', 'Unknown')}")
                add_log(f"Primary Tech Stack: {', '.join(analysis['ai_summary'].get('tech_stack', []))}")
                
                # Step 2: Push to GitHub
                add_log("Step 2: Authenticating with GitHub and preparing repository...")
                github_url = None
                try:
                    client = github_client_mod.github_client
                    if client is None:
                        client = github_client_mod.GitHubClient(token=github_token)
                    
                    add_log(f"Creating GitHub repository '{repo_name}'...")
                    github_url = client.push_project(
                        project_path=work_dir,
                        repo_name=repo_name,
                        username=github_username,
                        private=make_private,
                    )
                    add_log(f"Code successfully committed and pushed! Repository live at: {github_url}")
                except Exception as e:
                    add_log(f"⚠️ GitHub Push skipped/failed: {e}")
                    st.warning(f"Could not push code to GitHub: {e}")
                
                # Step 3: Deploy to Vercel (if token provided)
                live_url = None
                if vercel_token and vercel_client_mod.vercel_client is not None:
                    add_log("Step 3: Triggering project deployment on Vercel...")
                    try:
                        live_url = vercel_client_mod.vercel_client.deploy(
                            repo_name=repo_name,
                            github_username=github_username,
                        )
                        add_log(f"Vercel Deployment initiated. Live preview url: {live_url}")
                    except Exception as e:
                        add_log(f"⚠️ Vercel deployment skipped/failed: {e}")
                else:
                    add_log("Step 3: Vercel deployment skipped (Vercel token not configured).")
                
                # Step 4: Generate PRD + Content
                add_log("Step 4: Generating high-fidelity PRD, README and marketing copy...")
                summary = build_summary(
                    project_name=repo_name,
                    analysis=analysis["ai_summary"],
                    github_url=github_url,
                    live_url=live_url,
                    include_content=include_content,
                )
                add_log("PRD and readme generation finished.")
                
                # Generate platform-specific social drafts (LinkedIn, Fiverr, Upwork)
                social_drafts = {}
                if include_content:
                    add_log("Generating social copies for LinkedIn, Fiverr, and Upwork...")
                    try:
                        import backend.screenshot.formatter as formatter_mod
                        if formatter_mod.formatter is not None:
                            social_drafts = formatter_mod.formatter.format_all(analysis["ai_summary"], live_url=live_url)
                    except Exception as e:
                        add_log(f"⚠️ Social copies formatting skipped/failed: {e}")
                
                # Step 5: Screen captures (if requested)
                screenshots = []
                if capture_screenshot and live_url:
                    add_log("Step 5: Initiating Playwright screenshot captures...")
                    screenshot_dir = os.path.join(work_dir, "screenshots")
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshots = capture_screenshots(live_url, screenshot_dir)
                    add_log(f"Screenshots captured: {len(screenshots)} device breakpoint layout(s).")
                
                # Done
                add_log("Pipeline completed!", status="success")
                st.session_state["pipeline_results"] = {
                    "summary": summary.to_dict(),
                    "github_url": github_url,
                    "live_url": live_url,
                    "screenshots": screenshots,
                    "project_name": repo_name,
                    "social_drafts": social_drafts,
                }
                st.success("🎉 Pipeline complete! Results are available below.")
                st.balloons()
                
            except Exception as e:
                add_log(f"❌ Execution failed: {e}")
                st.error(f"Pipeline error: {e}")
            finally:
                # Cleanup zip extract path if needed
                if temp_dir_obj is not None:
                    try:
                        temp_dir_obj.cleanup()
                        add_log("Cleaned up temporary workspace.")
                    except Exception:
                        pass

# ── Results Sections ──────────────────────────────────────────────────────────
if "pipeline_results" in st.session_state:
    st.markdown("---")
    res = st.session_state["pipeline_results"]
    summary = res["summary"]
    
    st.subheader(f"📊 Results for {res['project_name']}")
    
    # URL Actions
    col_urls = st.columns(3)
    with col_urls[0]:
        if res["github_url"]:
            st.markdown(f'<a href="{res["github_url"]}" target="_blank" class="link-btn">📁 Open GitHub Repository</a>', unsafe_allow_html=True)
        else:
            st.info("GitHub Repository was not created.")
    with col_urls[1]:
        if res["live_url"]:
            st.markdown(f'<a href="{res["live_url"]}" target="_blank" class="link-btn" style="background:linear-gradient(135deg, #6366f1, #4f46e5)">🌐 View Live Deployment</a>', unsafe_allow_html=True)
        else:
            st.info("Vercel Live Preview is not deployed.")
            
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Product Requirements (PRD)",
        "📖 README.md",
        "📢 Marketing & Social Content",
        "📂 Tech Stack Analysis",
        "📸 Screenshots"
    ])
    
    with tab1:
        st.subheader("Product Requirements Document (PRD)")
        if summary.get("prd"):
            st.download_button("Download PRD.md", summary["prd"], file_name="PRD.md", mime="text/markdown")
            st.markdown(summary["prd"])
        else:
            st.info("PRD was not generated.")
            
    with tab2:
        st.subheader("README.md File Content")
        if summary.get("readme"):
            st.download_button("Download README.md", summary["readme"], file_name="README.md", mime="text/markdown")
            st.code(summary["readme"], language="markdown")
        else:
            st.info("README content not generated.")
            
    with tab3:
        st.subheader("Social Drafts & Gig Descriptions")
        social_drafts = res.get("social_drafts", {})
        
        col_soc_l, col_soc_r = st.columns(2)
        with col_soc_l:
            st.markdown("#### 👥 LinkedIn Post")
            linkedin_post = social_drafts.get("linkedin") or "N/A"
            st.text_area("LinkedIn Draft", linkedin_post, height=180)
            
            st.markdown("#### 💳 Fiverr Gig Portfolio Blurb")
            fiverr_gig = social_drafts.get("fiverr") or "N/A"
            st.text_area("Fiverr Draft", fiverr_gig, height=120)
            
        with col_soc_r:
            st.markdown("#### 💼 Upwork Portfolio Description")
            upwork_port = social_drafts.get("upwork") or "N/A"
            st.text_area("Upwork Draft", upwork_port, height=180)
            
            st.markdown("#### ✍️ Dev Blog Post")
            blog_post = summary.get("blog_post") or "N/A"
            st.text_area("Blog Post Draft", blog_post, height=180)
            
    with tab4:
        st.subheader("Project Technical Profile")
        ai_sum = summary.get("analysis", {})
        if ai_sum:
            col_tech1, col_tech2 = st.columns(2)
            with col_tech1:
                st.write(f"**Project Type**: {ai_sum.get('project_type', 'N/A')}")
                st.write(f"**Main Entry Point**: `{ai_sum.get('entry_point', 'N/A')}`")
                st.write(f"**Run Command**: `{ai_sum.get('run_command', 'N/A')}`")
                st.write(f"**Deploy Target**: `{ai_sum.get('deploy_target', 'N/A')}`")
            with col_tech2:
                st.write("**Tech Stack:**")
                for tech in ai_sum.get("tech_stack", []):
                    st.markdown(f"- {tech}")
                
            st.write("---")
            st.markdown("#### Purpose")
            st.write(ai_sum.get("purpose", "N/A"))
            
            st.markdown("#### Missing Pieces")
            missing = ai_sum.get("missing_pieces", [])
            if missing:
                for item in missing:
                    st.markdown(f"⚠️ {item}")
            else:
                st.success("No missing configuration elements detected! Ready to compile and ship.")
        else:
            st.info("Tech stack profile is not available.")
            
    with tab5:
        st.subheader("App Layout Breakpoint Captures")
        if res.get("screenshots"):
            for s_path in res["screenshots"]:
                name = os.path.basename(s_path).replace("screenshot_", "").replace(".png", "").capitalize()
                st.image(s_path, caption=f"{name} Breakpoint Preview", use_column_width=True)
        else:
            st.info("No screenshots were captured. Ensure screenshot capture is checked and Vercel live URL is ready.")
