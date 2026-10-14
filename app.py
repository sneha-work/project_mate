# app.py - FastAPI Application for ResearchMate AI
import os
import io
import json
import logging
import hmac
import hashlib
from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, Form, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import config
import database
from ollama_client import ollama_service, OllamaClient
from doc_converter import (
    parse_docx_file, parse_latex_file, parse_pdf_file, generate_latex_code,
    get_sample_academic_paper, STYLES_REGISTRY
)
from export_utils import (
    generate_paper_pdf, generate_paper_docx, generate_slides_pdf,
    generate_slides_pptx, generate_research_proposal_pdf, generate_bibliography_pdf
)
from slide_generator import generate_presentation
from literature_finder import search_verified_literature, get_topic_suggestions, VERIFIED_PAPERS_CATALOG
from idea_generator import generate_research_ideas
from conference_finder import find_topic_conferences, VERIFIED_CONFERENCES

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("researchmate.app")

# Initialize database
database.init_db()

# Create FastAPI app
app = FastAPI(
    title="ResearchMate AI",
    description="The Elite Academic Research & Publication Suite",
    version="2.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(config.BASE_DIR / "static")), name="static")

# Mount Jinja2 templates
templates = Jinja2Templates(directory=str(config.BASE_DIR / "templates"))


# Signed Cookie Session Helpers (Pure Python Standard Library)
COOKIE_NAME = "rm_session"

def sign_user_id(user_id: int) -> str:
    sig = hmac.new(config.SECRET_KEY.encode(), str(user_id).encode(), hashlib.sha256).hexdigest()
    return f"{user_id}:{sig}"

def verify_user_id(cookie_val: str) -> Optional[int]:
    if not cookie_val or ":" not in cookie_val:
        return None
    uid_str, sig = cookie_val.split(":", 1)
    expected = hmac.new(config.SECRET_KEY.encode(), uid_str.encode(), hashlib.sha256).hexdigest()
    if hmac.compare_digest(sig, expected):
        try:
            return int(uid_str)
        except ValueError:
            return None
    return None

def get_current_user(request: Request) -> Dict[str, Any]:
    cookie_val = request.cookies.get(COOKIE_NAME)
    user_id = verify_user_id(cookie_val) if cookie_val else 1
    user = database.get_user_by_id(user_id) if user_id else None
    if not user:
        user = database.get_or_create_user("guest", "guest@researchmate.ai", "Guest Scholar")
    return user


# ==========================================
# PAGE ROUTES (HTML VIEWS)
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def page_index(request: Request, user: dict = Depends(get_current_user)):
    """Sunny Homepage with introduction, purpose, sunny visuals, and quotes."""
    stats = database.get_user_stats(user["id"])
    return templates.TemplateResponse(request, "index.html", {
        "user": user,
        "stats": stats
    })

@app.get("/formatter", response_class=HTMLResponse)
async def page_formatter(request: Request, user: dict = Depends(get_current_user)):
    """Feature 1: 20-Style Academic Paper Formatter."""
    return templates.TemplateResponse(request, "formatter.html", {
        "user": user,
        "styles": STYLES_REGISTRY
    })

@app.get("/slides", response_class=HTMLResponse)
async def page_slides(request: Request, user: dict = Depends(get_current_user)):
    """Feature 2: Slide Deck Presentation Generator."""
    return templates.TemplateResponse(request, "slides.html", {
        "user": user
    })

@app.get("/literature", response_class=HTMLResponse)
async def page_literature(request: Request, user: dict = Depends(get_current_user)):
    """Feature 3: Verified Literature Discovery (20+ Papers)."""
    return templates.TemplateResponse(request, "literature.html", {
        "user": user
    })

@app.get("/ideas", response_class=HTMLResponse)
async def page_ideas(request: Request, user: dict = Depends(get_current_user)):
    """Feature 4: Innovative Research Idea Lab."""
    return templates.TemplateResponse(request, "ideas.html", {
        "user": user
    })

@app.get("/conferences", response_class=HTMLResponse)
async def page_conferences(request: Request, user: dict = Depends(get_current_user)):
    """Feature 5: Verified Conferences Finder."""
    return templates.TemplateResponse(request, "conferences.html", {
        "user": user
    })

@app.get("/history", response_class=HTMLResponse)
async def page_history(request: Request, user: dict = Depends(get_current_user)):
    """Scholar Library & History."""
    return templates.TemplateResponse(request, "history.html", {
        "user": user
    })

@app.get("/profile", response_class=HTMLResponse)
async def page_profile(request: Request, user: dict = Depends(get_current_user)):
    """Scholar Profile & Statistics."""
    stats = database.get_user_stats(user["id"])
    return templates.TemplateResponse(request, "profile.html", {
        "user": user,
        "stats": stats
    })

@app.get("/settings", response_class=HTMLResponse)
async def page_settings(request: Request, user: dict = Depends(get_current_user)):
    """Settings, Ollama Cloud API, Theme."""
    settings = database.get_user_settings(user["id"])
    return templates.TemplateResponse(request, "settings.html", {
        "user": user,
        "settings": settings
    })

@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ResearchMate AI", "version": "2.0.0"}


# ==========================================
# FEATURE 1: PAPER FORMATTER APIS
# ==========================================

@app.post("/api/formatter/parse")
async def api_formatter_parse(file: UploadFile = File(...), style_id: str = Form("ieee"), user: dict = Depends(get_current_user)):
    """Upload DOCX, LaTeX (.tex), or PDF and parse into structured academic components without adding extra content."""
    file_ext = Path(file.filename).suffix.lower()
    temp_path = config.UPLOADS_DIR / f"upload_{file.filename}"
    
    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)

    paper_data = None
    if file_ext == ".docx":
        paper_data = parse_docx_file(str(temp_path))
    elif file_ext in [".tex", ".latex"]:
        text_str = content.decode("utf-8", errors="ignore")
        paper_data = parse_latex_file(text_str)
    elif file_ext == ".pdf":
        paper_data = parse_pdf_file(str(temp_path))
    else:
        text_str = content.decode("utf-8", errors="ignore")
        paras = [p.strip() for p in text_str.split("\n\n") if p.strip()]
        title = paras[0][:100] if paras else file.filename.replace(file_ext, "").replace("_", " ").title()
        paper_data = {
            "title": title,
            "authors": [{"name": "Author", "affiliation": ""}],
            "abstract": paras[1][:600] if len(paras) > 1 else "",
            "keywords": [],
            "sections": [{"heading": "Main Content", "content": "\n\n".join(paras[2:]) if len(paras) > 2 else text_str}],
            "references": []
        }

    style_meta = STYLES_REGISTRY.get(style_id, STYLES_REGISTRY["ieee"])
    latex_code = generate_latex_code(paper_data, style_meta)

    database.add_history(
        user_id=user["id"],
        feature="formatter",
        title=f"Uploaded: {paper_data.get('title', 'Paper')[:50]}",
        summary=f"Parsed {file.filename} into structured manuscript."
    )

    return {
        "status": "success",
        "paper": paper_data,
        "latex_code": latex_code
    }

@app.get("/api/formatter/sample")
async def api_formatter_sample():
    """Return pre-built peer-reviewed sample paper (QR-Net Stanford/MIT)."""
    paper = get_sample_academic_paper()
    latex_code = generate_latex_code(paper, STYLES_REGISTRY["ieee"])
    return {"status": "success", "paper": paper, "latex_code": latex_code}

@app.post("/api/formatter/export")
async def api_formatter_export(request: Request, user: dict = Depends(get_current_user)):
    """Export paper to publication-grade PDF, DOCX, or LaTeX conforming to the selected style."""
    data = await request.json()
    style_id = data.get("style_id", "ieee")
    export_format = data.get("format", "pdf").lower()
    paper = data.get("paper", {})
    
    style_meta = STYLES_REGISTRY.get(style_id, STYLES_REGISTRY["ieee"])
    
    file_path = ""
    if export_format == "pdf":
        file_path = generate_paper_pdf(paper, style_meta)
    elif export_format == "docx":
        file_path = generate_paper_docx(paper, style_meta)
    elif export_format == "tex":
        import time
        filename = f"paper_{style_id}_{int(time.time())}.tex"
        file_path = str(config.EXPORTS_DIR / filename)
        tex_code = generate_latex_code(paper, style_meta)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(tex_code)

    database.add_history(
        user_id=user["id"],
        feature="formatter",
        title=f"{style_meta['name']}: {paper.get('title', 'Paper')[:50]}",
        summary=f"Generated {export_format.upper()} in {style_meta['name']} style.",
        file_path=file_path
    )

    return {
        "status": "success",
        "style": style_meta["name"],
        "download_url": f"/api/download?file={file_path}",
        "latex_code": generate_latex_code(paper, style_meta)
    }


# ==========================================
# FEATURE 2: SLIDE GENERATOR APIS
# ==========================================

@app.post("/api/slides/generate")
async def api_slides_generate(request: Request, user: dict = Depends(get_current_user)):
    """Generate structured slides deck (Descriptive or Analytical) with speaker notes and PDF."""
    data = await request.json()
    text = data.get("text", "")
    options = {
        "slide_count": data.get("slide_count", 8),
        "presentation_type": data.get("presentation_type", data.get("type", "Descriptive")),
        "theme": data.get("theme", "emerald")
    }

    deck = await generate_presentation(text, options=options)

    database.add_history(
        user_id=user["id"],
        feature="slides",
        title=f"Deck: {deck.get('title', 'Presentation')[:50]}",
        summary=f"{len(deck.get('slides', []))} slides generated ({deck.get('presentation_type', 'Descriptive')}).",
        meta=deck
    )

    return deck

@app.post("/api/slides/upload")
async def api_slides_upload(
    file: UploadFile = File(...),
    presentation_type: str = Form("Descriptive"),
    slide_count: int = Form(8),
    user: dict = Depends(get_current_user)
):
    """Upload PDF or DOCX research paper and summarize into a Descriptive or Analytical deck."""
    file_ext = Path(file.filename).suffix.lower()
    temp_path = config.UPLOADS_DIR / f"slide_upload_{file.filename}"
    
    content = await file.read()
    with open(temp_path, "wb") as f:
        f.write(content)

    extracted_text = ""
    title = file.filename.replace(file_ext, "").replace("_", " ").title()
    
    if file_ext == ".pdf":
        p_data = parse_pdf_file(str(temp_path))
        title = p_data.get("title") or title
        extracted_text = f"{p_data.get('title', '')}\n\nAbstract: {p_data.get('abstract', '')}\n\n"
        for s in p_data.get("sections", []):
            extracted_text += f"{s.get('heading', '')}\n{s.get('content', '')}\n\n"
    elif file_ext == ".docx":
        p_data = parse_docx_file(str(temp_path))
        title = p_data.get("title") or title
        extracted_text = f"{p_data.get('title', '')}\n\nAbstract: {p_data.get('abstract', '')}\n\n"
        for s in p_data.get("sections", []):
            extracted_text += f"{s.get('heading', '')}\n{s.get('content', '')}\n\n"
    elif file_ext in [".tex", ".latex"]:
        text_str = content.decode("utf-8", errors="ignore")
        p_data = parse_latex_file(text_str)
        title = p_data.get("title") or title
        extracted_text = f"{p_data.get('title', '')}\n\nAbstract: {p_data.get('abstract', '')}\n\n"
        for s in p_data.get("sections", []):
            extracted_text += f"{s.get('heading', '')}\n{s.get('content', '')}\n\n"
    else:
        extracted_text = content.decode("utf-8", errors="ignore")

    options = {
        "slide_count": slide_count,
        "presentation_type": presentation_type,
        "theme": "emerald"
    }
    deck = await generate_presentation(extracted_text, paper_meta=p_data, options=options)

    database.add_history(
        user_id=user["id"],
        feature="slides",
        title=f"Deck: {title[:50]}",
        summary=f"Summarized {file.filename} into {len(deck.get('slides', []))} slides ({deck.get('presentation_type', 'Descriptive')}).",
        meta=deck
    )

    return deck


# ==========================================
# FEATURE 3: LITERATURE DISCOVERY APIS
# ==========================================

@app.get("/api/literature/search")
async def api_literature_search(q: str = Query("machine learning"), user: dict = Depends(get_current_user)):
    """Search and retrieve at least 20 verified academic research papers."""
    results = await search_verified_literature(q)

    database.add_history(
        user_id=user["id"],
        feature="literature",
        title=f"Literature Search: {q.title()}",
        summary=f"Discovered {results['count']} verified papers with DOI and direct PDF links."
    )

    return results

@app.get("/api/literature/suggestions")
async def api_literature_suggestions(q: str = Query("")):
    """Return autocomplete suggestions for research topics."""
    return {"suggestions": get_topic_suggestions(q)}


# ==========================================
# FEATURE 4: INNOVATIVE IDEA LAB APIS
# ==========================================

@app.post("/api/ideas/generate")
async def api_ideas_generate(request: Request, user: dict = Depends(get_current_user)):
    """Generate breakthrough research proposals and hypotheses."""
    data = await request.json()
    topic = data.get("topic", "Foundational Deep Learning")
    domain = data.get("domain", "Computer Science & AI")
    focus = data.get("focus", "Breakthrough Methodology")

    res = await generate_research_ideas(topic, domain, focus)

    top_title = res["ideas"][0]["title"] if res.get("ideas") else "Research Proposal"
    database.add_history(
        user_id=user["id"],
        feature="ideas",
        title=f"Proposal: {top_title[:50]}",
        summary=f"Synthesized 3 novel hypotheses in {domain}."
    )

    return res


# ==========================================
# FEATURE 5: VERIFIED CONFERENCES APIS
# ==========================================

@app.get("/api/conferences/search")
async def api_conferences_search(
    q: str = Query(""),
    rank: str = Query("ALL"),
    field: str = Query("ALL")
):
    """Search verified conferences with submission deadlines and countdowns."""
    confs = find_topic_conferences(q, filter_rank=rank, field_category=field)
    return {"conferences": confs, "total": len(confs)}

@app.get("/api/conferences/export_pdf")
async def api_conferences_export_pdf(user: dict = Depends(get_current_user)):
    """Export verified conference calendar as a formatted PDF."""
    from export_utils import generate_bibliography_pdf
    items = []
    for c in VERIFIED_CONFERENCES:
        items.append({
            "title": f"{c['acronym']} — {c['name']} (CORE {c['core_rank']})",
            "authors": f"Venue: {c['venue']}",
            "year": 2026,
            "venue": f"Proceedings: {c['proceedings']} | Acceptance: ~{c['acceptance_rate']}",
            "abstract": f"Important Dates: Submission Deadline: {c['submission_deadline']} | Abstract: {c['abstract_deadline']} | Notification: {c['notification_date']} | Conference: {c['conference_dates']}",
            "url": c["url"],
            "doi": f"CFP: {c['cfp_url']}"
        })
    pdf_path = generate_bibliography_pdf(items, "Premier Verified Academic Conferences 2026")

    database.add_history(
        user_id=user["id"],
        feature="conferences",
        title="Conference Deadlines Guide 2026",
        summary="Exported verified CORE A*/A academic conference calendar.",
        file_path=pdf_path
    )

    return {"status": "success", "download_url": f"/api/download?file={pdf_path}"}


# ==========================================
# AUTHENTICATION & PROFILE APIS
# ==========================================

@app.get("/api/auth/guest")
async def api_auth_guest(response: Response):
    """Instant 1-Click Guest Access."""
    guest_user = database.get_or_create_user("guest", "guest@researchmate.ai", "Guest Scholar")
    res = RedirectResponse(url="/", status_code=303)
    res.set_cookie(COOKIE_NAME, sign_user_id(guest_user["id"]), httponly=True, max_age=86400 * 30)
    return res

@app.get("/api/auth/google")
async def api_auth_google(response: Response):
    """Simulated/Configurable Google Sign-In: instantly creates authenticated Scholar account."""
    scholar_user = database.get_or_create_user(
        username="scholar_google",
        email="scholar.dr@university.edu",
        full_name="Dr. Julian Vance",
        avatar_url="/static/images/avatar_default.svg",
        google_id="google_sub_10928374"
    )
    res = RedirectResponse(url="/profile", status_code=303)
    res.set_cookie(COOKIE_NAME, sign_user_id(scholar_user["id"]), httponly=True, max_age=86400 * 30)
    return res

@app.post("/api/profile/update")
async def api_profile_update(request: Request, user: dict = Depends(get_current_user)):
    """Update scholar profile details."""
    data = await request.json()
    full_name = data.get("full_name", user["full_name"])
    email = data.get("email", user["email"])
    database.update_user_profile(user["id"], full_name, email)
    return {"status": "success", "message": "Profile updated"}


# ==========================================
# LIBRARY & HISTORY APIS
# ==========================================

@app.get("/api/history")
async def api_get_history(type: str = Query("all"), user: dict = Depends(get_current_user)):
    """Retrieve user history or saved items."""
    if type == "papers":
        items = database.get_saved_papers(user["id"])
        formatted = [{"id": p["id"], "feature": "literature", "title": p["title"], "summary": f"By {p['authors']} ({p['year']})", "created_at": p.get("created_at"), "file_path": ""} for p in items]
        return {"items": formatted}
    elif type == "ideas":
        items = database.get_saved_ideas(user["id"])
        formatted = [{"id": i["id"], "feature": "ideas", "title": i["title"], "summary": f"Domain: {i['domain']}", "created_at": i.get("created_at"), "file_path": ""} for i in items]
        return {"items": formatted}
    elif type == "conferences":
        items = database.get_saved_conferences(user["id"])
        formatted = [{"id": c["id"], "feature": "conferences", "title": f"{c['acronym']}: {c['name']}", "summary": f"Venue: {c['venue']} | Deadline: {c['deadline']}", "created_at": c.get("created_at"), "file_path": ""} for c in items]
        return {"items": formatted}
    else:
        history = database.get_user_history(user["id"], feature=type)
        return {"items": history}

@app.delete("/api/history/{item_id}")
async def api_delete_history(item_id: int, user: dict = Depends(get_current_user)):
    """Delete a single history entry."""
    database.delete_history_item(user["id"], item_id)
    return {"status": "success"}

@app.post("/api/history/clear")
async def api_clear_history(type: str = Query("all"), user: dict = Depends(get_current_user)):
    """Clear history entries."""
    database.clear_user_history(user["id"], feature=type)
    return {"status": "success"}

@app.post("/api/library/save_paper")
async def api_save_paper(request: Request, user: dict = Depends(get_current_user)):
    """Save paper to user Library."""
    paper = await request.json()
    paper_id = database.save_paper(user["id"], paper)
    return {"status": "success", "id": paper_id}

@app.post("/api/library/save_idea")
async def api_save_idea(request: Request, user: dict = Depends(get_current_user)):
    """Save research proposal to user Library."""
    idea = await request.json()
    idea_id = database.save_idea(user["id"], idea)
    return {"status": "success", "id": idea_id}

@app.post("/api/library/save_conf")
async def api_save_conf(request: Request, user: dict = Depends(get_current_user)):
    """Save conference to user Calendar."""
    conf = await request.json()
    conf_id = database.save_conference(user["id"], conf)
    return {"status": "success", "id": conf_id}


# ==========================================
# SETTINGS APIS
# ==========================================

@app.post("/api/settings/save")
async def api_settings_save(request: Request, user: dict = Depends(get_current_user)):
    """Update user settings and API configurations."""
    data = await request.json()
    database.update_user_settings(
        user_id=user["id"],
        theme=data.get("theme", "light"),
        ollama_host=data.get("ollama_host", ""),
        ollama_model=data.get("ollama_model", ""),
        ollama_api_key=data.get("ollama_api_key", ""),
        default_style=data.get("default_style", "ieee"),
        google_client_id=data.get("google_client_id", "")
    )
    return {"status": "success"}

@app.post("/api/settings/test_ollama")
async def api_settings_test_ollama(request: Request):
    """Test connection to Ollama Cloud API."""
    data = await request.json()
    client = OllamaClient(api_key=data.get("api_key", ""), host=data.get("host", ""))
    result = await client.test_connection()
    return result


# ==========================================
# SECURE DOWNLOAD HANDLER
# ==========================================

@app.get("/api/download")
async def api_download(file: str = Query(...)):
    """Securely serve generated PDF, DOCX, PPTX, or TeX files."""
    file_path = Path(file).resolve()
    exports_dir = config.EXPORTS_DIR.resolve()
    uploads_dir = config.UPLOADS_DIR.resolve()
    
    if not (str(file_path).startswith(str(exports_dir)) or str(file_path).startswith(str(uploads_dir))):
        raise HTTPException(status_code=403, detail="Access denied: File outside export path.")
        
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested file was not found.")
        
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream"
    )

@app.get("/api/download/zip")
async def download_project_zip():
    """Download the complete ResearchMate AI codebase zip package."""
    zip_path = Path("ResearchMate_AI.zip").resolve()
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Zip file not found.")
    return FileResponse(
        path=str(zip_path),
        filename="ResearchMate_AI.zip",
        media_type="application/zip"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=config.HOST, port=config.PORT, reload=False)
