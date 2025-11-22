#!/usr/bin/env python3
"""
文献管理工具函数

提供文献合并、去重、过滤等实用功能
"""

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any
from builtins import print as builtin_print

DEBUG = False

def debug_print(*args, **kwargs):
    if DEBUG:
        builtin_print(*args, **kwargs)

def info(*args, **kwargs):
    builtin_print(*args, **kwargs)

print = debug_print

def _is_empty(val: Any) -> bool:
    return val is None or val == "" or (isinstance(val, (list, dict)) and len(val) == 0)


def _prefer_source(existing: Dict, new: Dict, preferred: str = "pubmed") -> Dict:
    """合并两条记录，冲突字段以首选来源(preferred)为准，缺失字段用非空值补齐。

    - preferred 默认为 'pubmed'
    - 当来源相同或都非首选时：保留 existing 的值，缺失时用 new 的值补齐
    - 当 new 是首选来源而 existing 不是：冲突时用 new 的值覆盖；否则补齐缺失
    - 当 existing 是首选来源而 new 不是：保持 existing，缺失用 new 补齐
    """
    pref = str(preferred).lower()
    src_existing = str(existing.get("source", "")).lower()
    src_new = str(new.get("source", "")).lower()

    prefer_new = (src_new == pref) and (src_existing != pref)
    prefer_existing = (src_existing == pref) and (src_new != pref)

    merged: Dict[str, Any] = dict(existing)
    # 聚合所有字段键
    all_keys = set(existing.keys()) | set(new.keys())

    for k in all_keys:
        ev = merged.get(k)
        nv = new.get(k)
        if _is_empty(ev) and not _is_empty(nv):
            merged[k] = nv
            continue
        if not _is_empty(ev) and _is_empty(nv):
            continue
        # 冲突：两个都有值且不同
        if not _is_empty(ev) and not _is_empty(nv) and ev != nv:
            if prefer_new:
                merged[k] = nv
            elif prefer_existing:
                # keep existing
                pass
            else:
                # 都非首选或同为首选：保留 existing，特殊处理 authors 列表做并集去重
                if k == "authors" and isinstance(ev, list) and isinstance(nv, list):
                    try:
                        merged[k] = list(dict.fromkeys([*ev, *nv]))
                    except Exception:
                        merged[k] = ev
                # 其他字段保持 existing
        # 两者皆空：保持现状
    return merged


def merge_literature_sources(input_files: List[str], dedup_by: str = "doi") -> List[Dict]:
    """
    合并多个来源的文献并去重

    Args:
        input_files: 输入JSON文件列表
        dedup_by: 去重依据字段(默认为DOI)

    Returns:
        合并去重后的文献列表
    """
    merged_map: Dict[str, Dict] = {}
    no_key_items: List[Dict] = []

    for input_file in input_files:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            papers = data.get("papers", [])

            for paper in papers:
                key_raw = paper.get(dedup_by)
                key = str(key_raw).lower().strip() if key_raw else ""
                if not key:
                    no_key_items.append(paper)
                    continue
                if key in merged_map:
                    merged_map[key] = _prefer_source(merged_map[key], paper, preferred="pubmed")
                else:
                    merged_map[key] = dict(paper)
    # 合并结果：先有键的去重结果，再附加无键的条目
    return list(merged_map.values()) + no_key_items

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

    parser.add_argument("--debug", action="store_true", help="启用详细日志")

    args = parser.parse_args()
    global DEBUG
    DEBUG = args.debug

    if args.command == "merge":
        papers = merge_literature_sources(args.input, args.dedup_by)
        output = {"papers": papers, "total": len(papers)}
        info(f"[合并] 输入文件: {len(args.input)}个")
        info(f"[去重] 合并结果: {len(papers)}篇")
    elif args.command == "filter":
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        criteria = {k: v for k, v in vars(args).items()
                   if k.startswith("min_") and v is not None}
        papers = filter_by_criteria(data.get("papers", []), **criteria)
        output = {"papers": papers, "total": len(papers)}
        info(f"[过滤] 输入: {len(data.get('papers', []))}篇 → 输出: {len(papers)}篇")

    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    info(f"[完成] 结果已保存到 {args.output}")

if __name__ == "__main__":
    main()
