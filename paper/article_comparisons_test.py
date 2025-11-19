#!/usr/bin/env python3
"""
Lightweight non-interactive test for talk-page sentiment/toxicity analysis.

Saves results to `paper/article_comparisons_test_output.json`.

Uses smaller models to keep downloads reasonable:
- sentiment: distilbert-base-uncased-finetuned-sst-2-english
- toxicity: unitary/toxic-bert (may still download ~200MB)

This script is intended for quick validation; it doesn't show plots.
"""
import requests
import re
import json
from collections import Counter
from pathlib import Path

# Try to import transformers. If missing, script will raise and user can install deps.
from transformers import pipeline

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'paper' / 'article_comparisons_test_output.json'
LITERATURE_DIR = ROOT / 'literature'

TOPICS = [
    "Donald Trump",
    "Antisemitism",
    "Capitalism",
    "Social Issues",
    "Atheism",
    "British National Party",
    "Feminism",
    "Gentrification",
]

endpoint = "https://en.wikipedia.org/w/api.php"
headers = {"User-Agent": "CarolinaBot/1.0 (https://example.com)"}


def fetch_talk_page_content(topic):
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": f"Talk:{topic}",
        "rvprop": "content",
        "rvslots": "main"
    }
    r = requests.get(endpoint, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    data = r.json()
    page = list(data["query"]["pages"].values())[0]
    if "revisions" not in page:
        return None
    return page["revisions"][0]["slots"]["main"]["*"]


def extract_comments(content):
    # Very simple splitter by signature timestamps (common on talk pages)
    comment_pattern = re.compile(r"(.*?)(--.*?\d{2}:\d{2},.*?\(UTC\))", re.DOTALL)
    matches = comment_pattern.findall(content)
    comments = [m[0].strip() for m in matches if m[0].strip()]
    # fallback: split by lines if no matches
    if not comments:
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
        return lines[:200]  # limit
    return comments[:200]


def categorize_score(score):
    if score < 0.5:
        return "Low"
    elif score < 0.75:
        return "Medium"
    else:
        return "High"


def classify_long_text(pipeline_model, text, chunk_size=300):
    words = text.split()
    if not words:
        return {"label": "NEUTRAL", "score": 0.0}
    results = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        try:
            res = pipeline_model(chunk, truncation=True)
        except Exception as e:
            # some models return a list, others dict
            res = pipeline_model(chunk)
        if isinstance(res, list):
            r = res[0]
        else:
            r = res
        results.append(r)
    # pick the highest-score result
    best = max(results, key=lambda r: r.get('score', 0.0))
    return best


def run_test():
    print("Loading models (may download weights)...")
    sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    toxicity_model = pipeline("text-classification", model="unitary/toxic-bert")

    results = {}
    for topic in TOPICS:
        print(f"Processing Talk:{topic} ...")
        try:
            content = fetch_talk_page_content(topic)
        except Exception as e:
            print(f"Failed to fetch {topic}: {e}")
            continue
        if not content:
            print(f"No talk page content for {topic}")
            continue
        comments = extract_comments(content)
        print(f"Extracted {len(comments)} comments (limited).")

        sent_labels = []
        sent_conf_levels = []
        tox_conf_levels = []

        for c in comments:
            s = classify_long_text(sentiment_model, c)
            t = classify_long_text(toxicity_model, c)
            # Normalize sentiment labels to Positive/Negative/Neutral
            lab = s.get('label', '')
            if lab.lower().startswith('pos'):
                labn = 'Positive'
            elif lab.lower().startswith('neg'):
                labn = 'Negative'
            else:
                labn = 'Neutral'
            sent_labels.append(labn)
            sent_conf_levels.append(categorize_score(s.get('score', 0.0)))
            tox_conf_levels.append(categorize_score(t.get('score', 0.0)))

        results[topic] = {
            'num_comments': len(comments),
            'sentiment_label_dist': dict(Counter(sent_labels)),
            'sentiment_conf_dist': dict(Counter(sent_conf_levels)),
            'toxicity_conf_dist': dict(Counter(tox_conf_levels)),
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f"Wrote results to {OUTPUT}")


if __name__ == '__main__':
    run_test()
