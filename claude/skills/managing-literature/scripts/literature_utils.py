#!/usr/bin/env python3
"""
文献管理工具函数

提供文献合并、去重、过滤等实用功能
"""

import argparse
import json
from typing import List, Dict

def merge_literature_sources(input_files: List[str], dedup_by: str = "doi") -> List[Dict]:
    """
    合并多个来源的文献并去重

    Args:
        input_files: 输入JSON文件列表
        dedup_by: 去重依据字段(默认为DOI)

    Returns:
        合并去重后的文献列表
    """
    all_papers = []
    seen = set()

    for input_file in input_files:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            papers = data.get("papers", [])

            for paper in papers:
                # 提取去重键(DOI/标题等)
                key = paper.get(dedup_by, "").lower().strip()

                if key and key not in seen:
                    seen.add(key)
                    all_papers.append(paper)
                elif not key:  # 没有去重键,保留
                    all_papers.append(paper)

    return all_papers

def filter_by_criteria(papers: List[Dict], **criteria) -> List[Dict]:
    """
    根据多个条件过滤文献

    Args:
        papers: 文献列表
        **criteria: 过滤条件(min_year, min_citations, min_impact_factor等)

    Returns:
        过滤后的文献列表
    """
    filtered = papers

    if "min_year" in criteria:
        filtered = [p for p in filtered if p.get("year", 0) >= criteria["min_year"]]

    if "min_citations" in criteria:
        filtered = [p for p in filtered if p.get("citations", 0) >= criteria["min_citations"]]

    if "min_impact_factor" in criteria:
        filtered = [p for p in filtered if p.get("impact_factor", 0) >= criteria["min_impact_factor"]]

    return filtered

def main():
    parser = argparse.ArgumentParser(description="Literature utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Merge command
    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--input", nargs="+", required=True, help="Input JSON files")
    merge_parser.add_argument("--output", required=True)
    merge_parser.add_argument("--dedup_by", default="doi", help="Field to deduplicate by")

    # Filter command
    filter_parser = subparsers.add_parser("filter")
    filter_parser.add_argument("--input", required=True)
    filter_parser.add_argument("--output", required=True)
    filter_parser.add_argument("--min_year", type=int)
    filter_parser.add_argument("--min_citations", type=int)
    filter_parser.add_argument("--min_impact_factor", type=float)

    args = parser.parse_args()

    if args.command == "merge":
        papers = merge_literature_sources(args.input, args.dedup_by)
        output = {"papers": papers, "total": len(papers)}
        print(f"[合并] 输入文件: {len(args.input)}个")
        print(f"[去重] 合并结果: {len(papers)}篇")
    elif args.command == "filter":
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        criteria = {k: v for k, v in vars(args).items()
                   if k.startswith("min_") and v is not None}
        papers = filter_by_criteria(data.get("papers", []), **criteria)
        output = {"papers": papers, "total": len(papers)}
        print(f"[过滤] 输入: {len(data.get('papers', []))}篇 → 输出: {len(papers)}篇")

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[完成] 结果已保存到 {args.output}")

if __name__ == "__main__":
    main()
