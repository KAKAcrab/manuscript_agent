#!/usr/bin/env python3
"""
OpenAlex literature search tool.

Searches OpenAlex API for academic papers with advanced filtering.
Free, open-source alternative to proprietary databases.
"""

import argparse
import json
import os
import requests
from typing import List, Dict, Optional
from datetime import datetime

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use os.environ directly

# Configuration from environment variables
OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL", "")
OPENALEX_API = os.getenv("OPENALEX_BASE_URL", "https://api.openalex.org/works")

if not OPENALEX_EMAIL:
    print("[WARNING] OPENALEX_EMAIL not set in environment. Using default.")
    print("[WARNING] Please set OPENALEX_EMAIL in .env file for polite pool access.")
    OPENALEX_EMAIL = "research@example.com"

def search_openalex(
    query: str,
    filter_criteria: Optional[str] = None,
    max_results: int = 10
) -> List[Dict]:
    """
    Search OpenAlex for papers.

    Args:
        query: Search query string
        filter_criteria: OpenAlex filter string (e.g., "publication_year:>2020")
        max_results: Maximum results to return

    Returns:
        List of paper dictionaries
    """
    results = []

    # Build query parameters
    params = {
        "search": query,
        "per-page": min(max_results, 200),  # OpenAlex max per page
        "mailto": OPENALEX_EMAIL  # From environment variable
    }

    if filter_criteria:
        params["filter"] = filter_criteria

    print(f"[OpenAlex] Query: {query}")
    if filter_criteria:
        print(f"[OpenAlex] Filter: {filter_criteria}")
    print(f"[OpenAlex] Searching OpenAlex API...")

    try:
        response = requests.get(OPENALEX_API, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        works = data.get('results', [])

        for work in works[:max_results]:
            try:
                metadata = extract_metadata(work)
                results.append(metadata)
                print(f"  [{len(results)}] {metadata.get('title', 'No title')[:60]}... ({metadata.get('year', 'N/A')})")
            except Exception as e:
                print(f"[WARNING] Error extracting metadata: {e}")
                continue

        print(f"[OpenAlex] Results: {len(results)} papers found")

    except requests.RequestException as e:
        print(f"[ERROR] OpenAlex API request failed: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    return results

def extract_metadata(work: Dict) -> Dict:
    """Extract standardized metadata from OpenAlex work object."""
    # Extract authors
    authors = []
    for authorship in work.get("authorships", []):
        author_info = authorship.get("author", {})
        author_name = author_info.get("display_name", "")
        if author_name:
            authors.append(author_name)

    # Extract DOI and clean it
    doi = work.get("doi", "")
    if doi and doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")

    # Extract journal/venue information
    primary_location = work.get("primary_location", {}) or {}
    source = primary_location.get("source", {}) or {}
    journal = source.get("display_name", "")

    # Get PDF URL if available from open access
    pdf_url = ""
    oa_info = work.get("open_access", {})
    if oa_info.get("is_oa"):
        pdf_url = oa_info.get("oa_url", "")

    # Get abstract - OpenAlex provides inverted abstract
    abstract = ""
    abstract_inverted = work.get("abstract_inverted_index", {})
    if abstract_inverted:
        # Reconstruct abstract from inverted index
        abstract = reconstruct_abstract(abstract_inverted)

    return {
        "title": work.get("title", ""),
        "authors": authors,
        "year": work.get("publication_year", 0),
        "journal": journal,
        "abstract": abstract,
        "citations": work.get("cited_by_count", 0),
        "doi": doi,
        "pmid": "",  # OpenAlex不提供PMID
        "pmcid": "",  # OpenAlex不提供PMCID
        "url": work.get("id", ""),
        "pdf_url": pdf_url,
        "is_open_access": work.get("open_access", {}).get("is_oa", False),
        "source": "openalex"
    }

def reconstruct_abstract(inverted_index: Dict) -> str:
    """Reconstruct abstract text from OpenAlex inverted index."""
    if not inverted_index:
        return ""

    # Build list of (position, word) tuples
    words_with_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            words_with_positions.append((pos, word))

    # Sort by position and join
    words_with_positions.sort(key=lambda x: x[0])
    abstract = " ".join([word for _, word in words_with_positions])

    return abstract

def main():
    parser = argparse.ArgumentParser(description="Search OpenAlex")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--filter", help="Filter criteria (e.g., publication_year:>2020)")
    parser.add_argument("--max_results", type=int, default=10)
    parser.add_argument("--max_oa", type=int, default=0, help="Additional open access papers to retrieve")
    parser.add_argument("--output", required=True, help="Output JSON file")

    args = parser.parse_args()

    # 基础检索
    results = search_openalex(
        query=args.query,
        filter_criteria=args.filter,
        max_results=args.max_results
    )

    # OA专项检索(如果指定)
    if args.max_oa > 0:
        print(f"\n[OpenAlex] 执行OA专项检索,目标{args.max_oa}篇...")

        # 构建OA过滤器
        oa_filter = "is_oa:true"
        if args.filter:
            oa_filter = f"{args.filter},is_oa:true"

        oa_results = search_openalex(
            query=args.query,
            filter_criteria=oa_filter,
            max_results=args.max_oa
        )

        # 合并结果并去重(基于DOI)
        existing_dois = {paper.get("doi") for paper in results if paper.get("doi")}
        for paper in oa_results:
            if paper.get("doi") and paper.get("doi") not in existing_dois:
                results.append(paper)
                existing_dois.add(paper.get("doi"))

        print(f"[OpenAlex] OA检索新增{len(oa_results)}篇,去重后总计{len(results)}篇")

    output_data = {
        "query": args.query,
        "filter": args.filter,
        "max_oa": args.max_oa,
        "timestamp": datetime.now().isoformat(),
        "total_results": len(results),
        "oa_count": sum(1 for p in results if p.get("is_open_access")),
        "papers": results
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"[OpenAlex] Results saved to {args.output}")

if __name__ == "__main__":
    main()
