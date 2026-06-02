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
        @page {{
            size: A4;
            margin: 2cm;
        }}
        body {{
            font-family: 'DejaVuSans', sans-serif;
            font-size: 10pt;
            line-height: 1.5;
            color: #333333;
        }}
        h1 {{
            font-family: 'DejaVuSans', sans-serif;
            font-weight: bold;
            font-size: 18pt;
            color: #1e3a8a;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 5px;
            margin-top: 20px;
            margin-bottom: 20px;
        }}
        h2 {{
            font-family: 'DejaVuSans', sans-serif;
            font-weight: bold;
            font-size: 14pt;
            color: #2563eb;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        h3 {{
            font-family: 'DejaVuSans', sans-serif;
            font-weight: bold;
            font-size: 12pt;
            color: #3b82f6;
            margin-top: 15px;
            margin-bottom: 5px;
        }}
        p {{
            margin-bottom: 10px;
        }}
        code {{
            font-family: monospace;
            background-color: #f3f4f6;
            padding: 2px 4px;
            font-size: 9pt;
        }}
        pre {{
            background-color: #f3f4f6;
            border: 1px solid #e5e7eb;
            padding: 10px;
            margin-bottom: 15px;
            display: block;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        ul, ol {{
            margin-top: 5px;
            margin-bottom: 10px;
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }}
        th, td {{
            border: 1px solid #d1d5db;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f3f4f6;
            font-weight: bold;
        }}
    </style>
    </head>
    <body>
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
