#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按加权总分筛选Top文献

功能概述（不改变其他脚本CLI）：
- 读取包含 papers 列表的JSON文件（通常来自 scihub_download.py 的成功集或 impact_factor.py 输出）。
- 在每条paper中，基于以下公式计算加权总分 total：
    total = quality_score * 0.4 + (
                theme_relevance * 0.4 +
                methods_relevance * 0.2 +
                results_relevance * 0.2 +
                argumentative_value * 0.2
            ) * 0.6
  其中各项取值来源：
    - quality_score: 由 impact_factor.py 计算并写入的字段；若缺失按0处理。
    - 主题等四项：来自 paper["relevance_score"][...]["score"]；若缺失按0处理，
      并兼容回退到 paper["final_score"] 或 paper["relevance_evaluation"]。
- 按总分降序排序，选取Top-K（默认3篇）。
- 输出到 {output_dir}/selected_${PART}_${query}-${hhmmss}.json（若总数小于K，则按实际数量输出），
  继承输入的所有顶层字段，仅用筛选后的papers替换，且为每条paper追加字段：
    - weighted_score: 计算得到的总分（float）
    - Reading_Report: 供后续人工/自动填写的结构化模板（中文键名）

用法示例：
  python select_top_papers.py \
    --input literature/5.texts/Results_20251111-0945.json \
    --output-dir literature/6.selected \
    --part Results \
    --top-k 3
"""

import argparse
import json
import re
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple


def _get(d: Dict[str, Any], path: List[str], default: float = 0.0) -> float:
    """从嵌套字典中安全取值并转为float。"""
    cur: Any = d
    try:
        for k in path:
            if not isinstance(cur, dict):
                return default
            cur = cur.get(k)
        if cur is None:
            return default
        return float(cur)
    except Exception:
        return default


def _scores_with_fallback(p: Dict[str, Any]) -> Dict[str, float]:
    """提取四项分数，优先 relevance_score，回退 final_score / relevance_evaluation。"""
    roots = ("relevance_score", "final_score", "relevance_evaluation")
    names = ("theme_relevance", "methods_relevance", "results_relevance", "argumentative_value")
    for root in roots:
        t = _get(p, [root, "theme_relevance", "score"], None)
        m = _get(p, [root, "methods_relevance", "score"], None)
        r = _get(p, [root, "results_relevance", "score"], None)
        a = _get(p, [root, "argumentative_value", "score"], None)
        if any(v is not None for v in (t, m, r, a)) or root == "final_score":
            return {
                "theme_relevance": float(t or 0.0),
                "methods_relevance": float(m or 0.0),
                "results_relevance": float(r or 0.0),
                "argumentative_value": float(a or 0.0),
            }
    return {n: 0.0 for n in names}


def compute_total_score(p: Dict[str, Any]) -> float:
    """按公式计算总分。缺失时按0处理。"""
    q = float(p.get("quality_score", 0.0) or 0.0)
    sc = _scores_with_fallback(p)
    t = sc["theme_relevance"]
    m = sc["methods_relevance"]
    r = sc["results_relevance"]
    a = sc["argumentative_value"]
    sub = t * 0.4 + m * 0.2 + r * 0.2 + a * 0.2
    total = q * 0.4 + sub * 0.6
    return float(total)


def reading_report_template() -> Dict[str, Any]:
    """返回 Reading_Report 占位模板。"""
    return {
        "core_content": { 
		"primary_finding": { 
			"statement": "", 
			"confidence_score": 0.0, 
			"location": "" },
		"methodological_details": { 
			"technique": "", 
			"sample_size": "",
			"statistical_method": "",
			"validation": "",
			"reproducibility_info": "",
			"extraction_relevance": 0.0 }, 
		"quantitative_results": { 
			"key_metrics": [ 
			{ 
				"metric": "", 
				"value": "", 
				"p_value": "", 
				"confidence_interval": null, 
				"comparison_baseline": "" }
				 ], 
			"suitable_for_citation": true 
			} 
	}, 
	"contextual_layers": { 
		"novelty_assessment": { 
			"innovation_type": "",
			"advancement_over_previous": "", 
			"citation_impact": "" }, 
		"biological_relevance": { 
			"disease_context": "", 
			"tissue_type": "", 
			"species": "", 
			"clinical_translation": "" }, 
		"technical_compatibility": { 
			"matches_our_methods": false, 
			"data_type": "", 
			"complementary_to_our_approach": true, 
			"integration_possibility": "" } 
	}, 
	"citation_recommendations": { 
		"primary_citation_text": "", 
		"citation_strength": "", 
		"alternative_uses": [ "", "" ], 
		"potential_conflicts": null }
    }


def sanitize_token(value: str, fallback: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()) if value else ""
    token = token.strip("_")
    return token or fallback


def slugify_query(value: str, fallback: str = "query") -> str:
    slug = value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug or fallback


def infer_part_query_from_input(path: str) -> Tuple[str, str]:
    stem = Path(path).stem
    part = "PART"
    remainder = ""
    if "_" in stem:
        part_candidate, remainder = stem.split("_", 1)
        if part_candidate:
            part = part_candidate
    else:
        remainder = stem
    query = "query"
    match = re.match(r"(.+)-(\d{6})$", remainder)
    if match:
        query = match.group(1) or query
    elif remainder:
        query = remainder
    return part, query


def main():
    parser = argparse.ArgumentParser(description="按加权总分筛选Top文献")
    parser.add_argument("--input", required=True, help="输入JSON文件（含papers）")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--part", help="撰写部分名称(用于文件命名)，可从输入meta.part推断")
    parser.add_argument("--top-k", type=int, default=3, help="输出的Top篇数，默认3")
    args = parser.parse_args()

    # 读取输入
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    papers: List[Dict[str, Any]] = list(data.get("papers", []) or [])
    if not papers:
        print("[信息] 输入中未找到papers，无输出。")
        return

    # 计算总分并排序
    for p in papers:
        try:
            p["weighted_score"] = compute_total_score(p)
        except Exception:
            p["weighted_score"] = 0.0

    papers.sort(key=lambda x: x.get("weighted_score", 0.0), reverse=True)

    k = max(1, int(args.top_k))
    selected = papers[: min(k, len(papers))]

    # 为选中的论文：
    # 1) 统一输出 relevance_score 字段（若只存在 final_score 或 relevance_evaluation，则复制为 relevance_score）；
    # 2) 移除旧字段 final_score / final_score_total（若存在）；
    # 3) 添加 Reading_Report 占位字段（若不存在）。
    for p in selected:
        try:
            p["weighted_score"] = compute_total_score(p)
        except Exception:
            p["weighted_score"] = 0.0
        # 统一 relevance_score 字段
        if not isinstance(p.get("relevance_score"), dict):
            for alt in ("final_score", "relevance_evaluation"):
                if isinstance(p.get(alt), dict):
                    try:
                        p["relevance_score"] = dict(p[alt])
                    except Exception:
                        p["relevance_score"] = p.get(alt)
                    break
        # 清理旧字段
        if "final_score" in p:
            try:
                del p["final_score"]
            except Exception:
                pass
        if "final_score_total" in p:
            try:
                del p["final_score_total"]
            except Exception:
                pass
        if not isinstance(p.get("Reading_Report"), dict):
            p["Reading_Report"] = reading_report_template()

    inferred_part, inferred_query = infer_part_query_from_input(args.input)
    part_token = sanitize_token(args.part or (data.get("meta", {}) or {}).get("part") or inferred_part, "PART")
    query_slug = slugify_query(inferred_query)
    time_hms = time.strftime("%H%M%S", time.localtime())
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"selected_{part_token}_{query_slug}-{time_hms}.json"

    # 继承顶层字段，仅替换 papers
    out_payload: Dict[str, Any]
    try:
        out_payload = dict(data)
    except Exception:
        out_payload = {}
    out_payload["papers"] = selected
    # 可选：同步更新 meta.total 为选中数量
    try:
        if isinstance(out_payload.get("meta"), dict):
            out_payload["meta"]["total"] = len(selected)
    except Exception:
        pass

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2, ensure_ascii=False)

    print(f"[完成] 已输出Top{len(selected)}: {out_path}")


if __name__ == "__main__":
    main()
