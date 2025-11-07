# utils/report_generation.py
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from pathlib import Path
from datetime import datetime
from utils.paths import REPORTS_DIR, PLOTS_DIR
import os

def generate_report_with_plots(metrics: dict, filename=None):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if filename is None:
        filename = f"netsentry_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path = REPORTS_DIR / filename

    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("NetSentry - Anomaly Detection Report", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Model Metrics:", styles['Heading2']))
    for k, v in metrics.items():
        story.append(Paragraph(f"<b>{k}:</b> {v}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Plots to include (look in PLOTS_DIR)
    plots = [
        ("rf_confusion.png", "Confusion Matrix"),
        ("rf_fi.png", "Feature Importance"),
        ("rf_roc.png", "ROC Curve")
    ]
    for fname, caption in plots:
        p = PLOTS_DIR / fname
        if p.exists():
            try:
                story.append(Paragraph(caption, styles['Heading3']))
                img = Image(str(p), width=6*inch, height=3*inch)
                story.append(img)
                story.append(Spacer(1, 12))
            except Exception:
                pass

    story.append(Paragraph("Notes:", styles['Heading3']))
    story.append(Paragraph("- This report shows model evaluation and plots generated on the dataset.", styles['Normal']))
    story.append(Paragraph("- For realistic evaluation, use a held-out test set or real network data.", styles['Normal']))
    doc.build(story)
    return str(path)
