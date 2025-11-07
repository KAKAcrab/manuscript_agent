#!/usr/bin/env python3
"""
CrossRef validation tool for verifying literature authenticity.
"""

import argparse
import json
import requests
from typing import Dict, List

CROSSREF_API = "https://api.crossref.org/works"

def validate_paper(doi: str, paper_data: Dict) -> Dict:
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
        response = requests.get(f"{CROSSREF_API}/{doi}", timeout=10)

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

        # Validated if score >= 0.8
        validated = total_score >= 0.8

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

def validate_batch(papers: List[Dict]) -> List[Dict]:
    """Validate batch of papers."""
    validated = []
    total = len(papers)

    print(f"[CrossRef] Validating {total} papers...")

    for i, paper in enumerate(papers, 1):
        doi = paper.get("doi")

        if not doi:
            print(f"  [{i}/{total}] Skipping paper without DOI: {paper.get('title', 'Unknown')[:50]}")
            continue

        print(f"  [{i}/{total}] Validating DOI: {doi}")

        validation = validate_paper(doi, paper)
        paper.update(validation)

        score = validation.get("validation_score", 0)

        if score >= 0.8:
            validated.append(paper)
            print(f"    ✓ Validated (score: {score:.2f})")
        else:
            reason = validation.get("reason", "Score below threshold")
            print(f"    ✗ Failed (score: {score:.2f}, reason: {reason})")

    print(f"[CrossRef] Validation complete: {len(validated)}/{total} papers passed")
    return validated

def main():
    parser = argparse.ArgumentParser(description="Validate papers via CrossRef")
    parser.add_argument("--input", required=True, help="Input JSON with papers")
    parser.add_argument("--output", required=True, help="Output validated JSON")
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        data = json.load(f)

    validated = validate_batch(data.get("papers", []))

    with open(args.output, 'w') as f:
        json.dump({"papers": validated, "total": len(validated)}, f, indent=2)

if __name__ == "__main__":
    main()
