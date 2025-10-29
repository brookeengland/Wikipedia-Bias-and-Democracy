---

type: literature\_review\_agent version: 1.0 author: Brooke England and Carolina Caraballo Vélez created: 2025-10-28 description: >- Customized AI agent workflow for automating the literature review process in the **Wikipedia, Bias, and Democracy** research project. This workflow is tailored to extract, summarize, and catalog academic works on bias detection, talk page dynamics, and democratic participation within Wikipedia. prerequisites:

- PDF research papers stored in the `literature/` directory
- Command-line access to `pdftotext` or equivalent Python parser (e.g., PyPDF2)
- Basic knowledge of Markdown and BibTeX structure
- Access to academic databases (Google Scholar, Semantic Scholar)
- Seed papers: Hube (2017), Klemp & Forcehimes (2010), Wikimedia Research Reports

---

# Overview

This workflow automates a structured literature review for the **Wikipedia, Bias, and Democracy** project. It instructs an AI agent to extract, summarize, and format findings from PDF research papers that explore topics including:

- Political or systemic bias in Wikipedia content
- Talk page discussions, editor civility, and toxicity
- The influence of Wikipedia on democratic engagement and civic participation

The process ensures that all reviewed literature is consistently documented, citable, and useful for further analysis in this research domain.

# Input

- All PDF files in the `literature/` folder
- Each PDF should be an academic paper relevant to Wikipedia, online bias, talk pages, or democratic participation

# Output

The AI agent will create or update the following files:

- `literature/literature-review.md`: structured Markdown summaries of all reviewed articles
- `paper/references.bib`: BibTeX entries for all articles, alphabetized and formatted for use in LaTeX or Overleaf

# Instructions

For each **new** PDF file in the `literature/` folder:

1. **Convert PDF to text**

   - Use `pdftotext name.pdf name.txt` or a Python script for conversion
   - Save the text file in the same directory for reference

2. **Extract Key Information**

   - Identify and record the following fields:
     - **Title** and **Authors**
     - **Main Contribution (2 sentences):** central argument or innovation
     - **Methodology (2 sentences):** type of study (e.g., quantitative/qualitative), data sources (e.g., Wikipedia dumps, talk pages, ORES), and analysis methods (e.g., NLP, Random Forest, sentiment analysis)
     - **Results (1 sentence):** main findings or conclusions
     - **Evaluation (1–5 rating):** assign an overall quality score and justify it in one sentence
   - Append a new entry to `literature/literature-review.md` in the format below

3. **Add Resource Links**

   - Create a Google Scholar link using the article title
   - Add additional resources when available:
     - arXiv LaTeX source
     - Code repositories (GitHub, GitLab)
     - Datasets or supplementary materials
     - Project websites or Wikimedia pages

4. **Create or Update BibTeX Entry**

   - Use the correct BibTeX type (`@article`, `@inproceedings`, `@book`, etc.)
   - Include only essential metadata: `author`, `title`, `year`, `journal` or `booktitle`, `publisher`
   - Exclude non-essential fields (doi, url, pages, etc.)
   - Make the title clickable using:
     ```bibtex
     title = {\href{https://scholar.google.com/scholar?q=TITLE}{TITLE}}
     ```
   - Follow citation key format: `firstauthorlastnameYEARkeyword`
   - Maintain alphabetical order by citation key

# Constraints

- Summaries must be concise (exactly 2 sentences each for Summary and Methodology)
- Only process new articles (skip if already summarized)
- Preserve and append to existing files
- Maintain alphabetical and chronological consistency
- Ensure valid Markdown rendering and proper link formatting

# Expected Output Format

```markdown
## [Article Title] (Year)
**Authors**: [Author names]

**Google Scholar**: [Link to Google Scholar search with article title]

**Summary**: [2-sentence overview of contribution]

**Methodology**: [2-sentence summary of data, methods, and analysis]

**Results**: [1-sentence summary of findings]

**Evaluation**: [Rating 1–5]/5 – [1-sentence justification]

**Resources**:
- LaTeX Source: [arXiv source link]
- Code: [repository link]
- Data: [dataset link]
- Project: [website link]
---
```

# Verification

After the workflow runs, verify that:

- Each PDF in `literature/` has a corresponding `.txt` file
- Each article entry in `literature-review.md` contains all required fields
- Markdown formatting renders correctly
- Each article has a valid clickable Google Scholar link
- Each reference exists in `paper/references.bib` and follows naming and formatting rules
- The summary set represents a balance of papers covering bias, talk pages, and democratic participation

# Learning Objectives

By completing this workflow, students and researchers will learn to:

- Automate literature analysis and documentation with reproducible workflows
- Apply consistent metadata extraction and structured summarization
- Integrate data-driven academic organization methods into collaborative research
- Enhance transparency and traceability of AI-assisted literature review processes

