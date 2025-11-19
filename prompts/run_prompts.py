#!/usr/bin/env python3
"""
Run prompt workflows found in the prompts/ folder.

Behavior:
- For each `*.prompt.md` file, parse frontmatter and use it as instructions.
- For the `literature_review_agent` workflow: convert PDFs in `literature/` to text
  (using pdftotext if available, else PyPDF2), then either call OpenAI (if
  OPENAI_API_KEY is set and `openai` is installed) to generate structured
  summaries, or create placeholder entries.
- Save a structured JSON output per run under `prompts/outputs/`.

Usage:
  python3 prompts/run_prompts.py

Notes:
- To enable LLM summarization, set the environment variable OPENAI_API_KEY
  and install `openai` (pip install openai).
- This script is conservative: it doesn't modify `paper/references.bib` or
  `literature/literature-review.md` automatically unless run with --apply.
"""

import os
import sys
import json
import glob
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = ROOT / "prompts"
LITERATURE_DIR = ROOT / "literature"
OUTPUTS_DIR = PROMPTS_DIR / "outputs"

# Simple frontmatter extractor for prompt files

def read_prompt_file(path: Path):
    text = path.read_text(encoding="utf-8")
    return text


def pdftotext_available():
    try:
        subprocess.run(["pdftotext", "-v"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Try pdftotext first, else fall back to PyPDF2 if available."""
    txt_path = pdf_path.with_suffix('.txt')
    if pdftotext_available():
        try:
            subprocess.run(["pdftotext", str(pdf_path), str(txt_path)], check=True)
            return txt_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            print(f"pdftotext failed for {pdf_path}: {e}")
    # Fallback to PyPDF2
    try:
        import PyPDF2
        text_parts = []
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for p in reader.pages:
                try:
                    text_parts.append(p.extract_text() or "")
                except Exception:
                    pass
        text = "\n\n".join(text_parts)
        # write text file for reference
        try:
            txt_path.write_text(text, encoding='utf-8')
        except Exception:
            pass
        return text
    except Exception:
        print("No suitable PDF parser available (pdftotext or PyPDF2). Install pdftotext or PyPDF2 to extract text.")
        return ""


def truncate_text(s: str, max_chars: int = 30000) -> str:
    return s if len(s) <= max_chars else s[:max_chars] + "\n\n...[truncated]"


def call_openai_chat(system_prompt: str, user_prompt: str, max_tokens=800):
    try:
        import openai
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        if not openai.api_key:
            print("OPENAI_API_KEY not set; skipping OpenAI call.")
            return None
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini" if False else "gpt-4o" if False else "gpt-4o-mini-preview" if False else "gpt-4o-mini" ,
            messages=[
                {"role":"system","content":system_prompt},
                {"role":"user","content":user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return resp
    except Exception as e:
        print(f"OpenAI call failed: {e}")
        return None


def generate_structured_summary(prompt_text: str, pdf_text: str, use_openai: bool):
    system = "You are an assistant that extracts structured metadata and concise summaries from academic papers."
    user = (
        "The workflow instructions are:\n\n" + prompt_text + "\n\n"
        + "The paper text (extracted) is below. Produce a JSON object with keys:\n"
        + "title, authors, year, summary (2 sentences), methodology (2 sentences), results (1 sentence), evaluation (1-5), resources (list).\n"
        + "If data is not available, use an empty string or reasonable placeholder.\n\n"
        + "Paper text:\n\n" + truncate_text(pdf_text, max_chars=20000)
    )

    if use_openai:
        resp = call_openai_chat(system, user)
        if resp and 'choices' in resp and len(resp.choices) > 0:
            content = resp.choices[0].message['content']
            # Try to parse JSON from the content
            try:
                parsed = json.loads(content)
                return parsed, content
            except Exception:
                # Return raw content in a wrapper
                return None, content
        else:
            return None, None
    else:
        # Create a placeholder structured object with basic extraction heuristics
        lines = pdf_text.splitlines()
        first_non_empty = next((l.strip() for l in lines if l.strip()), "")
        title_guess = first_non_empty[:200]
        structured = {
            "title": title_guess,
            "authors": "",
            "year": "",
            "summary": "[PLACEHOLDER] Short summary not generated because OPENAI_API_KEY is not set.",
            "methodology": "[PLACEHOLDER]",
            "results": "[PLACEHOLDER]",
            "evaluation": "3/5 - Not evaluated automatically.",
            "resources": []
        }
        raw_text = json.dumps(structured, ensure_ascii=False, indent=2)
        return structured, raw_text


def run_literature_review_workflow(prompt_path: Path):
    prompt_text = read_prompt_file(prompt_path)
    pdf_paths = sorted(LITERATURE_DIR.glob('*.pdf'))
    if not pdf_paths:
        print(f"No PDF files found in {LITERATURE_DIR}. Nothing to do.")
        return

    use_openai = bool(os.environ.get('OPENAI_API_KEY'))
    outputs = []
    for pdf in pdf_paths:
        print(f"Processing {pdf.name}...")
        txt = extract_text_from_pdf(pdf)
        if not txt:
            print(f"Warning: no text extracted from {pdf.name}; skipping structured summary.")
            continue
        structured, raw = generate_structured_summary(prompt_text, txt, use_openai=use_openai)
        out = {
            "pdf": str(pdf.relative_to(ROOT)),
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "structured": structured,
            "raw": raw
        }
        outputs.append(out)

    # Write outputs
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUTS_DIR / (prompt_path.stem + "_output.json")
    out_file.write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Wrote structured output to {out_file}")
    print("Done.")


def main():
    prompt_files = sorted(PROMPTS_DIR.glob('*.prompt.md'))
    if not prompt_files:
        print("No prompt files found in prompts/.")
        return
    for p in prompt_files:
        print(f"Running prompt workflow for {p.name}")
        # currently only supports literature_review_agent by design
        content = read_prompt_file(p)
        if 'type: literature_review_agent' in content:
            run_literature_review_workflow(p)
        else:
            print(f"Unknown or unsupported prompt type in {p.name}; skipping.")

if __name__ == '__main__':
    main()
