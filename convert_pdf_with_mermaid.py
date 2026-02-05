
import os
import subprocess
import markdown2
import re

def create_pdf_with_mermaid(md_file, output_pdf, chrome_path):
    # 1. Read Markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 2. Transform ```mermaid code blocks to <div class="mermaid">
    # Regex to find mermaid code blocks
    pattern = r'```mermaid\s*\n(.*?)\n```'
    
    # Function to replace matched block with div
    def replacer(match):
        code = match.group(1)
        # Escape HTML entities in code just in case, though mermaid handles it usually
        return f'<div class="mermaid">\n{code}\n</div>'
    
    # Pre-process markdown to swap mermaid blocks
    md_content_processed = re.sub(pattern, replacer, md_content, flags=re.DOTALL)

    # 3. Convert remaining Markdown to HTML
    html_body = markdown2.markdown(
        md_content_processed, 
        extras=["tables", "fenced-code-blocks", "cuddled-lists", "header-ids", "break-on-newline"]
    )

    # 4. Construct Full HTML with Mermaid CDN and Styles
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Documentation</title>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        </script>
        <style>
            body {{ font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; line-height: 1.6; padding: 40px; max-width: 900px; margin: 0 auto; }}
            h1, h2, h3 {{ border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
            code {{ background-color: #f6f8fa; padding: 0.2em 0.4em; border-radius: 3px; font-family: monospace; }}
            pre {{ background-color: #f6f8fa; padding: 16px; overflow: auto; border-radius: 6px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #dfe2e5; padding: 6px 13px; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(2n) {{ background-color: #f8f8f8; }}
            blockquote {{ border-left: 4px solid #dfe2e5; color: #6a737d; padding-left: 15px; }}
            .mermaid {{ margin: 30px 0; text-align: center; }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    # 5. Save HTML temporarily
    temp_html = "temp_doc.html"
    with open(temp_html, "w", encoding='utf-8') as f:
        f.write(html_content)

    print(f"[OK] Created temporary HTML: {temp_html}")

    # 6. Convert to PDF using Chrome Headless
    # --virtual-time-budget=5000 is important to allow JS (Mermaid) to render
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--print-to-pdf=" + output_pdf,
        "--no-pdf-header-footer",
        "--virtual-time-budget=5000", 
        os.path.abspath(temp_html)
    ]

    print(f"[...] Running Chrome conversion...")
    try:
        subprocess.run(cmd, check=True, shell=True)
        print(f"[OK] PDF created successfully: {output_pdf}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Chrome failed: {e}")
    
    # Cleanup
    # os.remove(temp_html)

if __name__ == "__main__":
    md_file = r"C:\Users\vijju\.gemini\antigravity\brain\94eb751d-279f-469d-a121-10d12609077f\github_env_variables_explained.md"
    pdf_file = r"C:\Users\vijju\Desktop\V-project\Ai_reviewer\github_env_variables_explained.pdf"
    chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    if not os.path.exists(chrome):
        print("Chrome not found at expected path")
    else:
        create_pdf_with_mermaid(md_file, pdf_file, chrome)
