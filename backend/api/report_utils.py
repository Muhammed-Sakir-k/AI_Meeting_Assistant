import os
import io
import json
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)

def generate_pdf_report(meeting, transcript, summary, action_items) -> io.BytesIO:
    """
    Generates a beautifully styled PDF report of the meeting.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles for Premium Look
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#2A1B60'), # Deep indigo
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#4A32A8'),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8
    )
    
    meta_style = ParagraphStyle(
        'MetadataText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        textColor=colors.HexColor('#666666'),
        spaceAfter=15
    )

    story = []
    
    # Title
    story.append(Paragraph(meeting.title or "Meeting Summary Report", title_style))
    
    # Metadata
    date_str = meeting.date.strftime("%B %d, %Y at %I:%M %p") if meeting.date else "Unknown Date"
    lang_str = (meeting.language or "Unknown").upper()
    story.append(Paragraph(f"Date: {date_str}   |   Language: {lang_str}", meta_style))
    story.append(Spacer(1, 10))
    
    # Summary Section
    story.append(Paragraph("Executive Summary", h2_style))
    summary_text = summary.summary_text if summary else "No summary available."
    story.append(Paragraph(summary_text, body_style))
    story.append(Spacer(1, 10))
    
    # Key Decisions
    if summary and summary.key_decisions:
        story.append(Paragraph("Key Decisions", h2_style))
        try:
            decisions = json.loads(summary.key_decisions)
        except Exception:
            # Fallback if stored as text
            decisions = [summary.key_decisions] if isinstance(summary.key_decisions, str) else []
            
        if decisions:
            for dec in decisions:
                story.append(Paragraph(f"• {dec}", body_style))
        else:
            story.append(Paragraph("No major decisions logged.", body_style))
        story.append(Spacer(1, 10))
        
    # Action Items Table
    story.append(Paragraph("Action Items", h2_style))
    if action_items:
        # Table Header
        table_data = [["Owner", "Task Description", "Deadline"]]
        for item in action_items:
            table_data.append([
                item.owner or "Unassigned",
                item.task or "",
                item.deadline or "N/A"
            ])
            
        # Build Flowable Table
        col_widths = [100, 300, 104] # Fits 504 pt width (612 total - margins)
        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A32A8')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F5F5FC')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8F8FD')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D2D2D2')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 9.5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
            ('TOPPADDING', (0,1), (-1,-1), 6),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No action items extracted.", body_style))
        
    story.append(Spacer(1, 15))
    story.append(PageBreak()) # Put transcript on a separate page
    
    # Transcript Section
    story.append(Paragraph("Transcript", h2_style))
    if transcript:
        try:
            transcript_data = json.loads(transcript.text)
            segments = transcript_data.get("segments", [])
            for seg in segments:
                text = seg.get("text", "")
                conf = seg.get("confidence", 1.0)
                time_str = f"[{int(seg.get('start', 0)//60):02d}:{int(seg.get('start', 0)%60):02d}]"
                speaker_str = f"<b>{seg.get('speaker')}:</b> " if seg.get("speaker") else ""
                
                # Highlight low confidence segments in PDF with a subtle tag or italics
                if seg.get("is_low_confidence", False):
                    p_text = f"<b>{time_str}</b> {speaker_str}<i><font color='#B33A3A'>{text} (low-confidence: {conf})</font></i>"
                else:
                    p_text = f"<b>{time_str}</b> {speaker_str}{text}"
                    
                story.append(Paragraph(p_text, body_style))
        except Exception:
            # Fallback for plain text
            for line in transcript.text.split("\n"):
                if line.strip():
                    story.append(Paragraph(line.strip(), body_style))
    else:
        story.append(Paragraph("No transcript available.", body_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_docx_report(meeting, transcript, summary, action_items) -> io.BytesIO:
    """
    Generates a beautifully styled Word Document (DOCX) of the meeting.
    """
    doc = Document()
    
    # Document Style
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    
    # Header Title
    title = doc.add_paragraph()
    title_run = title.add_run(meeting.title or "Meeting Summary Report")
    title_run.bold = True
    title_run.font.size = Pt(24)
    title_run.font.color.rgb = RGBColor(0x2A, 0x1B, 0x60)
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    
    # Metadata
    date_str = meeting.date.strftime("%B %d, %Y at %I:%M %p") if meeting.date else "Unknown Date"
    lang_str = (meeting.language or "Unknown").upper()
    meta = doc.add_paragraph()
    meta_run = meta.add_run(f"Date: {date_str}   |   Language: {lang_str}")
    meta_run.italic = True
    meta_run.font.size = Pt(9.5)
    meta_run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    
    doc.add_paragraph().paragraph_format.space_after = Pt(10)
    
    # Summary
    doc.add_heading("Executive Summary", level=2)
    summary_text = summary.summary_text if summary else "No summary available."
    p_sum = doc.add_paragraph(summary_text)
    p_sum.paragraph_format.space_after = Pt(15)
    
    # Key Decisions
    if summary and summary.key_decisions:
        doc.add_heading("Key Decisions", level=2)
        try:
            decisions = json.loads(summary.key_decisions)
        except Exception:
            decisions = [summary.key_decisions] if isinstance(summary.key_decisions, str) else []
            
        if decisions:
            for dec in decisions:
                doc.add_paragraph(dec, style='List Bullet')
        else:
            doc.add_paragraph("No major decisions logged.")
        doc.add_paragraph().paragraph_format.space_after = Pt(10)
        
    # Action Items Table
    doc.add_heading("Action Items", level=2)
    if action_items:
        table = doc.add_table(rows=1, cols=3)
        table.style = 'Light Shading Accent 1'
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = 'Owner'
        hdr_cells[1].text = 'Task Description'
        hdr_cells[2].text = 'Deadline'
        
        # Style table headers
        for cell in hdr_cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    
        for item in action_items:
            row_cells = table.add_row().cells
            row_cells[0].text = item.owner or "Unassigned"
            row_cells[1].text = item.task or ""
            row_cells[2].text = item.deadline or "N/A"
    else:
        doc.add_paragraph("No action items extracted.")
        
    doc.add_page_break()
    
    # Transcript
    doc.add_heading("Transcript", level=2)
    if transcript:
        try:
            transcript_data = json.loads(transcript.text)
            segments = transcript_data.get("segments", [])
            for seg in segments:
                text = seg.get("text", "")
                start = seg.get("start", 0)
                time_str = f"[{int(start//60):02d}:{int(start%60):02d}] "
                
                p = doc.add_paragraph()
                r_time = p.add_run(time_str)
                r_time.bold = True
                
                if seg.get("speaker"):
                    r_spk = p.add_run(f"{seg.get('speaker')}: ")
                    r_spk.bold = True
                    
                r_text = p.add_run(text)
                if seg.get("is_low_confidence", False):
                    r_text.italic = True
                    p.add_run(" (low-confidence)")
        except Exception:
            for line in transcript.text.split("\n"):
                if line.strip():
                    doc.add_paragraph(line.strip())
    else:
        doc.add_paragraph("No transcript available.")
        
    # Save to memory stream
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
