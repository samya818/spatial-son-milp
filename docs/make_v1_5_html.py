import markdown
from pathlib import Path

md_path = Path("docs/WiseNet_V1_5_Scientific_Report.md")
html_path = Path("docs/WiseNet_V1_5_Scientific_Report.html")

md_text = md_path.read_text(encoding="utf-8")
html_body = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>WiseNet V1.5 Scientific Report</title>
<style>
@page {{ size: A4; margin: 20mm 15mm 20mm 15mm; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1a1a1a; max-width: 900px; margin: 0 auto; padding: 25px; background: #fafafa; }}
.container {{ background: #ffffff; padding: 40px; border: 1px solid #e1e4e8; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
h1 {{ color: #0d233a; border-bottom: 2px solid #2b5c8f; padding-bottom: 8px; font-size: 24px; }}
h2 {{ color: #1b3d63; border-bottom: 1px solid #eaecef; padding-bottom: 6px; margin-top: 28px; font-size: 19px; }}
h3 {{ color: #2c3e50; margin-top: 18px; font-size: 15px; }}
table {{ width: 100%; border-collapse: collapse; margin: 18px 0; font-size: 13.5px; }}
th, td {{ border: 1px solid #d1d5db; padding: 9px 12px; text-align: left; }}
th {{ background-color: #f3f4f6; color: #111827; font-weight: 600; }}
tr:nth-child(even) {{ background-color: #f9fafb; }}
pre {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; overflow-x: auto; font-family: Consolas, monospace; font-size: 13px; color: #0f172a; }}
code {{ font-family: Consolas, monospace; background-color: #f1f5f9; padding: 2px 5px; border-radius: 4px; font-size: 13px; }}
.print-btn {{ position: fixed; top: 20px; right: 20px; background: #2563eb; color: #fff; padding: 10px 18px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }}
.print-btn:hover {{ background: #1d4ed8; }}
@media print {{ body {{ background: #fff; padding: 0; }} .container {{ border: none; box-shadow: none; padding: 0; }} .print-btn {{ display: none; }} }}
</style>
</head>
<body>
<button class="print-btn" onclick="window.print()">Print to PDF</button>
<div class="container">
{html_body}
</div>
</body>
</html>"""

html_path.write_text(html_doc, encoding="utf-8")
print(f"HTML report successfully created at: {html_path.resolve()}")
