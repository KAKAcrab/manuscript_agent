#!/usr/bin/env python3
"""
CrossRef validation tool for verifying literature authenticity.
"""

import argparse
import concurrent.futures
import json
from pathlib import Path
from typing import Dict, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from builtins import print as builtin_print

DEBUG = False

def debug_print(*args, **kwargs):
    if DEBUG:
        builtin_print(*args, **kwargs)

def info(*args, **kwargs):
    builtin_print(*args, **kwargs)

print = debug_print

CROSSREF_API = "https://api.crossref.org/works"


def create_session() -> requests.Session:
    sess = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods={"GET"},
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=16)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    sess.headers.update({"User-Agent": "managing-literature/1.0"})
    return sess

def validate_paper(doi: str, paper_data: Dict, session: requests.Session) -> Dict:
    """
    Validate paper via CrossRef API and return validation score.

    Args:
        doi: DOI to validate
        paper_data: Paper metadata to compare against CrossRef

    Returns:
        Dictionary with validation_score (0.0-1.0) and validated flag
    """
    if not doi:
        return {"validation_score": 0.0, "validated": False, "reason": "No DOI provided"}

    try:
        # Query CrossRef API
        response = session.get(f"{CROSSREF_API}/{doi}", timeout=20)

        if response.status_code != 200:
            return {"validation_score": 0.0, "validated": False, "reason": f"CrossRef returned {response.status_code}"}

        crossref_data = response.json()
        message = crossref_data.get("message", {})

        # Calculate validation score based on field matching
        score_components = []

        # 1. Title matching (40% weight)
        title_score = compare_titles(
            paper_data.get("title", ""),
            " ".join(message.get("title", []))
        )
        score_components.append(("title", title_score, 0.4))

        # 2. Year matching (20% weight)
        paper_year = paper_data.get("year", 0)
        crossref_year = extract_year(message)
        year_score = 1.0 if paper_year == crossref_year else 0.0
        score_components.append(("year", year_score, 0.2))

        # 3. Author matching (30% weight)
        author_score = compare_authors(
            paper_data.get("authors", []),
            message.get("author", [])
        )
        score_components.append(("authors", author_score, 0.3))

        # 4. Journal matching (10% weight)
        journal_score = compare_journals(
            paper_data.get("journal", ""),
            message.get("container-title", [""])[0]
        )
        score_components.append(("journal", journal_score, 0.1))

        # Calculate weighted total score
        total_score = sum(score * weight for _, score, weight in score_components)

        # Validated if score >= 0.6
        validated = total_score >= 0.6

        # Extract ISSN information for WOS API queries
        issn_list = message.get("ISSN", [])
        issn_type_list = message.get("issn-type", [])

        # Organize ISSN by type (print/electronic)
        issn_info = {}
        for issn_type in issn_type_list:
            if issn_type.get("type") == "print":
                issn_info["issn"] = issn_type.get("value")
            elif issn_type.get("type") == "electronic":
                issn_info["eissn"] = issn_type.get("value")

        # Fallback: if no typed ISSN, use first two from list
        if not issn_info and issn_list:
            issn_info["issn"] = issn_list[0] if len(issn_list) > 0 else None
            issn_info["eissn"] = issn_list[1] if len(issn_list) > 1 else issn_list[0]

        return {
            "validation_score": round(total_score, 3),
            "validated": validated,
            "score_breakdown": {name: round(score, 2) for name, score, _ in score_components},
            "crossref_data": {
                "title": " ".join(message.get("title", [])),
                "year": crossref_year,
                "journal": message.get("container-title", [""])[0],
                "authors": len(message.get("author", [])),
                "issn": issn_info.get("issn"),
                "eissn": issn_info.get("eissn")
            }
        }

    except requests.RequestException as e:
        return {"validation_score": 0.0, "validated": False, "reason": f"API error: {e}"}
    except Exception as e:
        return {"validation_score": 0.0, "validated": False, "reason": f"Validation error: {e}"}

def compare_titles(title1: str, title2: str) -> float:
    """Compare two titles and return similarity score (0.0-1.0)."""
    if not title1 or not title2:
        return 0.0

    # Normalize titles (lowercase, remove punctuation)
    import re
    normalize = lambda t: re.sub(r'[^\w\s]', '', t.lower()).strip()

    t1 = normalize(title1)
    t2 = normalize(title2)

    if t1 == t2:
        return 1.0

    # Simple word overlap similarity
    words1 = set(t1.split())
    words2 = set(t2.split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2

    return len(intersection) / len(union)

def extract_year(crossref_message: Dict) -> int:
    """Extract publication year from CrossRef message."""
    # Try published-print first, then published-online
    for date_type in ["published-print", "published-online", "created"]:
        date_parts = crossref_message.get(date_type, {}).get("date-parts", [[]])
        if date_parts and date_parts[0]:
            return int(date_parts[0][0])
    return 0

def compare_authors(authors1: List, authors2: List) -> float:
    """Compare author lists and return similarity score."""
    if not authors1 or not authors2:
        return 0.0

    # Normalize author names
    def normalize_author(author):
        if isinstance(author, str):
            return author.lower().strip()
        elif isinstance(author, dict):
            family = author.get("family", "")
            given = author.get("given", "")
            return f"{given} {family}".lower().strip()
        return ""

    normalized1 = {normalize_author(a) for a in authors1}
    normalized2 = {normalize_author(a) for a in authors2}

    # Calculate overlap
    intersection = normalized1 & normalized2
    union = normalized1 | normalized2

    if not union:
        return 0.0

    return len(intersection) / len(union)

def compare_journals(journal1: str, journal2: str) -> float:
    """Compare journal names and return similarity score."""
    if not journal1 or not journal2:
        return 0.0

    j1 = journal1.lower().strip()
    j2 = journal2.lower().strip()

    if j1 == j2:
        return 1.0

    # Check if one contains the other
    if j1 in j2 or j2 in j1:
        return 0.8

    return 0.0

def validate_batch(papers: List[Dict], workers: int = 4) -> List[Dict]:
    """Validate batch of papers with concurrency."""
    total = len(papers)
    info(f"[CrossRef] Validating {total} papers...")

    session = create_session()
    validated: List[Dict] = [dict(paper) for paper in papers]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        future_to_idx = {}
        for idx, paper in enumerate(validated, 1):
            doi = paper.get("doi")
            if not doi:
                paper["validation_score"] = 0.0
                paper["validated"] = False
                paper["reason"] = "No DOI provided"
                info(f"  [{idx}/{total}] 无DOI，跳过")
                continue
            print(f"  [{idx}/{total}] Validating DOI: {doi}")
            future = executor.submit(validate_paper, doi, paper, session)
            future_to_idx[future] = idx - 1

        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            paper = validated[idx]
            try:
                result = future.result()
            except Exception as exc:
                result = {"validation_score": 0.0, "validated": False, "reason": str(exc)}
            paper.update(result)
            score = result.get("validation_score", 0.0)
            if result.get("validated"):
                print(f"    ✓ Validated (score: {score:.2f})")
            else:
                print(f"    ✗ Failed (score: {score:.2f}, reason: {result.get('reason')})")

    info(f"[CrossRef] Validation complete: {sum(1 for p in validated if p.get('validated'))}/{total} papers passed")
    return validated

def main():
    parser = argparse.ArgumentParser(description="Validate papers via CrossRef")
    parser.add_argument("--input", required=True, help="Input JSON with papers")
    parser.add_argument("--output", required=True, help="Output validated JSON")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent requests (default 4)")
    parser.add_argument("--debug", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    global DEBUG
    DEBUG = args.debug

    with open(args.input, 'r') as f:
        data = json.load(f)

    validated = validate_batch(data.get("papers", []), workers=max(1, args.workers))

    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump({"papers": validated, "total": len(validated)}, f, indent=2)
    info(f"[CrossRef] 结果已保存到 {args.output}")


if __name__ == "__main__":
    main()
