import os
import re
import subprocess
from pathlib import Path
from scholarly import scholarly  # Install with `pip install scholarly`

# Directories
LITERATURE_DIR = "literature/"
REVIEW_FILE = os.path.join(LITERATURE_DIR, "literature-review.md")
BIBTEX_FILE = "paper/references.bib"

# Helper Functions
def convert_pdf_to_text(pdf_path):
    txt_path = pdf_path.with_suffix('.txt')
    subprocess.run(['pdftotext', str(pdf_path), str(txt_path)])
    return txt_path

def extract_metadata(text):
    # Placeholder for metadata extraction logic
    title = "Extracted Title"
    authors = "Extracted Authors"
    year = "Extracted Year"
    return title, authors, year

def summarize_text(text):
    # Placeholder for summarization logic
    summary = "Summarized main contribution."
    methodology = "Summarized methodology."
    results = "Summarized results."
    return summary, methodology, results

def create_markdown_entry(title, authors, year, summary, methodology, results):
    return f"""## {title} ({year})
**Authors**: {authors}

**Google Scholar**: [Link to Google Scholar search with article title]

**Summary**: {summary}

**Methodology**: {methodology}

**Results**: {results}

**Evaluation**: 4/5 – Placeholder evaluation.

**Resources**:
- LaTeX Source: [arXiv source link]
- Code: [repository link]
- Data: [dataset link]
- Project: [website link]
---
"""

def create_bibtex_entry(title, authors, year):
    citation_key = f"{authors.split()[0].lower()}{year}keyword"
    return f"""@article{{{citation_key},
  author = {{{authors}}},
  title = {{\\href{{https://scholar.google.com/scholar?q={title}}}{{{title}}}}},
  year = {{{year}}}
}}
"""

# Main Workflow
def process_pdfs():
    for pdf_file in Path(LITERATURE_DIR).glob("*.pdf"):
        txt_file = convert_pdf_to_text(pdf_file)
        with open(txt_file, 'r') as f:
            text = f.read()
        
        title, authors, year = extract_metadata(text)
        summary, methodology, results = summarize_text(text)
        
        # Update Markdown
        markdown_entry = create_markdown_entry(title, authors, year, summary, methodology, results)
        with open(REVIEW_FILE, 'a') as f:
            f.write(markdown_entry)
        
        # Update BibTeX
        bibtex_entry = create_bibtex_entry(title, authors, year)
        with open(BIBTEX_FILE, 'a') as f:
            f.write(bibtex_entry + "\n")

if __name__ == "__main__":
    process_pdfs()