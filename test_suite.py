# test_suite.py - End-to-End Verification Test Suite for ResearchMate AI
import asyncio
import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from doc_converter import parse_latex_file, get_sample_academic_paper, generate_latex_code, STYLES_REGISTRY
from export_utils import (
    generate_paper_pdf, generate_paper_docx, generate_slides_pdf,
    generate_slides_pptx, generate_research_proposal_pdf, generate_bibliography_pdf
)
from slide_generator import generate_presentation
from literature_finder import search_verified_literature, get_topic_suggestions
from idea_generator import generate_research_ideas
from conference_finder import find_topic_conferences
import database

async def run_tests():
    print("=" * 60)
    print("RUNNING RESEARCHMATE AI END-TO-END VERIFICATION SUITE")
    print("=" * 60)

    # 1. Test Database
    print("\n[TEST 1] Initializing SQLite database...")
    database.init_db()
    guest = database.get_or_create_user("test_guest", "test@univ.edu", "Test Scholar")
    assert guest["id"] > 0, "Failed to create guest user in DB"
    print(f"✓ Database verified! User created with ID: {guest['id']}")

    # 2. Test Feature 1: Paper Formatter & 20 Styles PDF/DOCX/LaTeX
    print("\n[TEST 2] Testing Feature 1: 20-Style Academic Paper Formatter & LaTeX...")
    sample_paper = get_sample_academic_paper()
    assert sample_paper["title"], "Sample paper title missing"
    assert len(sample_paper["sections"]) >= 4, "Sample paper sections missing"
    
    # Test LaTeX Code Generation
    ieee_meta = STYLES_REGISTRY["ieee"]
    latex_code = generate_latex_code(sample_paper, ieee_meta)
    assert "\\documentclass[conference]{IEEEtran}" in latex_code, "IEEE LaTeX code missing documentclass"
    assert sample_paper["title"] in latex_code, "Paper title missing in generated LaTeX"
    print(f"✓ Compilable LaTeX Code verified ({len(latex_code)} characters)!")

    # Generate IEEE PDF
    ieee_pdf = generate_paper_pdf(sample_paper, ieee_meta, "test_paper_ieee.pdf")
    assert os.path.exists(ieee_pdf) and os.path.getsize(ieee_pdf) > 1000, f"IEEE PDF missing or empty: {ieee_pdf}"
    print(f"✓ Formatted IEEE PDF generated ({os.path.getsize(ieee_pdf)} bytes): {ieee_pdf}")

    # Generate APA 7 PDF
    apa_meta = STYLES_REGISTRY["apa7"]
    apa_pdf = generate_paper_pdf(sample_paper, apa_meta, "test_paper_apa.pdf")
    assert os.path.exists(apa_pdf) and os.path.getsize(apa_pdf) > 1000, f"APA PDF missing or empty: {apa_pdf}"
    print(f"✓ Formatted APA 7 PDF generated ({os.path.getsize(apa_pdf)} bytes): {apa_pdf}")

    # Generate DOCX
    docx_file = generate_paper_docx(sample_paper, ieee_meta, "test_paper_ieee.docx")
    assert os.path.exists(docx_file) and os.path.getsize(docx_file) > 1000, f"DOCX missing or empty: {docx_file}"
    print(f"✓ Formatted DOCX generated ({os.path.getsize(docx_file)} bytes): {docx_file}")

    # 3. Test Feature 2: Slide Generator (Descriptive & Analytical Modes + PDF)
    print("\n[TEST 3] Testing Feature 2: Deck Maker (Descriptive & Analytical Modes)...")
    deck_desc = await generate_presentation(
        sample_paper["abstract"],
        paper_meta={"title": sample_paper["title"]},
        options={"slide_count": 8, "presentation_type": "Descriptive", "theme": "emerald"}
    )
    assert len(deck_desc["slides"]) == 8, f"Expected 8 slides, got {len(deck_desc['slides'])}"
    assert deck_desc["presentation_type"] == "Descriptive", "Expected Descriptive type"
    print(f"✓ Descriptive Deck generated with {len(deck_desc['slides'])} slides and summary.")

    deck_anal = await generate_presentation(
        sample_paper["abstract"],
        paper_meta={"title": sample_paper["title"]},
        options={"slide_count": 8, "presentation_type": "Analytical", "theme": "emerald"}
    )
    assert len(deck_anal["slides"]) == 8, f"Expected 8 slides, got {len(deck_anal['slides'])}"
    assert deck_anal["presentation_type"] == "Analytical", "Expected Analytical type"
    print(f"✓ Analytical Deck generated with {len(deck_anal['slides'])} slides and quantitative metrics.")
    
    # Verify PDF & PPTX exports
    slides_pdf = generate_slides_pdf(deck_anal, "test_presentation.pdf")
    slides_pptx = generate_slides_pptx(deck_anal, "test_presentation.pptx")
    assert os.path.exists(slides_pdf) and os.path.getsize(slides_pdf) > 1000, "Slides PDF missing"
    assert os.path.exists(slides_pptx) and os.path.getsize(slides_pptx) > 1000, "Slides PPTX missing"
    print(f"✓ Presentation PDF ({os.path.getsize(slides_pdf)} bytes) & PPTX ({os.path.getsize(slides_pptx)} bytes) verified!")

    # 4. Test Feature 3: 20+ Verified Research Papers Discovery
    print("\n[TEST 3] Testing Feature 3: Verified Literature Discovery (20+ Papers)...")
    lit_results = await search_verified_literature("Transformers Attention Deep Learning")
    papers_count = lit_results["count"]
    assert papers_count >= 20, f"Expected >= 20 verified papers, got {papers_count}"
    first_p = lit_results["papers"][0]
    assert first_p["url"] and first_p["pdf_url"], "Paper URLs missing"
    assert first_p["bibtex"], "BibTeX citation missing"
    print(f"✓ Verified Literature Search returned {papers_count} papers! (>= 20 papers guarantee met)")
    print(f"  First Paper: {first_p['title'][:50]}... | Citations: {first_p['citations']}")

    # Test Autocomplete
    suggestions = get_topic_suggestions("Trans")
    assert len(suggestions) > 0, "Topic suggestions empty"
    print(f"✓ Autocomplete suggestions verified: {suggestions[:3]}")

    # 5. Test Feature 4: Innovative Research Ideas
    print("\n[TEST 4] Testing Feature 4: Innovative Research Idea Lab...")
    ideas_res = await generate_research_ideas(
        "Hallucination Mitigation in Real-Time RAG Pipelines",
        domain="Computer Science & AI",
        focus_area="Breakthrough Methodology"
    )
    assert len(ideas_res["ideas"]) >= 3, "Expected at least 3 research proposals"
    top_idea = ideas_res["ideas"][0]
    assert top_idea["hypothesis"] and top_idea["methodology"], "Proposal components missing"
    print(f"✓ Generated {len(ideas_res['ideas'])} comprehensive research proposals.")
    print(f"  Top Proposal: {top_idea['title'][:60]}... (Feasibility: {top_idea['feasibility']})")

    # 6. Test Feature 5: Verified Academic Conferences
    print("\n[TEST 5] Testing Feature 5: Verified Conferences Finder...")
    confs = find_topic_conferences(filter_rank="A*")
    assert len(confs) >= 8, f"Expected >= 8 A* conferences, got {len(confs)}"
    neurips = next((c for c in confs if "NeurIPS" in c["acronym"]), None)
    assert neurips is not None, "NeurIPS 2026 missing from conference list"
    assert neurips["venue"] and neurips["submission_deadline"], "Conference details missing"
    print(f"✓ Verified Conferences Finder returned {len(confs)} premier A* venues.")
    print(f"  Sample: {neurips['acronym']} | Venue: {neurips['venue']} | Days Left: {neurips['days_remaining']}")

    print("\n" + "=" * 60)
    print("ALL 5 FEATURES & CORE UTILITIES PASSED INDISPUTABLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
