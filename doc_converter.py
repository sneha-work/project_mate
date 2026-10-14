# doc_converter.py - Academic Document Parsing & 20-Style Formatting Engine
import re
import os
import docx
from typing import Dict, Any, List, Optional
from config import EXPORTS_DIR

# Define the 20 Popular Research-Paper Styles metadata and formatting rules
STYLES_REGISTRY = {
    "ieee": {
        "id": "ieee",
        "name": "IEEE Conference / Transactions",
        "category": "Engineering & CS",
        "columns": 2,
        "font_family": "Times-Roman",
        "citation_format": "Numbered bracketed [1]",
        "heading_style": "Roman numerals (I. INTRODUCTION)",
        "accent_color": "#002855",
        "margin_in": 0.75,
        "line_spacing": 1.05,
        "description": "Standard two-column format used across all IEEE conferences and transaction journals."
    },
    "acm": {
        "id": "acm",
        "name": "ACM Conference (sigconf)",
        "category": "Computer Science",
        "columns": 2,
        "font_family": "Helvetica",
        "citation_format": "Numbered bracketed [1]",
        "heading_style": "Bold Arabic numerals (1. INTRODUCTION)",
        "accent_color": "#007ea7",
        "margin_in": 0.75,
        "line_spacing": 1.1,
        "description": "Official Association for Computing Machinery proceedings standard format."
    },
    "apa7": {
        "id": "apa7",
        "name": "APA 7th Edition",
        "category": "Social & Behavioral Sciences",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Author-date (Smith & Lee, 2024)",
        "heading_style": "Title Case Bold Centered / Left",
        "accent_color": "#2c3e50",
        "margin_in": 1.0,
        "line_spacing": 1.5,
        "description": "American Psychological Association 7th edition manuscript format with 1-inch margins."
    },
    "harvard": {
        "id": "harvard",
        "name": "Harvard Referencing Style",
        "category": "Multidisciplinary",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Author-date (Johnson, 2023: 45)",
        "heading_style": "Hierarchical decimal (1.0, 1.1)",
        "accent_color": "#a51c30",
        "margin_in": 1.0,
        "line_spacing": 1.2,
        "description": "Widely used university referencing standard with alphabetical bibliography."
    },
    "springer_lncs": {
        "id": "springer_lncs",
        "name": "Springer LNCS (Lecture Notes in Computer Science)",
        "category": "Computer Science",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Numbered bracketed [1]",
        "heading_style": "Bold numbered (1 Introduction)",
        "accent_color": "#d9534f",
        "margin_in": 1.1,
        "line_spacing": 1.15,
        "description": "Compact single-column format for Springer Lecture Notes in Computer Science proceedings."
    },
    "elsevier": {
        "id": "elsevier",
        "name": "Elsevier (ScienceDirect Standard)",
        "category": "Life & Physical Sciences",
        "columns": 2,
        "font_family": "Times-Roman",
        "citation_format": "Author-date or numbered bracketed",
        "heading_style": "Numbered (1. Introduction)",
        "accent_color": "#ff6c00",
        "margin_in": 0.8,
        "line_spacing": 1.1,
        "description": "Elsevier flagship layout featuring structured abstract and author footnote affiliations."
    },
    "nature": {
        "id": "nature",
        "name": "Nature",
        "category": "Multidisciplinary Science",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Numbered superscripts 1,2",
        "heading_style": "Bold lowercase unnumbered",
        "accent_color": "#c40000",
        "margin_in": 0.9,
        "line_spacing": 1.15,
        "description": "High-impact layout with bold first-paragraph synopsis and compact superscript referencing."
    },
    "mla9": {
        "id": "mla9",
        "name": "MLA 9th Edition",
        "category": "Humanities & Literature",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Author-page (Miller 42)",
        "heading_style": "Unnumbered section titles",
        "accent_color": "#333333",
        "margin_in": 1.0,
        "line_spacing": 1.5,
        "description": "Modern Language Association format with top-left student/author header and Works Cited."
    },
    "chicago": {
        "id": "chicago",
        "name": "Chicago Manual of Style (17th Ed.)",
        "category": "History & Social Sciences",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Author-Date or Footnote bibliography",
        "heading_style": "Traditional centered title & headlines",
        "accent_color": "#800000",
        "margin_in": 1.0,
        "line_spacing": 1.3,
        "description": "Chicago Author-Date standard with rigorous citation and editorial presentation."
    },
    "vancouver": {
        "id": "vancouver",
        "name": "Vancouver Style (ICMJE)",
        "category": "Biomedicine & Healthcare",
        "columns": 1,
        "font_family": "Helvetica",
        "citation_format": "Numerical order of appearance (1)",
        "heading_style": "Standard uppercase/bold",
        "accent_color": "#005a9c",
        "margin_in": 0.9,
        "line_spacing": 1.2,
        "description": "Uniform requirements for biomedical journals with sequential numerical references."
    },
    "cell": {
        "id": "cell",
        "name": "Cell Press",
        "category": "Cellular & Molecular Biology",
        "columns": 1,
        "font_family": "Helvetica",
        "citation_format": "Author-date in text",
        "heading_style": "Summary, Results, Discussion, STAR Methods",
        "accent_color": "#009688",
        "margin_in": 0.85,
        "line_spacing": 1.15,
        "description": "Cell Press research article format with structured STAR Methods and resource highlights."
    },
    "oxford": {
        "id": "oxford",
        "name": "Oxford Academic (OUP)",
        "category": "Academic Press",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Author-date or numbered",
        "heading_style": "Small-caps / Roman section styling",
        "accent_color": "#002147",
        "margin_in": 1.0,
        "line_spacing": 1.25,
        "description": "Oxford University Press journals standard with elegant serif and running rules."
    },
    "mdpi": {
        "id": "mdpi",
        "name": "MDPI Open Access",
        "category": "Open Access Multidisciplinary",
        "columns": 1,
        "font_family": "Helvetica",
        "citation_format": "Numbered bracketed [1]",
        "heading_style": "Numbered bold with left color rule",
        "accent_color": "#185a9d",
        "margin_in": 0.8,
        "line_spacing": 1.15,
        "description": "Clean modern open-access layout with blue branding, structured abstract, and keywords."
    },
    "aip": {
        "id": "aip",
        "name": "AIP (American Institute of Physics)",
        "category": "Physics & Materials",
        "columns": 2,
        "font_family": "Times-Roman",
        "citation_format": "Numbered superscripts or brackets",
        "heading_style": "Uppercase centered Roman numerals",
        "accent_color": "#0d3b66",
        "margin_in": 0.75,
        "line_spacing": 1.05,
        "description": "Two-column physics format with compact equations and numerical citations."
    },
    "frontiers": {
        "id": "frontiers",
        "name": "Frontiers in Science",
        "category": "Multidisciplinary",
        "columns": 1,
        "font_family": "Helvetica",
        "citation_format": "Author-date (Smith et al., 2024)",
        "heading_style": "Clean sans-serif numbered sections",
        "accent_color": "#e05338",
        "margin_in": 0.85,
        "line_spacing": 1.2,
        "description": "Frontiers open science format with distinct author contribution block."
    },
    "plos_one": {
        "id": "plos_one",
        "name": "PLOS ONE",
        "category": "Science & Medicine",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Numbered bracketed [1]",
        "heading_style": "Bold Title Case with Data Availability block",
        "accent_color": "#006699",
        "margin_in": 0.9,
        "line_spacing": 1.25,
        "description": "Public Library of Science format with open data declaration and clear section headings."
    },
    "wiley": {
        "id": "wiley",
        "name": "Wiley Online Library",
        "category": "Scientific, Technical, Medical",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Numbered or Author-date",
        "heading_style": "Numbered bold (1 | INTRODUCTION)",
        "accent_color": "#005691",
        "margin_in": 0.9,
        "line_spacing": 1.2,
        "description": "Classic Wiley publishing format with vertical section dividers and metadata bars."
    },
    "taylor_francis": {
        "id": "taylor_francis",
        "name": "Taylor & Francis",
        "category": "Social, Cultural, Sciences",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Author-date (Chicago/APA based)",
        "heading_style": "Hierarchical numbered (1. Introduction)",
        "accent_color": "#336699",
        "margin_in": 1.0,
        "line_spacing": 1.2,
        "description": "Taylor & Francis journal standard with clean typography and running footers."
    },
    "cambridge": {
        "id": "cambridge",
        "name": "Cambridge University Press",
        "category": "Humanities, Law, Sciences",
        "columns": 1,
        "font_family": "Times-Roman",
        "citation_format": "Author-date or footnote numerals",
        "heading_style": "Small caps centered and elegant rules",
        "accent_color": "#003b46",
        "margin_in": 1.0,
        "line_spacing": 1.25,
        "description": "Refined British academic press design with classic running heads and serif body."
    },
    "emerald": {
        "id": "emerald",
        "name": "Emerald Publishing",
        "category": "Management & Business Research",
        "columns": 1,
        "font_family": "Helvetica",
        "citation_format": "Harvard author-date",
        "heading_style": "Emerald Structured Abstract Sections",
        "accent_color": "#007a78",
        "margin_in": 0.9,
        "line_spacing": 1.2,
        "description": "Emerald format characterized by structured abstract: Purpose, Methodology, Findings, Originality."
    }
}

def is_metadata_banner(line: str) -> bool:
    """Detect publisher, ISSN, DOI, and journal masthead banner lines."""
    l = line.lower().strip()
    if not l:
        return True
    return any(p in l for p in [
        "issn:", "isbn:", "doi:", "doi.org", "available at http", "published by",
        "open access", "cc-by", "journal of", "proceedings of", "volume ", "vol.",
        "issue ", "department of research", "received:", "accepted:", "revised:",
        "indexing terms", "terms of use"
    ]) or l.startswith("©") or l.startswith("copyright") or l.startswith("http://") or l.startswith("https://")


def parse_docx_file(file_path: str) -> Dict[str, Any]:
    """Parse a DOCX file into structured academic components strictly from uploaded content."""
    doc = docx.Document(file_path)
    paragraphs = []
    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt:
            paragraphs.append(txt)

    if not paragraphs:
        return {
            "title": "Untitled Research Paper",
            "authors": [{"name": "Author", "affiliation": ""}],
            "abstract": "",
            "keywords": [],
            "sections": [],
            "references": []
        }

    # 1. Identify True Manuscript Title
    title = ""
    title_idx = -1
    for i in range(min(14, len(paragraphs))):
        p = paragraphs[i]
        if is_metadata_banner(p):
            continue
        p_clean = p.strip()
        if len(p_clean) >= 15 and not p_clean.lower().startswith(("dr.", "prof.", "by ", "author", "1.", "1 ", "i.", "abstract")):
            title = p_clean
            title_idx = i
            break

    if not title:
        title = paragraphs[0]
        title_idx = 0

    # 2. Identify where first section begins
    first_sec_idx = len(paragraphs)
    for i in range(title_idx + 1, len(paragraphs)):
        p = paragraphs[i]
        p_lower = p.lower()
        if (
            re.match(r"^(\d+(\.\d+)*|[IVXLCDM]+\.?)\s+[A-Za-z]", p)
            or p_lower.startswith(("abstract", "1.0", "1 ", "i."))
            or (p.isupper() and len(p.split()) < 6 and not any(k in p_lower for k in ["college", "university", "department"]))
        ):
            first_sec_idx = i
            break

    # 3. Extract Real Authors & Affiliations
    authors = []
    current_author = None
    for line in paragraphs[title_idx + 1 : first_sec_idx]:
        if is_metadata_banner(line):
            continue
        line_clean = line.strip()
        if "email" in line_clean.lower() or "e-mail" in line_clean.lower() or line_clean.startswith("*"):
            continue

        is_affil = any(k in line_clean.lower() for k in [
            "professor", "department", "college", "university", "institute", "student",
            "faculty", "school of", "hospital", "laboratory", "ind.", "usa", "uk", "canada", "center"
        ])
        if is_affil:
            if current_author:
                current_author["affiliation"] = (current_author["affiliation"] + ", " + line_clean).strip(", ")
            elif authors:
                authors[-1]["affiliation"] = (authors[-1]["affiliation"] + ", " + line_clean).strip(", ")
        else:
            if "," in line_clean and not any(k in line_clean.lower() for k in ["dept", "univ", "college"]):
                for a_name in line_clean.split(","):
                    if a_name.strip():
                        authors.append({"name": a_name.strip(), "affiliation": ""})
                current_author = authors[-1] if authors else None
            else:
                current_author = {"name": line_clean, "affiliation": ""}
                authors.append(current_author)

    if not authors:
        authors = [{"name": "Author", "affiliation": ""}]

    # 4. Extract Abstract, Sections, and References
    abstract = ""
    keywords = []
    sections = []
    references = []
    current_section = None
    in_abstract = False
    in_references = False

    for i in range(first_sec_idx, len(paragraphs)):
        p = paragraphs[i]
        p_lower = p.lower()

        if p_lower.startswith("references") or p_lower.startswith("bibliography") or p_lower == "works cited":
            in_references = True
            continue

        if in_references:
            references.append(p)
            continue

        if p_lower.startswith("abstract"):
            in_abstract = True
            abstract_text = re.sub(r"^abstract[\s:\-—]*", "", p, flags=re.IGNORECASE).strip()
            if abstract_text:
                abstract = abstract_text
            continue

        if in_abstract and (p_lower.startswith("keywords") or p_lower.startswith("index terms")):
            in_abstract = False
            kw_text = re.sub(r"^(keywords|index terms)[\s:\-—]*", "", p, flags=re.IGNORECASE)
            keywords = [k.strip() for k in re.split(r"[,;]", kw_text) if k.strip()]
            continue

        if in_abstract:
            if any(p_lower.startswith(h) for h in ["1.", "1 ", "i.", "introduction"]):
                in_abstract = False
            else:
                abstract += ("\n" + p if abstract else p)
                continue

        # Detect Headings
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
            if current_section:
                sections.append(current_section)
            current_section = {"heading": p, "content": []}
        else:
            if current_section:
                current_section["content"].append(p)
            else:
                current_section = {"heading": "Introduction", "content": [p]}

    if current_section:
        sections.append(current_section)

    for s in sections:
        if isinstance(s["content"], list):
            s["content"] = "\n\n".join(s["content"])

    if not abstract and sections:
        first_sec_paras = sections[0].get("content", "").split("\n\n")
        if first_sec_paras:
            abstract = first_sec_paras[0][:400]

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "keywords": keywords,
        "sections": sections,
        "references": references
    }


def parse_pdf_file(file_path: str) -> Dict[str, Any]:
    """Parse an uploaded PDF research paper into structured academic components using PyMuPDF."""
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf

    doc = pymupdf.open(file_path)
    full_paragraphs = []
    for page in doc:
        blocks = page.get_text("blocks")
        for b in blocks:
            txt = b[4].strip()
            if txt:
                # Some blocks have multiple lines
                sub_lines = [l.strip() for l in txt.split("\n") if l.strip()]
                full_paragraphs.extend(sub_lines)

    if not full_paragraphs:
        return {
            "title": "Untitled Research Paper",
            "authors": [{"name": "Author", "affiliation": ""}],
            "abstract": "",
            "keywords": [],
            "sections": [],
            "references": []
        }

    # 1. Identify True Manuscript Title
    title = ""
    title_idx = -1
    for i in range(min(20, len(full_paragraphs))):
        p = full_paragraphs[i]
        if is_metadata_banner(p):
            continue
        p_clean = p.strip()
        if len(p_clean) >= 15 and not p_clean.lower().startswith(("dr.", "prof.", "by ", "author", "1.", "1 ", "i.", "abstract")):
            title = p_clean
            title_idx = i
            break

    if not title:
        title = full_paragraphs[0]
        title_idx = 0

    # 2. Identify First Section Index
    first_sec_idx = len(full_paragraphs)
    for i in range(title_idx + 1, len(full_paragraphs)):
        p = full_paragraphs[i]
        p_lower = p.lower()
        if (
            re.match(r"^(\d+(\.\d+)*|[IVXLCDM]+\.?)\s+[A-Za-z]", p)
            or p_lower.startswith(("abstract", "1.0", "1 ", "i."))
            or (p.isupper() and len(p.split()) < 6 and not any(k in p_lower for k in ["college", "university", "department"]))
        ):
            first_sec_idx = i
            break

    # 3. Extract Real Authors & Affiliations
    authors = []
    current_author = None
    for line in full_paragraphs[title_idx + 1 : first_sec_idx]:
        if is_metadata_banner(line):
            continue
        line_clean = line.strip()
        if "email" in line_clean.lower() or "e-mail" in line_clean.lower() or line_clean.startswith("*"):
            continue

        is_affil = any(k in line_clean.lower() for k in [
            "professor", "department", "college", "university", "institute", "student",
            "faculty", "school of", "hospital", "laboratory", "ind.", "usa", "uk", "canada", "center"
        ])
        if is_affil:
            if current_author:
                current_author["affiliation"] = (current_author["affiliation"] + ", " + line_clean).strip(", ")
            elif authors:
                authors[-1]["affiliation"] = (authors[-1]["affiliation"] + ", " + line_clean).strip(", ")
        else:
            if "," in line_clean and not any(k in line_clean.lower() for k in ["dept", "univ", "college"]):
                for a_name in line_clean.split(","):
                    if a_name.strip():
                        authors.append({"name": a_name.strip(), "affiliation": ""})
                current_author = authors[-1] if authors else None
            else:
                current_author = {"name": line_clean, "affiliation": ""}
                authors.append(current_author)

    if not authors:
        authors = [{"name": "Author", "affiliation": ""}]

    # 4. Extract Abstract, Sections, References
    abstract = ""
    keywords = []
    sections = []
    references = []
    current_section = None
    in_abstract = False
    in_references = False

    for i in range(first_sec_idx, len(full_paragraphs)):
        p = full_paragraphs[i]
        p_lower = p.lower()

        if p_lower.startswith("references") or p_lower.startswith("bibliography") or p_lower == "works cited":
            in_references = True
            continue

        if in_references:
            references.append(p)
            continue

        if p_lower.startswith("abstract"):
            in_abstract = True
            abstract_text = re.sub(r"^abstract[\s:\-—]*", "", p, flags=re.IGNORECASE).strip()
            if abstract_text:
                abstract = abstract_text
            continue

        if in_abstract and (p_lower.startswith("keywords") or p_lower.startswith("index terms")):
            in_abstract = False
            kw_text = re.sub(r"^(keywords|index terms)[\s:\-—]*", "", p, flags=re.IGNORECASE)
            keywords = [k.strip() for k in re.split(r"[,;]", kw_text) if k.strip()]
            continue

        if in_abstract:
            if any(p_lower.startswith(h) for h in ["1.", "1 ", "i.", "introduction"]):
                in_abstract = False
            else:
                abstract += ("\n" + p if abstract else p)
                continue

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
            if current_section:
                sections.append(current_section)
            current_section = {"heading": p, "content": []}
        else:
            if current_section:
                current_section["content"].append(p)
            else:
                current_section = {"heading": "Introduction", "content": [p]}

    if current_section:
        sections.append(current_section)

    for s in sections:
        if isinstance(s["content"], list):
            s["content"] = "\n\n".join(s["content"])

    if not abstract and sections:
        first_sec_paras = sections[0].get("content", "").split("\n\n")
        if first_sec_paras:
            abstract = first_sec_paras[0][:400]

    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "keywords": keywords,
        "sections": sections,
        "references": references
    }

def parse_latex_file(tex_content: str) -> Dict[str, Any]:
    """Parse a LaTeX .tex string into structured academic components strictly from uploaded content."""
    # Extract Title
    title_match = re.search(r"\\title(?:\[[^\]]*\])?\{([^}]+)\}", tex_content, re.DOTALL)
    title = clean_latex_macros(title_match.group(1)) if title_match else "Untitled Research Paper"
    
    # Extract Authors
    authors = []
    author_match = re.search(r"\\author(?:\[[^\]]*\])?\{([^}]+)\}", tex_content, re.DOTALL)
    if author_match:
        raw_authors = author_match.group(1)
        for chunk in re.split(r"\\and|\\quad|,", raw_authors):
            clean_a = clean_latex_macros(chunk).strip()
            if clean_a:
                authors.append({"name": clean_a, "affiliation": ""})
    if not authors:
        authors = [{"name": "Author", "affiliation": ""}]
        
    # Extract Abstract
    abstract_match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex_content, re.DOTALL)
    abstract = clean_latex_macros(abstract_match.group(1)).strip() if abstract_match else ""
    
    # Extract Keywords
    keywords = []
    kw_match = re.search(r"\\(?:keywords|IEEEkeywords)\{([^}]+)\}", tex_content)
    if kw_match:
        keywords = [k.strip() for k in re.split(r"[,;]", clean_latex_macros(kw_match.group(1))) if k.strip()]
        
    # Extract Sections
    section_matches = list(re.finditer(r"\\section\{([^}]+)\}(.*?)(?=\\section\{|\\begin\{thebibliography\}|\\bibliography\{|\\end\{document\}|$)", tex_content, re.DOTALL))
    sections = []
    for sm in section_matches:
        sec_title = clean_latex_macros(sm.group(1)).strip()
        sec_body = clean_latex_macros(sm.group(2)).strip()
        sections.append({
            "heading": sec_title,
            "content": sec_body
        })
        
    # Extract References
    references = []
    ref_match = re.search(r"\\begin\{thebibliography\}(.*?)\\end\{thebibliography\}", tex_content, re.DOTALL)
    if ref_match:
        bib_items = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{[^}]*\}(.*?)(?=\\bibitem|\Z)", ref_match.group(1), re.DOTALL)
        for bi in bib_items:
            clean_bi = clean_latex_macros(bi).strip()
            if clean_bi:
                references.append(clean_bi)
                
    return {
        "title": title,
        "authors": authors,
        "abstract": abstract,
        "keywords": keywords,
        "sections": sections,
        "references": references
    }

def generate_latex_code(paper: Dict[str, Any], style_meta: Dict[str, Any]) -> str:
    """Generate clean, compilable, publication-grade LaTeX (.tex) code conforming to selected style."""
    style_id = style_meta.get("id", "ieee")
    title = paper.get("title", "Untitled Manuscript")
    authors = paper.get("authors", [])
    abstract = paper.get("abstract", "")
    keywords = paper.get("keywords", [])
    sections = paper.get("sections", [])
    references = paper.get("references", [])

    if style_id == "ieee":
        doc_class = "\\documentclass[conference]{IEEEtran}"
        extra_pkgs = "\\usepackage{amsmath,amssymb,amsfonts}\n\\usepackage{algorithmic}\n\\usepackage{graphicx}\n\\usepackage{textcomp}\n\\usepackage{xcolor}\n\\usepackage{cite}"
    elif style_id == "acm":
        doc_class = "\\documentclass[sigconf]{acmart}"
        extra_pkgs = "\\usepackage{booktabs}"
    elif style_id == "springer_lncs":
        doc_class = "\\documentclass{llncs}"
        extra_pkgs = "\\usepackage{graphicx}\n\\usepackage{amsmath}"
    elif style_id == "elsevier":
        doc_class = "\\documentclass[preprint,12pt]{elsarticle}"
        extra_pkgs = "\\usepackage{amssymb}\n\\usepackage{amsmath}"
    elif style_id == "nature":
        doc_class = "\\documentclass[fleqn,10pt]{wlscirep}"
        extra_pkgs = "\\usepackage[utf8]{inputenc}\n\\usepackage[T1]{fontenc}"
    else:
        doc_class = "\\documentclass[11pt,a4paper]{article}"
        extra_pkgs = "\\usepackage[utf8]{inputenc}\n\\usepackage{amsmath,amssymb}\n\\usepackage{geometry}\n\\geometry{margin=1in}"

    author_blocks = []
    for a in authors:
        name = a.get("name", "Author")
        affil = a.get("affiliation", "")
        if style_id == "ieee":
            if affil:
                author_blocks.append(f"\\IEEEauthorblockN{{{name}}}\n\\IEEEauthorblockA{{{affil}}}")
            else:
                author_blocks.append(f"\\IEEEauthorblockN{{{name}}}")
        elif style_id == "acm":
            if affil:
                author_blocks.append(f"\\author{{{name}}}\n\\affiliation{{\\institution{{{affil}}}}}")
            else:
                author_blocks.append(f"\\author{{{name}}}")
        else:
            author_blocks.append(f"{name} ({affil})" if affil else name)

    if style_id == "ieee":
        author_tex = "\\author{\n" + " \\and\n".join(author_blocks) + "\n}"
    elif style_id == "acm":
        author_tex = "\n".join(author_blocks)
    else:
        author_tex = "\\author{" + " \\and ".join(author_blocks) + "}"

    lines = [
        f"% ========================================================================",
        f"% LaTeX Manuscript Generated by ResearchMate AI",
        f"% Style Target: {style_meta.get('name', 'Academic Style')} ({style_id})",
        f"% ========================================================================",
        doc_class,
        extra_pkgs,
        "",
        f"\\title{{{title}}}",
        author_tex,
        "\\date{\\today}",
        "",
        "\\begin{document}",
        "\\maketitle",
        ""
    ]

    if abstract:
        lines.append("\\begin{abstract}")
        lines.append(abstract)
        lines.append("\\end{abstract}")
        lines.append("")

    if keywords:
        if style_id == "ieee":
            lines.append(f"\\begin{{IEEEkeywords}}\n{', '.join(keywords)}\n\\end{{IEEEkeywords}}\n")
        else:
            lines.append(f"\\noindent\\textbf{{Keywords:}} {', '.join(keywords)}\\par\\vspace{{0.5em}}\n")

    for sec in sections:
        heading = sec.get("heading", "Section")
        clean_h = re.sub(r"^(\d+(\.\d+)*|[IVXLCDM]+\.)\s+", "", heading)
        lines.append(f"\\section{{{clean_h}}}")
        content = sec.get("content", "")
        lines.append(content)
        lines.append("")

    if references:
        lines.append("\\begin{thebibliography}{99}")
        for i, ref in enumerate(references):
            lines.append(f"\\bibitem{{ref{i+1}}} {ref}")
        lines.append("\\end{thebibliography}")

    lines.append("")
    lines.append("\\end{document}")
    return "\n".join(lines)

def clean_latex_macros(text: str) -> str:
    """Clean common LaTeX commands for display."""
    if not text:
        return ""
    text = re.sub(r"%.*?\n", "\n", text)
    text = re.sub(r"\\[a-zA-Z]+(?:\*|\[[^\]]*\])?\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+", " ", text)
    text = text.replace("{", "").replace("}", "").replace("$", "")
    return re.sub(r"\s+", " ", text).strip()

def get_sample_academic_paper() -> Dict[str, Any]:
    """Returns a rich, peer-reviewed sample paper for instant testing."""
    return {
        "title": "Quantum-Resilient Neural Architectures for Secure Autonomous Edge Systems",
        "authors": [
            {"name": "Dr. Elena Rostova", "affiliation": "Center for Cyber-Physical Intelligence, Stanford University"},
            {"name": "Prof. Marcus Thorne", "affiliation": "Quantum Information Systems Laboratory, MIT"},
            {"name": "Amina Al-Mansoor", "affiliation": "Department of Computer Science, ETH Zurich"}
        ],
        "abstract": "The transition to post-quantum cryptography necessitates robust redesign of edge machine learning inference pipelines. Existing cryptographic schemes introduce severe latency overheads (up to 340%) when embedded into low-power autonomous robotics. In this work, we propose QR-Net: a hardware-aware lattice-based neural acceleration framework combining polynomial ring masking with structured weight quantization. On hardware-in-the-loop benchmarks using robotic flight controllers, QR-Net achieves 4.8x faster lattice NTT polynomial multiplication while maintaining 99.2% classification accuracy on safety-critical perception tasks under active fault-injection attacks. Our mathematical guarantees establish provable security bounds under the Learning With Errors (LWE) hardness reduction.",
        "keywords": ["Post-Quantum Cryptography", "Autonomous Edge Systems", "Lattice Cryptography", "Neural Architecture Search", "Fault Injection Resilience"],
        "sections": [
            {
                "heading": "1. Introduction",
                "content": "Modern autonomous aerial and terrestrial platforms rely extensively on deep neural networks deployed on resource-constrained embedded edge processors. However, the impending availability of fault-tolerant quantum computers threatens traditional public-key infrastructure. Lattice-based cryptography—specifically schemes based on Ring Learning With Errors (Ring-LWE)—has emerged as the premier candidate for post-quantum defense. Unfortunately, modern edge microcontrollers lack the arithmetic pipeline bandwidth to compute modular polynomial multiplications without debilitating framerate drops in autonomous navigation."
            },
            {
                "heading": "2. Related Work & Theoretical Gap",
                "content": "Prior works such as Kyber-Edge (Chen et al., 2023) investigated systolic arrays for Number Theoretic Transforms (NTT). However, existing systems treat cryptographic verification and neural tensor execution as disjoint sequential stages. This disjoint scheduling incurs substantial cache thrashing and memory bus bottlenecks, leaving the system vulnerable to differential power analysis and transient memory corruption."
            },
            {
                "heading": "3. Proposed QR-Net Architecture",
                "content": "We formulate QR-Net as a unified co-design framework. First, weights are quantized into balanced ternary representations that directly align with modular polynomial coefficients. Second, we integrate a zero-overhead NTT accelerator that re-uses existing matrix multiply units (MACs) on the neural tensor processing unit. The underlying security guarantee reduces directly to the shortest vector problem (SVP) in ideal lattices."
            },
            {
                "heading": "4. Empirical Evaluation & Benchmarks",
                "content": "We implemented QR-Net on an ARM Cortex-M55 microcontroller paired with an Ethos-U55 microNPU, alongside a secondary evaluation on an NVIDIA Jetson Orin Nano. Our benchmark suite evaluates: (1) End-to-end perception latency (ms), (2) Microjoules per inference cycle, (3) Side-channel leakage via Test Vector Leakage Assessment (TVLA), and (4) Adversarial perturbation tolerance. Across 50,000 flight controller test cycles, QR-Net reduces post-quantum crypto latency from 84.2ms to 17.5ms with zero detectable side-channel leakage across 1,000,000 power traces."
            },
            {
                "heading": "5. Discussion & Future Directions",
                "content": "The findings demonstrate that cryptographic safety and neural real-time performance are not mutually exclusive. Future exploration includes scaling QR-Net to multi-agent swarm consensus protocols and formal verification of the microcode against timing side channels."
            },
            {
                "heading": "6. Conclusion",
                "content": "We introduced QR-Net, the first co-designed post-quantum resilient neural architecture for resource-bounded autonomous edge platforms. By unifying lattice polynomial operations with neural tensor pipelines, QR-Net achieves state-of-the-art efficiency while providing mathematically proven security against quantum adversaries."
            }
        ],
        "references": [
            "[1] Alkim, E., Ducas, L., Pöppelmann, T., & Schwabe, P. (2016). Post-quantum key exchange—a new hope. In USENIX Security Symposium (pp. 327-343).",
            "[2] Chen, L., Jordan, S., Liu, Y. K., Moody, D., Peralta, R., Perlner, R., & Smith-Tone, D. (2023). Report on post-quantum cryptography. NIST Special Publication, 800, 208.",
            "[3] He, K., Zhang, X., Ren, S., & Sun, J. (2016). Deep residual learning for image recognition. In Proceedings of the IEEE conference on computer vision and pattern recognition (pp. 770-778).",
            "[4] Lyubashevsky, V., Peikert, C., & Regev, O. (2013). On ideal lattices and learning with errors over rings. Journal of the ACM (JACM), 60(6), 1-35.",
            "[5] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. Advances in neural information processing systems, 30."
        ]
    }
