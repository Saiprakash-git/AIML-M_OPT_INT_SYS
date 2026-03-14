import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from utils.storage import load_plant_config, load_batch_history
import json

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(_BASE_DIR, "results", "reports")
SIGNATURE_FILE = os.path.join(_BASE_DIR, "golden_signature.json")

# Ensure reports directory exists
os.makedirs(REPORTS_DIR, exist_ok=True)

def _load_golden_signatures() -> dict:
    if os.path.exists(SIGNATURE_FILE):
        with open(SIGNATURE_FILE, 'r') as f:
            try:
                return json.load(f)
            except:
                pass
    return {}

def generate_pdf_report() -> str:
    """
    Generates a PDF report compiling plant config, recent batch history, 
    and current golden signatures. Returns the absolute path to the PDF.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"OptiMFG_Plant_Report_{timestamp}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=20,
        alignment=1 # Center
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=20,
        spaceAfter=10,
        borderPadding=5
    )
    normal_style = styles['Normal']

    story = []

    # 1. Title & Header
    story.append(Paragraph("OptiMFG Automated System Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}", ParagraphStyle('Date', parent=normal_style, alignment=1, textColor=colors.gray)))
    story.append(Spacer(1, 30))

    # 2. Plant Configuration
    story.append(Paragraph("Current Plant Configuration", heading_style))
    config = load_plant_config()
    config_data = [
        ["Electricity Capacity", f"{config.get('electricity_capacity_kw', 0)} kW"],
        ["Machine Power Limit", f"{config.get('machine_power_limit_kw', 0)} kW"],
        ["Carbon Emission Limit", f"{config.get('carbon_emission_limit_kg', 0)} kg"],
        ["Default Config", config.get('default_machine_configuration', 'Standard')],
    ]
    
    t_config = Table(config_data, colWidths=[200, 200])
    t_config.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#334155')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
    ]))
    story.append(t_config)
    story.append(Spacer(1, 20))

    # 3. Golden Signatures
    story.append(Paragraph("Established Golden Signatures", heading_style))
    sigs = _load_golden_signatures()
    
    if sigs:
        for mode, data in sigs.items():
            story.append(Paragraph(f"<b>Mode:</b> {mode} (Batch Context: {data.get('batch_context', 'N/A')})", normal_style))
            p = data.get("predictions", {})
            sig_data = [
                ["Metric", "Value"],
                ["Quality Score", f"{p.get('Quality_Score', 0):.4f}"],
                ["Energy Consumed", f"{p.get('Energy_per_batch', 0):.2f} kWh"],
                ["Carbon Emission", f"{p.get('Carbon_emission', 0):.2f} kg"],
                ["Asset Health", f"{p.get('Asset_Health_Score', 1):.4f}"]
            ]
            t_sig = Table(sig_data, colWidths=[200, 200])
            t_sig.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ]))
            story.append(t_sig)
            story.append(Spacer(1, 15))
    else:
        story.append(Paragraph("No Golden Signatures established yet.", normal_style))

    story.append(PageBreak())

    # 4. Recent Batches
    story.append(Paragraph("Recent Batch History (Last 10)", heading_style))
    history = load_batch_history()
    
    if history:
        # Take last 10, reversed (newest first)
        recent = list(reversed(history))[:10]
        
        hist_data = [["Batch ID", "Mode", "Material", "Quality", "Energy"]]
        for b in recent:
            p = b.get("predicted_outcomes", {})
            hist_data.append([
                b.get("batch_id", "N/A")[:12], # Truncate long IDs slightly for table fit
                b.get("optimization_mode", "N/A"),
                b.get("material_type", "N/A"),
                f"{p.get('Quality_Score', 0):.3f}",
                f"{p.get('Energy_per_batch', 0):.1f} kWh"
            ])
            
        t_hist = Table(hist_data, colWidths=[110, 80, 110, 80, 80])
        t_hist.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#475569')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ]))
        story.append(t_hist)
    else:
        story.append(Paragraph("No batch history recorded.", normal_style))

    # Build PDF
    doc.build(story)
    
    return filepath
