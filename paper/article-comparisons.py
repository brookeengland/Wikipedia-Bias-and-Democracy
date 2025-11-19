import requests
import re
from transformers import pipeline
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
import argparse
import json
from pathlib import Path

# root path
ROOT = Path(__file__).resolve().parents[1]

# ===================================
# Helper: non-interactive runner
# ===================================
def process_topics(topics, save_fig=True, show_fig=False, fig_path=None, results_path=None, max_comments=100):
    """Run the analysis for a list of topics and save plots and JSON results.

    Args:
        topics (list[str]): list of Wikipedia talk page topics (page titles without 'Talk:').
        save_fig (bool): whether to save the comparative figure instead of showing it.
        fig_path (Path|str): path to save the figure PNG.
        results_path (Path|str): path to save JSON summary of counts.
        max_comments (int): limit comments extracted per talk page.
    Returns:
        dict: aggregated results per topic.
    """
    endpoint = "https://en.wikipedia.org/w/api.php"
    headers = {"User-Agent": "CarolinaBot/1.0 (https://example.com)"}

    # Load models (kept the original choices)
    print("Loading models (this may take a bit)...")
    sentiment_model = pipeline("sentiment-analysis", model="tabularisai/multilingual-sentiment-analysis")
    toxicity_model = pipeline("text-classification", model="unitary/toxic-bert")

    # reuse helper functions from original script scope
    # create a requests.Session with retry/backoff to be more resilient to network blips
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=frozenset(["GET"]))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    def fetch_talk_page_content(topic):
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": f"Talk:{topic}",
            "rvprop": "content",
            "rvslots": "main"
        }
        try:
            response = session.get(endpoint, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            page = list(data["query"]["pages"].values())[0]
            if "revisions" not in page:
                print(f"⚠️ No content found for Talk:{topic}")
                return None
            return page["revisions"][0]["slots"]["main"]["*"]
        except Exception as e:
            print(f"Error fetching Talk:{topic} — {type(e).__name__}: {e}")
            return None

    def extract_comments(content, limit=max_comments):
        comment_pattern = re.compile(r"(.*?)(--.*?\d{2}:\d{2},.*?\(UTC\))", re.DOTALL)
        matches = comment_pattern.findall(content)
        comments = [m[0].strip() for m in matches if m[0].strip()]
        if not comments:
            lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
            return lines[:limit]
        return comments[:limit]

    def classify_long_text(pipeline_model, text, max_length=512):
        words = text.split()
        results = []
        for i in range(0, len(words), max_length):
            chunk = " ".join(words[i:i+max_length])
            result = pipeline_model(chunk, truncation=True, max_length=max_length)[0]
            results.append(result)
        return max(results, key=lambda r: r["score"]) if results else {"label":"","score":0.0}

    def categorize_score(score):
        if score < 0.5:
            return "Low"
        elif score < 0.75:
            return "Medium"
        else:
            return "High"

    topic_results = {}

    for topic in topics:
        print(f"\n=== Processing Talk:{topic} ===")
        content = fetch_talk_page_content(topic)
        if not content:
            continue

        comments = extract_comments(content)
        print(f"Extracted {len(comments)} comments.\n")

        sentiment_labels, sentiment_confidences, toxicity_conf_levels = [], [], []

        for comment in comments:
            sentiment = classify_long_text(sentiment_model, comment)
            toxicity = classify_long_text(toxicity_model, comment)

            sentiment_labels.append(sentiment.get("label", ""))
            sentiment_confidences.append(categorize_score(sentiment.get("score", 0.0)))
            toxicity_conf_levels.append(categorize_score(toxicity.get("score", 0.0)))

        topic_results[topic] = {
            "sentiment_label_dist": Counter(sentiment_labels),
            "sentiment_conf_dist": Counter(sentiment_confidences),
            "toxicity_conf_dist": Counter(toxicity_conf_levels),
            "num_comments": len(comments),
        }

    # Plotting (similar to original) but save to file if requested
    if topic_results:
        topics_list = list(topic_results.keys())
        num_topics = len(topics_list)
        width = 0.2
        x = np.arange(num_topics)

        fig, axs = plt.subplots(1, 4, figsize=(28, 6))
        labels = ["Positive", "Neutral", "Negative"]
        colors = ["#7FC97F", "#BEAED4", "#FDC086"]
        for i, label in enumerate(labels):
            counts = [topic_results[t]["sentiment_label_dist"].get(label, 0) for t in topics_list]
            axs[0].bar(x + (i - 1)*width, counts, width, label=label, color=colors[i])
        axs[0].set_title("Sentiment Labels")
        axs[0].set_xticks(x)
        axs[0].set_xticklabels(topics_list, rotation=15)
        axs[0].set_ylabel("Number of Comments")
        axs[0].legend()

        levels = ["Low", "Medium", "High"]
        colors_levels = ["#D9D9D9", "#A6CEE3", "#1F78B4"]
        for i, level in enumerate(levels):
            counts = [topic_results[t]["sentiment_conf_dist"].get(level, 0) for t in topics_list]
            axs[1].bar(x + (i - 1)*width, counts, width, label=level, color=colors_levels[i])
        axs[1].set_title("Sentiment Confidence")
        axs[1].set_xticks(x)
        axs[1].set_xticklabels(topics_list, rotation=15)
        axs[1].legend()

        for i, level in enumerate(levels):
            counts = [topic_results[t]["toxicity_conf_dist"].get(level, 0) for t in topics_list]
            axs[2].bar(x + (i - 1)*width, counts, width, label=level, color=colors_levels[i])
        axs[2].set_title("Toxicity Levels (Low/Med/High)")
        axs[2].set_xticks(x)
        axs[2].set_xticklabels(topics_list, rotation=15)
        axs[2].legend()

        bottom = np.zeros(num_topics)
        for i, label in enumerate(labels):
            counts = np.array([topic_results[t]["sentiment_label_dist"].get(label, 0) for t in topics_list])
            topic_totals = np.array([sum(topic_results[t]["sentiment_label_dist"].values()) for t in topics_list])
            perc = np.divide(counts, topic_totals, out=np.zeros_like(counts, dtype=float), where=topic_totals!=0) * 100
            axs[3].bar(x, perc, bottom=bottom, label=label, color=colors[i])
            bottom += perc
        axs[3].set_title("Sentiment Labels (Stacked %)")
        axs[3].set_xticks(x)
        axs[3].set_xticklabels(topics_list, rotation=15)
        axs[3].set_ylabel("Percentage (%)")
        axs[3].legend()

        plt.tight_layout()
        if save_fig:
            fig_path = Path(fig_path or (ROOT / 'figures' / 'article_comparisons.png'))
            fig_path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(fig_path)
            print(f"Saved figure to {fig_path}")
            if show_fig:
                # Try to display interactively; if that fails (headless), open the image with the OS
                try:
                    plt.show()
                except Exception as e:
                    import subprocess
                    try:
                        subprocess.run(["open", str(fig_path)], check=False)
                    except Exception:
                        print(f"Could not display figure interactively: {e}")
        else:
            plt.show()

    # Save results JSON if requested
    if results_path:
        rp = Path(results_path)
        rp.parent.mkdir(parents=True, exist_ok=True)
        # convert Counters to dicts
        serializable = {t: {k: (v if not isinstance(v, Counter) else dict(v)) for k, v in topic_results[t].items()} for t in topic_results}
        rp.write_text(json.dumps(serializable, indent=2), encoding='utf-8')
        print(f"Wrote JSON results to {rp}")

    return topic_results


def _default_topic_sets():
    # default topic list (from user request) and some example subsets
    default = [
        "Donald Trump",
        "Antisemitism",
        "Capitalism",
        "Social Issues",
        "Atheism",
        "British National Party",
        "Feminism",
        "Gentrification",
    ]
    subsets = {
        "default": default,
        "political": ["Donald Trump", "British National Party", "Capitalism"],
        "social": ["Feminism", "Gentrification", "Atheism"],
        "extremes": ["British National Party", "Antisemitism"],
    }
    return subsets


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run article comparisons non-interactively.')
    parser.add_argument('--topics', type=str, help='Comma-separated list of topics to analyze')
    parser.add_argument('--subset', type=str, help='Run one of the predefined subsets (default, political, social, extremes)')
    parser.add_argument('--run-all-subsets', action='store_true', help='Run all predefined subsets')
    parser.add_argument('--fig-dir', type=str, default=str(ROOT / 'figures'), help='Directory to save figures')
    parser.add_argument('--results', type=str, default=str(ROOT / 'paper' / 'article_comparisons_results.json'), help='JSON file to write aggregated results')
    args = parser.parse_args()

    subsets = _default_topic_sets()
    runs = []
    if args.topics:
        topics_list = [t.strip() for t in args.topics.split(',') if t.strip()]
        runs.append(('custom', topics_list))
    elif args.subset:
        key = args.subset
        if key in subsets:
            runs.append((key, subsets[key]))
        else:
            print(f"Unknown subset '{key}'. Available: {list(subsets.keys())}")
            raise SystemExit(1)
    elif args.run_all_subsets:
        for k, v in subsets.items():
            runs.append((k, v))
    else:
        # default single run
        runs.append(('default', subsets['default']))

    all_results = {}
    for name, tlist in runs:
        print(f"Running subset '{name}' with topics: {tlist}")
        fig_path = Path(args.fig_dir) / f"article_comparisons_{name}.png"
        res_path = Path(args.results).with_suffix(f'.{name}.json')
        r = process_topics(tlist, save_fig=True, fig_path=fig_path, results_path=res_path)
        all_results[name] = r

    # write a combined results file
    outp = Path(args.results)
    outp.parent.mkdir(parents=True, exist_ok=True)
    serializable = {s: {t: {k: (v if not isinstance(v, Counter) else dict(v)) for k, v in all_results[s][t].items()} for t in all_results[s]} for s in all_results}
    outp.write_text(json.dumps(serializable, indent=2), encoding='utf-8')
    print(f"Wrote combined results to {outp}")

# End of file (original interactive flow removed; use CLI entrypoint instead)