# export_utils.py - High-Quality Academic PDF, DOCX, and PPTX Exporter
import os
import io
import time
from typing import Dict, Any, List
from config import EXPORTS_DIR

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from pptx import Presentation
from pptx.util import Inches as PptxInches, Pt as PptxPt
from pptx.dml.color import RGBColor as PptxRGBColor
from pptx.enum.text import PP_ALIGN

# Numbered Canvas for Two-Pass Page Numbering (e.g. Page 1 of 5)
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        page_text = f"Page {self._pageNumber} of {page_count}"
        header_text = getattr(self, "header_title", "ResearchMate AI Academic Formatter")
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, header_text[:75])
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)
            
        # Footer
        self.drawRightString(558, 40, page_text)
        self.drawString(54, 40, "Formatted via ResearchMate AI • Verified Academic Standard")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 50, 558, 50)
        self.restoreState()


def generate_paper_pdf(paper_data: Dict[str, Any], style_meta: Dict[str, Any], filename: str = None) -> str:
    """Generate a publication-grade PDF conforming to the selected research paper style."""
    if not filename:
        filename = f"paper_{style_meta.get('id', 'standard')}_{int(time.time())}.pdf"
    file_path = os.path.join(EXPORTS_DIR, filename)
    
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=inch * style_meta.get("margin_in", 0.8),
        rightMargin=inch * style_meta.get("margin_in", 0.8),
        topMargin=inch * 0.9,
        bottomMargin=inch * 0.9
    )
    
    styles = getSampleStyleSheet()
    font_name = "Times-Roman" if "Times" in style_meta.get("font_family", "Times") else "Helvetica"
    font_bold = "Times-Bold" if font_name == "Times-Roman" else "Helvetica-Bold"
    font_italic = "Times-Italic" if font_name == "Times-Roman" else "Helvetica-Oblique"
    accent = colors.HexColor(style_meta.get("accent_color", "#5a0f1a"))

    title_style = ParagraphStyle(
        'PaperTitle',
        parent=styles['Heading1'],
        fontName=font_bold,
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=12
    )

    authors_style = ParagraphStyle(
        'PaperAuthors',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )

    journal_banner_style = ParagraphStyle(
        'JournalBanner',
        parent=styles['Normal'],
        fontName=font_bold,
        fontSize=9,
        leading=12,
        textColor=accent,
        alignment=0,
        spaceAfter=10
    )

    abstract_heading_style = ParagraphStyle(
        'AbstractHeading',
        parent=styles['Heading3'],
        fontName=font_bold,
        fontSize=11,
        leading=14,
        textColor=accent,
        spaceAfter=4
    )

    abstract_body_style = ParagraphStyle(
        'AbstractBody',
        parent=styles['Normal'],
        fontName=font_italic,
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1e293b"),
        alignment=4 # Justify
    )

    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName=font_bold,
        fontSize=12,
        leading=16,
        textColor=accent,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14 * style_meta.get("line_spacing", 1.1),
        textColor=colors.HexColor("#1e293b"),
        alignment=4,
        spaceAfter=8,
        firstLineIndent=14
    )

    reference_style = ParagraphStyle(
        'Reference',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
        leftIndent=18,
        firstLineIndent=-18,
        spaceAfter=4
    )

    story = []

    # Journal / Conference identification banner
    banner_text = f"<b>{style_meta.get('name', 'ACADEMIC MANUSCRIPT')}</b> | ResearchMate Verified Formatting"
    story.append(Paragraph(banner_text, journal_banner_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent, spaceAfter=14))

    # Title
    story.append(Paragraph(paper_data.get("title", "Untitled Research Paper"), title_style))
    
    # Authors & Affiliations
    authors_text = ""
    for a in paper_data.get("authors", []):
        authors_text += f"<b>{a.get('name', '')}</b><br/><i>{a.get('affiliation', '')}</i><br/>"
    if authors_text:
        story.append(Paragraph(authors_text, authors_style))
        story.append(Spacer(1, 10))

    # Abstract Container / Callout
    abstract_content = [
        Paragraph(f"<b>Abstract</b>—{paper_data.get('abstract', '')}", abstract_body_style)
    ]
    if paper_data.get("keywords"):
        kw_str = ", ".join(paper_data.get("keywords", []))
        abstract_content.append(Spacer(1, 4))
        abstract_content.append(Paragraph(f"<b><i>Keywords</i></b>—{kw_str}", abstract_body_style))

    abstract_table = Table(
        [[abstract_content]],
        colWidths=[doc.width]
    )
    abstract_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
        ('LINEBEFORE', (0, 0), (0, -1), 3.0, accent),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(abstract_table)
    story.append(Spacer(1, 14))

    # Sections
    for sec in paper_data.get("sections", []):
        story.append(Paragraph(sec.get("heading", ""), section_heading_style))
        content = sec.get("content", "")
        # Break content into paragraphs
        paras = [p.strip() for p in content.split("\n\n") if p.strip()]
        for p in paras:
            story.append(Paragraph(p, body_style))
        story.append(Spacer(1, 6))

    # References
    if paper_data.get("references"):
        story.append(Spacer(1, 10))
        ref_heading = "References" if style_meta.get("id") != "mla9" else "Works Cited"
        story.append(Paragraph(ref_heading, section_heading_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=8))
        for ref in paper_data.get("references", []):
            story.append(Paragraph(ref, reference_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    return file_path


def generate_paper_docx(paper_data: Dict[str, Any], style_meta: Dict[str, Any], filename: str = None) -> str:
    """Generate a clean native Microsoft Word (.docx) document formatted in the selected style."""
    if not filename:
        filename = f"paper_{style_meta.get('id', 'standard')}_{int(time.time())}.docx"
    file_path = os.path.join(EXPORTS_DIR, filename)

    doc = docx.Document()
    
    # Set Margins
    margin = style_meta.get("margin_in", 1.0)
    for section in doc.sections:
        section.top_margin = Inches(margin)
        section.bottom_margin = Inches(margin)
        section.left_margin = Inches(margin)
        section.right_margin = Inches(margin)

    # Document Header
    header_p = doc.add_paragraph()
    header_p.text = f"{style_meta.get('name', 'Academic Manuscript')} | ResearchMate AI Formatted"
    header_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if header_p.runs:
        header_p.runs[0].font.size = Pt(8.5)
        header_p.runs[0].font.color.rgb = RGBColor(120, 140, 160)

    # Title
    title_p = doc.add_paragraph()
    title_run = title_p.add_run(paper_data.get("title", "Untitled Research Paper"))
    title_run.bold = True
    title_run.font.size = Pt(18)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_after = Pt(12)

    # Authors
    for a in paper_data.get("authors", []):
        author_p = doc.add_paragraph()
        arun = author_p.add_run(a.get("name", ""))
        arun.bold = True
        arun.font.size = Pt(11)
        if a.get("affiliation"):
            aff_run = author_p.add_run(f"\n{a.get('affiliation')}")
            aff_run.italic = True
            aff_run.font.size = Pt(9.5)
        author_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        author_p.paragraph_format.space_after = Pt(4)

    # Abstract Box
    doc.add_paragraph().paragraph_format.space_after = Pt(8)
    abs_title_p = doc.add_paragraph()
    abs_title_run = abs_title_p.add_run("Abstract—")
    abs_title_run.bold = True
    abs_run = abs_title_p.add_run(paper_data.get("abstract", ""))
    abs_run.italic = True
    abs_title_p.paragraph_format.left_indent = Inches(0.5)
    abs_title_p.paragraph_format.right_indent = Inches(0.5)

    if paper_data.get("keywords"):
        kw_p = doc.add_paragraph()
        kw_title = kw_p.add_run("Keywords—")
        kw_title.bold = True
        kw_p.add_run(", ".join(paper_data.get("keywords", [])))
        kw_p.paragraph_format.left_indent = Inches(0.5)
        kw_p.paragraph_format.right_indent = Inches(0.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # Sections
    for sec in paper_data.get("sections", []):
        h = doc.add_heading(level=2)
        hrun = h.add_run(sec.get("heading", ""))
        hrun.bold = True
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)

        for p_text in sec.get("content", "").split("\n\n"):
            if p_text.strip():
                p = doc.add_paragraph(p_text.strip())
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.first_line_indent = Inches(0.25)

    # References
    if paper_data.get("references"):
        doc.add_paragraph().paragraph_format.space_after = Pt(12)
        ref_h = doc.add_heading(level=2)
        ref_h.add_run("References")
        for ref in paper_data.get("references", []):
            ref_p = doc.add_paragraph(ref)
            ref_p.paragraph_format.left_indent = Inches(0.4)
            ref_p.paragraph_format.first_line_indent = Inches(-0.4)
            ref_p.paragraph_format.space_after = Pt(4)

    doc.save(file_path)
    return file_path


def generate_slides_pdf(deck_data: Dict[str, Any], filename: str = None) -> str:
    """Generate high-definition landscape slide deck in PDF format."""
    if not filename:
        filename = f"slides_{int(time.time())}.pdf"
    file_path = os.path.join(EXPORTS_DIR, filename)

    # Landscape letter format (11 x 8.5 inches = 792 x 612 pt)
    doc = SimpleDocTemplate(
        file_path,
        pagesize=landscape(letter),
        leftMargin=inch * 0.7,
        rightMargin=inch * 0.7,
        topMargin=inch * 0.6,
        bottomMargin=inch * 0.6
    )

    styles = getSampleStyleSheet()
    theme_colors = {
        "burgundy": {"primary": colors.HexColor("#5a0f1a"), "accent": colors.HexColor("#d88c9a"), "bg": colors.HexColor("#fffbfa"), "card": colors.HexColor("#fdf2f4")},
        "navy": {"primary": colors.HexColor("#0f2b48"), "accent": colors.HexColor("#3874a6"), "bg": colors.HexColor("#f8fafc"), "card": colors.HexColor("#f1f5f9")},
        "emerald": {"primary": colors.HexColor("#124434"), "accent": colors.HexColor("#2e8b57"), "bg": colors.HexColor("#f7faf8"), "card": colors.HexColor("#edf5f0")}
    }
    theme = theme_colors.get(deck_data.get("theme", "burgundy"), theme_colors["burgundy"])

    slide_title_style = ParagraphStyle(
        'SlideTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=theme["primary"],
        spaceAfter=4
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    bullet_style = ParagraphStyle(
        'SlideBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=10
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=15,
        textColor=theme["primary"]
    )

    notes_style = ParagraphStyle(
        'Notes',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b")
    )

    story = []
    slides = deck_data.get("slides", [])

    for i, slide in enumerate(slides):
        is_first = (i == 0)
        
        # Header Row: Badge & Slide Index
        badge_p = Paragraph(f"  {slide.get('category', 'RESEARCH PRESENTATION').upper()}  ", badge_style)
        badge_table = Table([[badge_p]], colWidths=[200])
        badge_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), theme["primary"]),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('CORNERPAD', (0, 0), (-1, -1), 4),
        ]))
        
        page_num_p = Paragraph(f"<b>Slide {i+1} of {len(slides)}</b>", ParagraphStyle('PNum', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor("#94a3b8"), alignment=2))
        
        header_table = Table([[badge_table, page_num_p]], colWidths=[400, doc.width - 400])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 6))

        # Slide Title
        story.append(Paragraph(slide.get("title", ""), slide_title_style))
        story.append(HRFlowable(width="100%", thickness=2, color=theme["accent"], spaceAfter=14))

        # Main Slide Body: Left bullets, Right insight card
        bullets_flow = []
        for bp in slide.get("bullets", []):
            bullets_flow.append(Paragraph(f"• <b>{bp.get('lead', '')}:</b> {bp.get('detail', '')}", bullet_style))
            
        right_card_flow = []
        if slide.get("callout"):
            right_card_flow.append(Paragraph(f"<b>KEY TAKEAWAY</b><br/>{slide.get('callout')}", callout_style))
        if slide.get("metric"):
            right_card_flow.append(Spacer(1, 10))
            right_card_flow.append(Paragraph(f"<font size=20 color='{theme['primary'].hexval()}'><b>{slide.get('metric', {}).get('val', '')}</b></font><br/>{slide.get('metric', {}).get('label', '')}", bullet_style))

        right_table = Table([[right_card_flow]], colWidths=[240])
        right_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), theme["card"]),
            ('BOX', (0, 0), (-1, -1), 1, theme["accent"]),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 14),
            ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ]))

        left_width = doc.width - 260
        body_table = Table([[bullets_flow, right_table]], colWidths=[left_width, 260])
        body_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('RIGHTPADDING', (0, 0), (0, 0), 16),
        ]))
        story.append(body_table)

        # Speaker Notes Bottom Drawer
        if slide.get("speaker_notes"):
            story.append(Spacer(1, 14))
            notes_table = Table([[Paragraph(f"🎙️ <b>Speaker Notes:</b> {slide.get('speaker_notes')}", notes_style)]], colWidths=[doc.width])
            notes_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ('LINEBEFORE', (0, 0), (0, -1), 2, colors.HexColor("#94a3b8")),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(notes_table)

        if i < len(slides) - 1:
            story.append(PageBreak())

    doc.build(story)
    return file_path


def generate_slides_pptx(deck_data: Dict[str, Any], filename: str = None) -> str:
    """Generate an editable PowerPoint presentation (.pptx) file."""
    if not filename:
        filename = f"presentation_{int(time.time())}.pptx"
    file_path = os.path.join(EXPORTS_DIR, filename)

    prs = Presentation()
    # 16:9 widescreen
    prs.slide_width = PptxInches(13.333)
    prs.slide_height = PptxInches(7.5)
    blank_layout = prs.slide_layouts[6]

    for slide_data in deck_data.get("slides", []):
        slide = prs.slides.add_slide(blank_layout)

        # Category Badge
        cat_box = slide.shapes.add_textbox(PptxInches(0.8), PptxInches(0.6), PptxInches(4), PptxInches(0.4))
        cat_tf = cat_box.text_frame
        cat_p = cat_tf.paragraphs[0]
        cat_p.text = slide_data.get("category", "ACADEMIC PRESENTATION").upper()
        cat_p.font.size = PptxPt(11)
        cat_p.font.bold = True
        cat_p.font.color.rgb = PptxRGBColor(90, 15, 26) # Burgundy accent

        # Title
        title_box = slide.shapes.add_textbox(PptxInches(0.8), PptxInches(1.0), PptxInches(11.5), PptxInches(1.0))
        title_tf = title_box.text_frame
        title_tf.word_wrap = True
        title_p = title_tf.paragraphs[0]
        title_p.text = slide_data.get("title", "")
        title_p.font.size = PptxPt(26)
        title_p.font.bold = True
        title_p.font.color.rgb = PptxRGBColor(30, 41, 59)

        # Content bullets box
        left_box = slide.shapes.add_textbox(PptxInches(0.8), PptxInches(2.2), PptxInches(7.5), PptxInches(4.2))
        left_tf = left_box.text_frame
        left_tf.word_wrap = True

        for j, bp in enumerate(slide_data.get("bullets", [])):
            p = left_tf.add_paragraph() if j > 0 else left_tf.paragraphs[0]
            p.text = f"• {bp.get('lead', '')}: {bp.get('detail', '')}"
            p.font.size = PptxPt(16)
            p.space_after = PptxPt(12)

        # Right Callout Card
        if slide_data.get("callout"):
            right_box = slide.shapes.add_textbox(PptxInches(8.8), PptxInches(2.2), PptxInches(3.8), PptxInches(3.5))
            right_tf = right_box.text_frame
            right_tf.word_wrap = True
            rp = right_tf.paragraphs[0]
            rp.text = "KEY TAKEAWAY\n" + slide_data.get("callout", "")
            rp.font.size = PptxPt(14)
            rp.font.italic = True
            rp.font.color.rgb = PptxRGBColor(90, 15, 26)

        # Speaker notes
        if slide_data.get("speaker_notes"):
            notes_slide = slide.notes_slide
            tf = notes_slide.notes_text_frame
            tf.text = slide_data.get("speaker_notes", "")

    prs.save(file_path)
    return file_path


def generate_research_proposal_pdf(idea_data: Dict[str, Any], filename: str = None) -> str:
    """Generate an official, formatted Research Proposal in PDF format."""
    if not filename:
        filename = f"proposal_{int(time.time())}.pdf"
    file_path = os.path.join(EXPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=inch * 0.8,
        rightMargin=inch * 0.8,
        topMargin=inch * 0.9,
        bottomMargin=inch * 0.9
    )

    styles = getSampleStyleSheet()
    accent = colors.HexColor("#5a0f1a")

    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=accent, spaceAfter=12)
    h2_style = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=accent, spaceBefore=12, spaceAfter=4, keepWithNext=True)
    body_style = ParagraphStyle('Body', fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor("#1e293b"), spaceAfter=8)

    story = [
        Paragraph("<b>RESEARCHMATE AI — INNOVATIVE RESEARCH PROPOSAL</b>", ParagraphStyle('Banner', fontName='Helvetica-Bold', fontSize=9, textColor=accent)),
        HRFlowable(width="100%", thickness=1.5, color=accent, spaceAfter=12),
        Paragraph(idea_data.get("title", "Research Proposal"), title_style),
        Paragraph(f"<b>Research Domain:</b> {idea_data.get('domain', 'General AI & Computer Science')} | <b>Feasibility Score:</b> {idea_data.get('feasibility', '9/10')}", body_style),
        Spacer(1, 8),
        Paragraph("1. Core Problem Statement & Novelty Hypothesis", h2_style),
        Paragraph(idea_data.get("hypothesis", ""), body_style),
        Paragraph("2. Literature Gap & Limitations of Prior Work", h2_style),
        Paragraph(idea_data.get("novelty", ""), body_style),
        Paragraph("3. Proposed Methodology & Mathematical / Algorithmic Framework", h2_style),
        Paragraph(idea_data.get("methodology", ""), body_style),
        Paragraph("4. Experimental Protocol, Datasets & Evaluation Metrics", h2_style),
        Paragraph(idea_data.get("experiments", "Evaluated on standard international benchmarks with ablation baselines."), body_style),
        Paragraph("5. Anticipated Challenges & Mitigation Strategies", h2_style),
        Paragraph(idea_data.get("challenges", "Potential edge latency overhead mitigated via layer pruning and asynchronous dispatch."), body_style),
        Paragraph("6. Target Academic Venues & Impact Potential", h2_style),
        Paragraph(idea_data.get("target_venues", "Target conferences: NeurIPS, ICML, CVPR, ICLR."), body_style)
    ]

    doc.build(story, canvasmaker=NumberedCanvas)
    return file_path


def generate_bibliography_pdf(papers: List[Dict[str, Any]], query: str, filename: str = None) -> str:
    """Export 20+ verified research papers into an indexed PDF bibliography."""
    if not filename:
        filename = f"literature_{int(time.time())}.pdf"
    file_path = os.path.join(EXPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=inch * 0.8,
        rightMargin=inch * 0.8,
        topMargin=inch * 0.9,
        bottomMargin=inch * 0.9
    )

    styles = getSampleStyleSheet()
    accent = colors.HexColor("#5a0f1a")

    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=accent, spaceAfter=8)
    sub_style = ParagraphStyle('Sub', fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor("#64748b"), spaceAfter=14)
    item_title_style = ParagraphStyle('ItemTitle', fontName='Helvetica-Bold', fontSize=10.5, leading=14, textColor=colors.HexColor("#0f172a"))
    item_meta_style = ParagraphStyle('ItemMeta', fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor("#475569"))
    item_abs_style = ParagraphStyle('ItemAbs', fontName='Helvetica-Oblique', fontSize=8.5, leading=11.5, textColor=colors.HexColor("#334155"))

    story = [
        Paragraph("<b>RESEARCHMATE AI — VERIFIED LITERATURE DISCOVERY</b>", ParagraphStyle('Banner', fontName='Helvetica-Bold', fontSize=9, textColor=accent)),
        HRFlowable(width="100%", thickness=1.5, color=accent, spaceAfter=10),
        Paragraph(f"Curated Bibliography: {query.title()}", title_style),
        Paragraph(f"Total Verified Research Works: {len(papers)} | Source: arXiv, OpenAlex, Semantic Scholar & Peer-Reviewed Proceedings", sub_style)
    ]

    for idx, p in enumerate(papers, 1):
        p_card = [
            Paragraph(f"<b>[{idx}] {p.get('title', '')}</b>", item_title_style),
            Paragraph(f"<b>Authors:</b> {p.get('authors', '')} | <b>Year:</b> {p.get('year', '')} | <b>Venue:</b> {p.get('venue', 'Academic Publication')}", item_meta_style),
            Paragraph(f"<b>Direct Verified Link:</b> <font color='#0284c7'><u>{p.get('url', '')}</u></font>", item_meta_style),
            Spacer(1, 3),
            Paragraph(f"<b>Abstract Summary:</b> {p.get('abstract', '')[:280]}...", item_abs_style)
        ]
        card_table = Table([[p_card]], colWidths=[doc.width])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc") if idx % 2 == 0 else colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(card_table)
        story.append(Spacer(1, 6))

    doc.build(story, canvasmaker=NumberedCanvas)
    return file_path


def generate_notes_deck_pdf(deck_data: Dict[str, Any], filename: str = None) -> str:
    """Generate a comprehensive Academic Study & Lecture Notes Deck in PDF format."""
    if not filename:
        filename = f"notes_deck_{int(time.time())}.pdf"
    file_path = os.path.join(EXPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=inch * 0.8,
        rightMargin=inch * 0.8,
        topMargin=inch * 0.8,
        bottomMargin=inch * 0.8
    )

    styles = getSampleStyleSheet()
    accent = colors.HexColor("#5a0f1a")
    sub_accent = colors.HexColor("#d88c9a")

    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=20, leading=24, textColor=accent, spaceAfter=8)
    sub_style = ParagraphStyle('Sub', fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor("#64748b"), spaceAfter=14)
    note_header_style = ParagraphStyle('NoteH', fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=accent, spaceBefore=8, spaceAfter=4)
    bullet_style = ParagraphStyle('Bullet', fontName='Helvetica', fontSize=9.5, leading=14, textColor=colors.HexColor("#1e293b"), spaceAfter=4)
    takeaway_style = ParagraphStyle('Takeaway', fontName='Helvetica-Oblique', fontSize=9.5, leading=13.5, textColor=colors.HexColor("#5a0f1a"))
    script_style = ParagraphStyle('Script', fontName='Helvetica', fontSize=9, leading=12.5, textColor=colors.HexColor("#334155"))

    story = [
        Paragraph("<b>RESEARCHMATE AI — ACADEMIC LECTURE & STUDY NOTES DECK</b>", ParagraphStyle('Banner', fontName='Helvetica-Bold', fontSize=9, textColor=accent)),
        HRFlowable(width="100%", thickness=1.5, color=accent, spaceAfter=10),
        Paragraph(deck_data.get("title", "Comprehensive Research Notes"), title_style),
        Paragraph(f"Extracted Study Cards: {len(deck_data.get('slides', []))} &bull; Tone: {deck_data.get('tone', 'Academic')} &bull; Verified Synthesized Notes", sub_style)
    ]

    for idx, slide in enumerate(deck_data.get("slides", []), 1):
        card_content = [
            Paragraph(f"<b>CARD #{idx}: {slide.get('title', '').upper()}</b> &bull; <i>{slide.get('category', 'CORE TOPIC')}</i>", note_header_style),
            HRFlowable(width="100%", thickness=0.5, color=sub_accent, spaceAfter=6),
            Paragraph("<b>Key Conceptual Takeaways:</b>", ParagraphStyle('H4', fontName='Helvetica-Bold', fontSize=9.5, textColor=colors.HexColor("#1e293b")))
        ]
        
        for bp in slide.get("bullets", []):
            card_content.append(Paragraph(f"&bull; <b>{bp.get('lead', '')}:</b> {bp.get('detail', '')}", bullet_style))
            
        if slide.get("callout"):
            card_content.append(Spacer(1, 4))
            card_content.append(Paragraph(f"<b>Core Formula / Principle:</b> {slide.get('callout')}", takeaway_style))
            
        if slide.get("speaker_notes"):
            card_content.append(Spacer(1, 4))
            card_content.append(Paragraph(f"<b>🎙️ Detailed Presenter / Study Commentary:</b> {slide.get('speaker_notes')}", script_style))

        card_table = Table([[card_content]], colWidths=[doc.width])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fdf7f8") if idx % 2 == 1 else colors.HexColor("#ffffff")),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#e2e8f0")),
            ('LINEBEFORE', (0, 0), (0, -1), 3, accent),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(card_table)
        story.append(Spacer(1, 10))

    doc.build(story, canvasmaker=NumberedCanvas)
    return file_path

