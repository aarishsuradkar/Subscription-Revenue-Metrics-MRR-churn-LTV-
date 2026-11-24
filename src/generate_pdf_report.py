"""
generate_pdf_report.py
Converts PROJECT_REPORT.md into a beautifully styled PDF report using headless Google Chrome.
Embeds CSS styling for tables, typography, callouts, and charts.
"""

import os
import re
import base64
import subprocess
import markdown

def image_to_base64(img_path):
    if os.path.exists(img_path):
        with open(img_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
            return f"data:image/png;base64,{encoded}"
    return ""

def generate_pdf():
    print("Generating styled PDF from PROJECT_REPORT.md...")
    
    with open('PROJECT_REPORT.md', 'r', encoding='utf-8') as f:
        md_content = f.read()
        
    # Convert markdown to HTML with tables & code block support
    html_body = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'nl2br']
    )
    
    # Encode charts for self-contained HTML rendering
    chart_mrr = image_to_base64('output/mrr_movements_stacked.png')
    chart_cohort = image_to_base64('output/cohort_retention_heatmap.png')
    chart_churn = image_to_base64('output/churn_by_plan.png')
    
    # Visual gallery insert
    visual_gallery_html = f"""
    <div class="page-break"></div>
    <h2>Visual Analytics Gallery</h2>
    <div class="chart-container">
        <h3>1. Monthly MRR Movements (Bridge Waterfall)</h3>
        <img src="{chart_mrr}" alt="MRR Movements Waterfall" style="width: 100%; border-radius: 6px; border: 1px solid #e0e0e0;" />
        <p class="caption">Figure 1: Monthly New MRR, Expansion MRR, Contraction MRR, and Churned MRR with Net New MRR trajectory.</p>
    </div>
    
    <div class="chart-container page-break">
        <h3>2. Customer Cohort Logo Retention Heatmap</h3>
        <img src="{chart_cohort}" alt="Cohort Retention Heatmap" style="width: 100%; border-radius: 6px; border: 1px solid #e0e0e0;" />
        <p class="caption">Figure 2: Multi-tenure logo retention decay curve across acquisition cohorts (Month 0 through Month 12).</p>
    </div>
    
    <div class="chart-container page-break">
        <h3>3. Churn Hazard and Lifetime Value by Plan Tier</h3>
        <img src="{chart_churn}" alt="Plan Churn and LTV" style="width: 100%; border-radius: 6px; border: 1px solid #e0e0e0;" />
        <p class="caption">Figure 3: Plan-level logo churn rates and estimated LTV at an 80% gross margin assumption.</p>
    </div>
    """
    
    # Insert visual gallery before section 5
    if "## 5. Dual-Engine Verification" in html_body:
        html_body = html_body.replace("<h2>5. Dual-Engine Verification", visual_gallery_html + "\n<h2>5. Dual-Engine Verification")
    else:
        html_body += visual_gallery_html

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Subscription Revenue Metrics - Project Report</title>
    <style>
        @page {{
            size: A4;
            margin: 20mm 16mm 20mm 16mm;
            @bottom-right {{
                content: counter(page);
                font-size: 9pt;
                color: #888;
            }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #24292f;
            line-height: 1.6;
            font-size: 10.5pt;
        }}
        h1 {{
            color: #0f3460;
            font-size: 20pt;
            border-bottom: 2px solid #0f3460;
            padding-bottom: 6px;
            margin-top: 0;
            margin-bottom: 12px;
        }}
        h2 {{
            color: #1a365d;
            font-size: 14pt;
            border-bottom: 1px solid #e1e4e8;
            padding-bottom: 4px;
            margin-top: 22px;
            margin-bottom: 10px;
            page-break-after: avoid;
        }}
        h3 {{
            color: #2b6cb0;
            font-size: 12pt;
            margin-top: 16px;
            margin-bottom: 6px;
            page-break-after: avoid;
        }}
        blockquote {{
            background-color: #f6f8fa;
            border-left: 4px solid #f9826c;
            color: #57606a;
            padding: 8px 14px;
            margin: 12px 0;
            font-size: 9.5pt;
            border-radius: 0 4px 4px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 14px 0;
            font-size: 9.5pt;
            page-break-inside: avoid;
        }}
        th, td {{
            padding: 6px 10px;
            border: 1px solid #d0d7de;
            text-align: left;
        }}
        th {{
            background-color: #f1f4f9;
            color: #1f2328;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #fbfcfd;
        }}
        code {{
            background-color: #eff1f3;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 9pt;
        }}
        pre {{
            background-color: #f6f8fa;
            padding: 10px;
            border-radius: 6px;
            overflow-x: auto;
            border: 1px solid #d0d7de;
            font-size: 8.5pt;
            page-break-inside: avoid;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        .page-break {{
            page-break-before: always;
        }}
        .chart-container {{
            margin: 20px 0;
            text-align: center;
            page-break-inside: avoid;
        }}
        .caption {{
            font-size: 8.5pt;
            color: #666;
            font-style: italic;
            margin-top: 4px;
        }}
        ul, ol {{
            margin-top: 4px;
            margin-bottom: 10px;
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 4px;
        }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>
"""
    
    os.makedirs('output', exist_ok=True)
    html_path = os.path.abspath('output/report.html')
    pdf_path = os.path.abspath('PROJECT_REPORT.pdf')
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
        
    print(f"Generated HTML report at: {html_path}")
    
    # Path to Google Chrome
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        chrome_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
    cmd = [
        chrome_path,
        '--headless',
        '--disable-gpu',
        '--no-pdf-header-footer',
        '--run-all-compositor-stages-before-draw',
        f'--print-to-pdf={pdf_path}',
        html_path
    ]
    
    print("Printing PDF via headless browser...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1000:
        size_kb = os.path.getsize(pdf_path) / 1024
        print(f"SUCCESS: Created {pdf_path} ({size_kb:.1f} KB)")
    else:
        print(f"ERROR: Failed to generate PDF: {res.stderr}")

if __name__ == '__main__':
    generate_pdf()
