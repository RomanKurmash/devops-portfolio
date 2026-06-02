import os
import sys
import markdown
from xhtml2pdf import pisa

def convert_md_to_pdf(md_path, pdf_path):
    if not os.path.exists(md_path):
        print(f"Error: Source file {md_path} does not exist.")
        return False
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    html_content = markdown.markdown(
        md_content,
        extensions=["extra", "codehilite", "toc"]
    )
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_regular = os.path.join(script_dir, "fonts", "DejaVuSans.ttf")
    font_bold = os.path.join(script_dir, "fonts", "DejaVuSans-Bold.ttf")
    font_mono = os.path.join(script_dir, "fonts", "DejaVuSansMono.ttf")
    styled_html = f"""
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @font-face {{
            font-family: 'DejaVuSans';
            src: url('{font_regular}');
        }}
        @font-face {{
            font-family: 'DejaVuSans';
            src: url('{font_bold}');
            font-weight: bold;
        }}
        @font-face {{
            font-family: 'DejaVuSansMono';
            src: url('{font_mono}');
        }}
        @page {{
            size: A4;
            @frame header_frame {{
                -pdf-frame-content: header_content;
                left: 54pt; width: 487pt; top: 36pt; height: 30pt;
            }}
            @frame content_frame {{
                left: 54pt; width: 487pt; top: 80pt; height: 680pt;
            }}
            @frame footer_frame {{
                -pdf-frame-content: footer_content;
                left: 54pt; width: 487pt; top: 780pt; height: 30pt;
            }}
        }}
        body {{
            font-family: 'DejaVuSans', sans-serif;
            font-size: 10pt;
            line-height: 1.5;
            color: #334155;
        }}
        h1 {{
            font-family: 'DejaVuSans', sans-serif;
            font-weight: bold;
            font-size: 18pt;
            color: #1e3a8a;
            border-bottom: 2px solid #3b82f6;
            padding-bottom: 6px;
            margin-top: 10px;
            margin-bottom: 20px;
        }}
        h2 {{
            font-family: 'DejaVuSans', sans-serif;
            font-weight: bold;
            font-size: 13pt;
            color: #0f172a;
            margin-top: 25px;
            margin-bottom: 12px;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 4px;
        }}
        h3 {{
            font-family: 'DejaVuSans', sans-serif;
            font-weight: bold;
            font-size: 11pt;
            color: #2563eb;
            margin-top: 20px;
            margin-bottom: 8px;
        }}
        p {{
            margin-bottom: 12px;
            text-align: justify;
        }}
        code {{
            font-family: 'DejaVuSansMono', monospace;
            background-color: #f1f5f9;
            color: #0f172a;
            border: 0.5px solid #cbd5e1;
            padding: 1px 4px;
            font-size: 8.5pt;
        }}
        pre {{
            background-color: #f8fafc;
            border: 1px solid #cbd5e1;
            border-left: 3px solid #3b82f6;
            padding: 10px;
            margin-top: 10px;
            margin-bottom: 20px;
            display: block;
        }}
        pre code {{
            font-family: 'DejaVuSansMono', monospace;
            background-color: transparent;
            color: #0f172a;
            border: none;
            padding: 0;
            font-size: 8pt;
            line-height: 1.4;
        }}
        ul, ol {{
            margin-top: 5px;
            margin-bottom: 15px;
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 6px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #e2e8f0;
            padding: 8px 10px;
            text-align: left;
            font-size: 9pt;
        }}
        th {{
            background-color: #f8fafc;
            color: #1e293b;
            font-weight: bold;
            border-bottom: 2px solid #cbd5e1;
        }}
        tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
        hr {{
            border: none;
            border-top: 1px solid #cbd5e1;
            margin-top: 30px;
            margin-bottom: 30px;
        }}
    </style>
    </head>
    <body>
        <div id="header_content" style="text-align: right; font-size: 7.5pt; color: #64748b; border-bottom: 0.5px solid #cbd5e1; padding-bottom: 3px;">
            SecOps AI - DevOps Portfolio Documentation
        </div>
        <div id="footer_content" style="text-align: center; font-size: 8pt; color: #64748b; border-top: 0.5px solid #cbd5e1; padding-top: 3px;">
            Сторінка <pdf:pagenumber/> з <pdf:pagecount/>
        </div>
        {html_content}
    </body>
    </html>
    """
    with open(pdf_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(styled_html, dest=pdf_file)
    if pisa_status.err:
        print(f"Error occurred during PDF generation for {md_path}")
        return False
    print(f"Successfully converted {md_path} to {pdf_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        doc_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documentation")
        for filename in os.listdir(doc_dir):
            if filename.endswith(".md"):
                md_file = os.path.join(doc_dir, filename)
                pdf_file = os.path.join(doc_dir, filename[:-3] + ".pdf")
                convert_md_to_pdf(md_file, pdf_file)
    else:
        src = sys.argv[1]
        if len(sys.argv) >= 3:
            dest = sys.argv[2]
        else:
            if src.endswith(".md"):
                dest = src[:-3] + ".pdf"
            else:
                dest = src + ".pdf"
        convert_md_to_pdf(src, dest)
