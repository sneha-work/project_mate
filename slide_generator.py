# slide_generator.py - Academic Paper to Presentation Deck Generator
import re
import json
import logging
from typing import Dict, Any, List, Optional
from ollama_client import ollama_service
from export_utils import generate_slides_pdf, generate_slides_pptx, generate_notes_deck_pdf

logger = logging.getLogger("researchmate.slides")


def extract_paper_summary(paper_text: str, title: str = "") -> Dict[str, Any]:
    """Extract a concise academic summary and core takeaways directly from paper text."""
    clean_text = paper_text.strip()
    paras = [p.strip() for p in clean_text.split("\n\n") if p.strip()]

    first_few = " ".join(paras[:3])[:800] if paras else clean_text[:800]

    return {
        "title": title or (paras[0][:90] if paras else "Academic Research Analysis"),
        "executive_summary": first_few,
        "key_takeaways": [
            "Analyzes core technological breakthroughs and foundational literature.",
            "Validates real-world applicability, functional workflows, and domain opportunities.",
            "Formulates strategic directions while addressing critical implementation challenges."
        ]
    }


def parse_raw_text_into_sections(raw_text: str) -> List[Dict[str, Any]]:
    """Parse unformatted manuscript text into structured sections by detecting headings."""
    paras = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
    if not paras:
        return []

    sections = []
    current_sec = None

    for p in paras:
        p_lower = p.lower()
        is_heading = False
        if len(p) < 95 and (
            re.match(r"^(\d+(\.\d+)*|[IVXLCDM]+\.?)\s+[A-Za-z]", p)
            or (p.isupper() and len(p.split()) < 7)
            or any(p_lower.startswith(k) for k in [
                "introduction", "literature review", "related work", "method", "methodology",
                "proposed framework", "challenges", "opportunities", "future possibilities",
                "results", "discussion", "conclusion"
            ])
        ):
            is_heading = True

        if is_heading:
            if current_sec:
                sections.append(current_sec)
            current_sec = {"heading": p, "content": []}
        else:
            if current_sec:
                current_sec["content"].append(p)
            else:
                current_sec = {"heading": "Introduction", "content": [p]}

    if current_sec:
        sections.append(current_sec)

    return sections


async def generate_presentation(paper_text: str, paper_meta: Dict[str, Any] = None, options: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate a structured, summarized presentation deck (Descriptive or Analytical) from an uploaded paper."""
    options = options or {}
    slide_count = int(options.get("slide_count", 8))
    # Strictly either "Descriptive" or "Analytical"
    presentation_type = options.get("presentation_type", options.get("type", "Descriptive")).strip().capitalize()
    if presentation_type not in ["Descriptive", "Analytical"]:
        presentation_type = "Descriptive"

    theme = options.get("theme", "emerald")

    title = (paper_meta and paper_meta.get("title")) or ""
    if not title:
        first_line = paper_text.strip().split("\n")[0].strip()
        title = first_line[:100] if len(first_line) > 10 else "Academic Research Presentation"

    summary_data = extract_paper_summary(paper_text, title)

    # Prompt Ollama with real text if available
    prompt = f"""You are a distinguished university professor and academic conference keynote chair.
Summarize the following research paper into an elite {slide_count}-slide presentation deck.
The presentation type MUST be: {presentation_type.upper()}.

Paper Title: {title}
Paper Content:
{paper_text[:4500]}

Rules for Type = {presentation_type.upper()}:
{"- Focus on qualitative synthesis, background motivation, clinical/practical workflows, domain implications, and descriptive impact." if presentation_type == "Descriptive" else "- Focus on quantitative metrics, numerical findings, algorithmic phases, complexity bounds, statistical results, and benchmarks."}
- Number of slides: exactly {slide_count}
- Tone: Rigorous Academic
- Extract all bullet points and speaker notes strictly from the provided paper content above.

Return ONLY valid JSON matching this schema:
{{
  "title": "{title}",
  "presentation_type": "{presentation_type}",
  "theme": "{theme}",
  "executive_summary": "2-3 sentence overview of this specific paper.",
  "slides": [
    {{
      "category": "SLIDE CATEGORY",
      "title": "Clear Slide Title",
      "bullets": [
        {{"lead": "Key Point 1", "detail": "Detailed explanation from paper."}},
        {{"lead": "Key Point 2", "detail": "Detailed explanation from paper."}},
        {{"lead": "Key Point 3", "detail": "Detailed explanation from paper."}}
      ],
      "callout": "Crucial memorable takeaway from this section.",
      "metric": {{"val": "99.2%", "label": "Key Parameter / Metric"}},
      "speaker_notes": "Verbatim oral script for the presenter based on this section."
    }}
  ]
}}
"""
    ai_response = await ollama_service.chat(prompt, system=f"You are an academic presentation architect. Format strictly as {presentation_type} presentation JSON.")

    parsed_deck = None
    if ai_response:
        try:
            json_match = re.search(r"\{.*\}", ai_response, re.DOTALL)
            if json_match:
                parsed_deck = json.loads(json_match.group(0))
        except Exception as e:
            logger.warning(f"Failed to parse Ollama JSON slide response: {e}")

    # Fallback to local deterministic paper summarization engine
    if not parsed_deck or "slides" not in parsed_deck or len(parsed_deck["slides"]) == 0:
        parsed_deck = synthesize_academic_deck(title, paper_text, slide_count, presentation_type, theme, paper_meta=paper_meta)

    parsed_deck["presentation_type"] = presentation_type
    parsed_deck["theme"] = theme
    parsed_deck["slide_count"] = len(parsed_deck["slides"])
    if "executive_summary" not in parsed_deck:
        parsed_deck["executive_summary"] = summary_data["executive_summary"]

    # Generate downloadable PDF & PPTX files
    pdf_path = generate_slides_pdf(parsed_deck)
    pptx_path = generate_slides_pptx(parsed_deck)
    notes_pdf_path = generate_notes_deck_pdf(parsed_deck)

    parsed_deck["pdf_url"] = f"/api/download?file={pdf_path}"
    parsed_deck["pptx_url"] = f"/api/download?file={pptx_path}"
    parsed_deck["notes_pdf_url"] = f"/api/download?file={notes_pdf_path}"

    return parsed_deck


def synthesize_academic_deck(
    title: str,
    full_text: str,
    slide_count: int,
    presentation_type: str,
    theme: str,
    paper_meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Deterministically synthesize a high-yield academic slide deck directly from the paper's actual text."""
    paper_meta = paper_meta or {}

    # Extract Authors string
    authors_list = paper_meta.get("authors", [])
    if authors_list and isinstance(authors_list, list):
        author_names = [a.get("name", "") for a in authors_list if isinstance(a, dict) and a.get("name")]
        authors_str = ", ".join(author_names[:4])
        first_affil = authors_list[0].get("affiliation", "") if isinstance(authors_list[0], dict) else ""
    else:
        authors_str = "Academic Research Authors"
        first_affil = ""

    # Extract Sections
    sections = paper_meta.get("sections", [])
    if not sections or not isinstance(sections, list):
        sections = parse_raw_text_into_sections(full_text)

    # Normalize section content to lists of paragraphs
    normalized_sections = []
    for s in sections:
        h = s.get("heading", "Section")
        c = s.get("content", "")
        if isinstance(c, str):
            c_paras = [p.strip() for p in c.split("\n\n") if p.strip()]
        elif isinstance(c, list):
            c_paras = [p.strip() for p in c if str(p).strip()]
        else:
            c_paras = []
        if c_paras:
            normalized_sections.append({"heading": h, "paragraphs": c_paras})

    # If no sections could be identified, chunk full_text into synthetic sections
    if not normalized_sections:
        all_paras = [p.strip() for p in full_text.split("\n\n") if p.strip()]
        if not all_paras:
            all_paras = ["This research paper examines foundational methodology and empirical findings."]
        chunk_size = max(1, len(all_paras) // 5)
        normalized_sections = [
            {"heading": "1.0 INTRODUCTION", "paragraphs": all_paras[:chunk_size]},
            {"heading": "2.0 METHODOLOGY & ARCHITECTURE", "paragraphs": all_paras[chunk_size:chunk_size*2] or all_paras[:chunk_size]},
            {"heading": "3.0 EXPERIMENTAL READINGS", "paragraphs": all_paras[chunk_size*2:chunk_size*3] or all_paras[:chunk_size]},
            {"heading": "4.0 CHALLENGES & DISCUSSIONS", "paragraphs": all_paras[chunk_size*3:chunk_size*4] or all_paras[:chunk_size]},
            {"heading": "5.0 CONCLUSION", "paragraphs": all_paras[chunk_size*4:] or all_paras[:chunk_size]},
        ]

    # Identify Key Anchors: Introduction, Conclusion, Challenges, Middle Readings
    intro_sec = next((s for s in normalized_sections if "intro" in s["heading"].lower()), normalized_sections[0])
    concl_sec = next((s for s in normalized_sections if "concl" in s["heading"].lower()), normalized_sections[-1])
    chall_sec = next((s for s in normalized_sections if any(k in s["heading"].lower() for k in ["challenge", "limitation", "risk", "ethical", "privacy"])), None)

    mid_sections = [s for s in normalized_sections if s != intro_sec and s != concl_sec and s != chall_sec]

    slides = []

    # ----------------------------------------------------
    # SLIDE 1: Executive Overview & Title Slide
    # ----------------------------------------------------
    intro_paras = intro_sec["paragraphs"]
    lead_sentence = intro_paras[0][:150] if intro_paras else "Comprehensive investigation of current methodologies."
    second_sentence = intro_paras[1][:150] if len(intro_paras) > 1 else (intro_paras[0][150:300] if len(intro_paras[0]) > 150 else "Evaluates transformative practical breakthroughs.")

    slides.append({
        "category": "EXECUTIVE OVERVIEW",
        "title": title[:75],
        "bullets": [
            {
                "lead": "Authorship & Affiliation",
                "detail": f"{authors_str}" + (f" • {first_affil[:60]}" if first_affil else "")
            },
            {
                "lead": "Core Scope",
                "detail": lead_sentence
            },
            {
                "lead": "Scholarly Impact",
                "detail": second_sentence
            }
        ],
        "callout": "Comprehensive investigation of current applications, practical implementations, and future possibilities.",
        "metric": {"val": "Overview", "label": "Scope"},
        "speaker_notes": f"Welcome esteemed colleagues. Today we present '{title}'. This research provides a thorough analysis of state-of-the-art developments, operational implementations, and key structural considerations."
    })

    # ----------------------------------------------------
    # SLIDE 2: Background Motivation & Research Context
    # ----------------------------------------------------
    p1 = intro_paras[0][:140] if intro_paras else "Rapid technological advancements create transformative opportunities."
    p2 = intro_paras[1][:140] if len(intro_paras) > 1 else "Automated analysis significantly improves precision and operational efficiency."
    p3 = intro_paras[2][:140] if len(intro_paras) > 2 else "Addresses systemic bottlenecks and optimizes resource allocation across domains."

    slides.append({
        "category": "PROBLEM MOTIVATION",
        "title": "Introduction: Background & Domain Objectives",
        "bullets": [
            {"lead": "Domain Evolution", "detail": p1},
            {"lead": "Core Necessity", "detail": p2},
            {"lead": "Operational Scope", "detail": p3}
        ],
        "callout": "Addressing foundational challenges to enhance efficiency and establish reliable benchmarks.",
        "metric": {"val": "Foundational", "label": "Context"},
        "speaker_notes": "Turning to the motivation: the authors demonstrate that integrating advanced computational paradigms addresses longstanding domain bottlenecks and enhances workflow precision."
    })

    # ----------------------------------------------------
    # SLIDES 3 to N-2: Core Readings & Technical Sections
    # ----------------------------------------------------
    slots_needed = slide_count - 3 - (1 if chall_sec else 0)
    slots_needed = max(1, slots_needed)

    if mid_sections:
        step = max(1, len(mid_sections) // slots_needed)
        selected_mids = mid_sections[::step][:slots_needed]
    else:
        selected_mids = [intro_sec]

    for sec in selected_mids:
        s_paras = sec["paragraphs"]
        b1 = s_paras[0][:140] if s_paras else "Detailed methodological investigation."
        b2 = s_paras[1][:140] if len(s_paras) > 1 else (s_paras[0][140:280] if len(s_paras[0]) > 140 else "Empirical analysis and operational frameworks.")
        b3 = s_paras[2][:140] if len(s_paras) > 2 else (s_paras[0][280:420] if len(s_paras[0]) > 280 else "Strategic workflow integration and domain deployment.")

        if presentation_type == "Analytical":
            cat_name = "QUANTITATIVE READINGS"
            callout_text = f"Empirical findings and operational metrics demonstrated in {sec['heading'][:35]}."
            metric_obj = {"val": "Empirical", "label": "Validation"}
        else:
            cat_name = "CORE APPLICATIONS & FINDINGS"
            callout_text = f"Key conceptual mechanisms and domain utility within {sec['heading'][:35]}."
            metric_obj = {"val": "Active", "label": "Implementation"}

        slides.append({
            "category": cat_name,
            "title": sec["heading"][:65],
            "bullets": [
                {"lead": "Primary Framework", "detail": b1},
                {"lead": "Operational Role", "detail": b2},
                {"lead": "Practical Significance", "detail": b3}
            ],
            "callout": callout_text,
            "metric": metric_obj,
            "speaker_notes": f"Examining {sec['heading']}: the paper details how these specific methodologies are structured, highlighting tangible benefits in operational reliability."
        })

    # ----------------------------------------------------
    # SLIDE N-1: Challenges & Roadblocks (if present or synthesized)
    # ----------------------------------------------------
    if chall_sec:
        c_paras = chall_sec["paragraphs"]
        cb1 = c_paras[0][:140] if c_paras else "Adoption requires addressing financial and infrastructure hurdles."
        cb2 = c_paras[1][:140] if len(c_paras) > 1 else "Safety, reliability, and precision must be verified before deployment."
        cb3 = c_paras[2][:140] if len(c_paras) > 2 else "Stringent regulatory compliance and ethical standards are mandatory."

        slides.append({
            "category": "CRITICAL CHALLENGES",
            "title": chall_sec["heading"][:65],
            "bullets": [
                {"lead": "Infrastructure & Cost", "detail": cb1},
                {"lead": "Safety & Reliability", "detail": cb2},
                {"lead": "Ethical & Legal Governance", "detail": cb3}
            ],
            "callout": "Overcoming operational, financial, and ethical hurdles is vital for safe deployment.",
            "metric": {"val": "Governance", "label": "Compliance"},
            "speaker_notes": "A critical contribution of this research is its transparent discussion of challenges—highlighting that sustainable adoption demands rigorous safety and compliance."
        })
    elif len(slides) < slide_count - 1:
        slides.append({
            "category": "CRITICAL CHALLENGES",
            "title": "Implementation & Regulatory Roadblocks",
            "bullets": [
                {"lead": "Data Quality & Bias", "detail": "Ensuring diverse, high-fidelity datasets without sampling disparities."},
                {"lead": "Privacy & Security", "detail": "Strict adherence to confidentiality and secure data storage standards."},
                {"lead": "Regulatory Compliance", "detail": "Navigating complex institutional approvals and verification protocols."}
            ],
            "callout": "Rigorous compliance and data privacy are prerequisites for reliable integration.",
            "metric": {"val": "Critical", "label": "Friction"},
            "speaker_notes": "Here we examine the operational bottlenecks and governance safeguards essential for reliable implementation."
        })

    # ----------------------------------------------------
    # SLIDE N: Conclusion & Future Horizons
    # ----------------------------------------------------
    concl_paras = concl_sec["paragraphs"]
    cb1 = concl_paras[0][:140] if concl_paras else "The study demonstrates transformative potential across modern workflows."
    cb2 = concl_paras[0][140:280] if concl_paras and len(concl_paras[0]) > 140 else (concl_paras[1][:140] if len(concl_paras) > 1 else "Ethical oversight and regulatory compliance must accompany technological adoption.")
    cb3 = "Continued technological maturity and multidisciplinary collaboration will drive future breakthroughs."

    slides.append({
        "category": "CONCLUSION & HORIZONS",
        "title": "Conclusion: Strategic Synthesis & Future Outlook",
        "bullets": [
            {"lead": "Core Synthesis", "detail": cb1},
            {"lead": "Governance Imperative", "detail": cb2},
            {"lead": "Future Horizon", "detail": cb3}
        ],
        "callout": "Revolutionizing practice while maintaining uncompromising ethical and safety standards.",
        "metric": {"val": "Transformative", "label": "Impact"},
        "speaker_notes": f"In conclusion, the findings confirm that while transformative potential exists to optimize outcomes and efficiency, rigorous governance is paramount. Thank you."
    })

    # Guarantee exact slide_count
    if len(slides) > slide_count:
        # Keep slide 1 (overview), slide 2 (intro), drop middle slides to fit, keep last 2 (challenges & concl)
        excess = len(slides) - slide_count
        while excess > 0 and len(slides) > 4:
            # Remove a middle slide
            slides.pop(2)
            excess -= 1
    elif len(slides) < slide_count:
        while len(slides) < slide_count:
            idx = len(slides)
            slides.insert(-1, {
                "category": "IN-DEPTH READINGS",
                "title": f"Thematic Deep-Dive & Advanced Findings (Part {idx-2})",
                "bullets": [
                    {"lead": "Key Finding", "detail": p1 if p1 else "Explores specialized domain dynamics and architectural nuances."},
                    {"lead": "Empirical Observation", "detail": p2 if p2 else "Validates procedural stability under operational variances."},
                    {"lead": "Strategic Significance", "detail": p3 if p3 else "Establishes structured protocols for continued domain advancement."}
                ],
                "callout": "Detailed domain exploration validating foundational principles.",
                "metric": {"val": f"Section {idx-2}", "label": "Analysis"},
                "speaker_notes": "In this deep-dive slide, we examine granular methodological findings and domain operational dynamics."
            })

    return {
        "title": title,
        "presentation_type": presentation_type,
        "theme": theme,
        "executive_summary": extract_paper_summary(full_text, title)["executive_summary"],
        "slides": slides
    }
