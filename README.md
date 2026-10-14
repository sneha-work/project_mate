# ResearchMate AI — Academic Research & Publication Suite

An elite academic companion engineered for professors, researchers, and university scholars. ResearchMate AI automates manuscript formatting into 20 premier academic styles, synthesizes presentation slides with speaker notes, surfaces at least 20 verified research papers with DOI links, formulates innovative research proposals, and tracks verified CORE A*/A conference deadlines.

## Color Palette & Aesthetic Design
- **Original Color Palette** (from design inspiration):
  - **Blush**: `#f2d7db`
  - **Dusty Rose**: `#d88c9a`
  - **Rich Burgundy**: `#5a0f1a`
  - **Deep Burgundy**: `#3d0910`
- **Design Inspiration**:
  - [SciSpace](https://scispace.com/) & [ORBIT Academic Formatter](https://orbit-research.app/): Clean research dashboard, dual-pane document previews, and elegant responsive layouts.
  - Neo-morphism / glassmorphism pill navigation dock, sunny visual architectural sanctuary hero, motivational research quotes, and rotating inspirational messages.

---

## 5 Functional Core Features

### 1. 20-Style Academic Paper Formatter (`/formatter`)
- **Upload Formats**: Microsoft Word (`.docx`), LaTeX (`.tex`), or Plain Text/Pasted text.
- **20 Popular Research Styles**:
  1. **IEEE Conference / Transactions** (Two-column, Roman numeral headings, bracketed numbers)
  2. **ACM Conference (sigconf)** (Two-column, Libertine/Helvetica, CCS classification)
  3. **APA 7th Edition** (1-inch margins, author-date citations, centered title)
  4. **Harvard Referencing** (Author-year, distinct single-column university format)
  5. **Springer LNCS** (Lecture Notes in Computer Science compact format)
  6. **Elsevier (ScienceDirect)** (Elsevier header banner, structured abstract)
  7. **Nature** (Serif typography, bold synopsis paragraph, superscript citations)
  8. **MLA 9th Edition** (Author header block, double-spaced layout, Works Cited)
  9. **Chicago Manual of Style (17th Ed.)** (Author-Date / Notes style)
  10. **Vancouver Style (ICMJE)** (Biomedical numerical order of appearance)
  11. **Cell Press** (Summary, Results, Discussion, STAR Methods)
  12. **Oxford Academic (OUP)** (Elegant serif title block, running headers)
  13. **MDPI Open Access** (Blue header accents, structured abstract)
  14. **AIP (American Institute of Physics)** (Two-column physics layout)
  15. **Frontiers in Science** (Author contributions block, modern open science)
  16. **PLOS ONE** (Data availability statement block, clean single column)
  17. **Wiley Online Library** (Classic editorial layout, keywords badges)
  18. **Taylor & Francis** (Standard academic article format)
  19. **Cambridge University Press** (Refined British academic typography)
  20. **Emerald Publishing** (Structured abstract: Purpose, Methodology, Findings, Originality)
- **Live Dual-Pane Preview**: Interactive document previewer matching selected typography and column formats.
- **Real Downloads**:
  - Publication-grade **PDF** (rendered with Python ReportLab with exact margins, headers, and footers).
  - Native Microsoft Word **DOCX** (generated via `python-docx`).
  - Native LaTeX **.tex** source code.

### 2. Presentation Slide Deck Generator (`/slides`)
- **Customizable Controls**: Slide count (5, 8, 12, 16 slides), presentation tone (Academic Defense, Conference Talk, Industry Briefing, Student Lecture), color theme (Blush & Burgundy, Academic Navy, Emerald), and content depth.
- **Interactive Slide Player**: Fullscreen presentation mode, Next/Previous navigation (supporting keyboard arrow keys), key takeaway cards, metric badges, and expandable speaker notes drawer.
- **Real Downloads**:
  - Landscape **PDF** slide deck.
  - Native editable PowerPoint **PPTX** (generated via `python-pptx`).

### 3. Verified Literature Discovery (`/literature`)
- **20+ Verified Research Papers Guarantee**: Real-time querying to arXiv API (`export.arxiv.org`) and peer-reviewed catalog.
- **Rich Verified Details**: Title, authors, year, venue, abstract, citation counts, direct paper URL, direct PDF download URL, and DOI.
- **BibTeX Citations**: 1-click modal to copy standard BibTeX entries.
- **Topic Autocomplete**: Dynamic suggestions dropdown while typing.
- **Real Download**: Export curated bibliography as a formatted **PDF**.

### 4. Innovative Research Idea Lab (`/ideas`)
- **Breakthrough Proposals**: Formulates 3 distinct research proposals complete with Novelty Hypothesis, Literature Gap critique, step-by-step Methodology, Experimental Protocol (datasets, baselines, metrics), Challenges & Mitigations, and Target Venues.
- **Feasibility Scores**: Realistic feasibility rating (1-10) and estimated project timeline.
- **Real Download**: Export research proposal as a publication-grade **PDF**.

### 5. Verified Conferences Finder (`/conferences`)
- **Verified Venues & Dates**: Comprehensive listings of premier CORE A* and A conferences (NeurIPS, ICML, CVPR, ICLR, ACL, KDD, IEEE S&P, OSDI, CHI, etc.).
- **Live Countdown Timers**: Visual days remaining counter with urgency indicators for submission deadlines.
- **Verified Links**: Direct links to official conference portals and Calls for Papers (CFP).
- **Real Download**: Export upcoming deadlines calendar as a formatted **PDF**.

---

## Authentication, Profile, History & Settings
- **Google Login & 1-Click Guest Access**: Immediate full access without OAuth friction, plus simulated/configurable Google OAuth.
- **Scholar Profile**: Research metrics, tracked papers, and personal details.
- **History & Library**: Dedicated tabs for Formatted Papers, Slide Decks, Literature Searches, Saved Ideas, and Tracked Conferences.
- **Ollama Cloud API Integration**: Securely loads `OLLAMA_API_KEY`, `OLLAMA_HOST`, and `OLLAMA_MODEL` from environment variables, backed by a deterministic academic fallback engine so the platform works 100% out of the box on any device without local model downloads!
- **Dark & Light Modes**: Seamless theme switching with smooth transitions.

---

## Quick Start & Running Instructions

### 1. Requirements
- Python 3.10+
- Dependencies installed via `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Start the Server
```bash
python run.py
```
Open your browser to `http://localhost:8000`.

### 3. Run the Verification Test Suite
```bash
python test_suite.py
```
Verifies all 5 features and real document downloads end-to-end.
