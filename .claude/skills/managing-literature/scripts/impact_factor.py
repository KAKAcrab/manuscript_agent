#!/usr/bin/env python3
"""
期刊影响因子查询工具（基于jcr.db数据库）

使用ShowJCR项目的jcr.db数据库，支持期刊名、ISSN、eISSN查询
返回影响因子、WOS大类、中科院/JCR分区、TOP期刊、预警状态等信息
"""

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

# jcr.db数据库路径
DATABASE_FILE = Path(__file__).parent / "jcr.db"

def normalize_journal_name(name: str) -> str:
    """标准化期刊名称用于模糊匹配"""
    if not name:
        return ""
    normalized = name.lower()
    normalized = normalized.replace("&", "and")
    normalized = " ".join(normalized.split())
    return normalized

def fuzzy_match_journal(cursor, table: str, journal_name: str) -> Optional[tuple]:
    """模糊匹配期刊名称
    
    匹配策略:
    1. 精确匹配(COLLATE NOCASE)
    2. 标准化匹配(&→and, 去除多余空格)
    3. LIKE模糊匹配(包含关键词)
    """
    # 策略1: 精确匹配
    cursor.execute(f"SELECT * FROM {table} WHERE Journal = ? COLLATE NOCASE", (journal_name,))
    row = cursor.fetchone()
    if row:
        return row
    
    # 策略2: 标准化匹配
    normalized_query = normalize_journal_name(journal_name)
    cursor.execute(f"SELECT * FROM {table}")
    all_journals = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    journal_col_idx = columns.index("Journal")
    
    for row in all_journals:
        if normalize_journal_name(row[journal_col_idx]) == normalized_query:
            print(f"[模糊匹配] '{journal_name}' → '{row[journal_col_idx]}'")
            return row
    
    # 策略3: LIKE模糊匹配
    keywords = [w for w in normalized_query.split() if len(w) > 3]
    if keywords:
        like_pattern = "%" + "% %".join(keywords) + "%"
        cursor.execute(f"SELECT * FROM {table} WHERE LOWER(Journal) LIKE ?", (like_pattern,))
        row = cursor.fetchone()
        if row:
            print(f"[关键词匹配] '{journal_name}' → '{row[journal_col_idx]}'")
            return row
    
    return None

def query_journal_info(
    journal_name: Optional[str] = None,
    issn: Optional[str] = None,
    eissn: Optional[str] = None
) -> Optional[Dict]:
    """
    查询期刊完整信息

    优先级: 期刊名 > ISSN > eISSN
    多年份数据时返回最新年份信息

    Args:
        journal_name: 期刊名称
        issn: Print ISSN
        eissn: Electronic ISSN

    Returns:
        期刊信息字典，包含IF、分区、TOP、预警等字段
        若未找到返回None
    """
    if not DATABASE_FILE.exists():
        print(f"[错误] 数据库文件未找到: {DATABASE_FILE}")
        return None

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # 1. 查询JCR影响因子(支持模糊匹配)
        jcr_info = None
        for year_table in ["JCR2024", "JCR2023", "JCR2022"]:
            if journal_name:
                row = fuzzy_match_journal(cursor, year_table, journal_name)
            elif issn:
                cursor.execute(f"SELECT * FROM {year_table} WHERE ISSN = ?", (issn,))
                row = cursor.fetchone()
            elif eissn:
                cursor.execute(f"SELECT * FROM {year_table} WHERE eISSN = ?", (eissn,))
                row = cursor.fetchone()
            else:
                return None

            if row:
                columns = [desc[0] for desc in cursor.description]
                jcr_info = dict(zip(columns, row))
                jcr_info["jcr_year"] = year_table.replace("JCR", "")
                break

        if not jcr_info:
            print(f"[本地] 未找到期刊: {journal_name or issn or eissn}")
            conn.close()
            return None

        # 2. 查询中科院分区（优先2025年，降级到2023/2022）
        fqb_info = None
        query_journal = jcr_info["Journal"]  # 使用JCR中的标准期刊名

        for year_table in ["FQBJCR2025", "FQBJCR2023", "FQBJCR2022"]:
            cursor.execute(f"SELECT * FROM {year_table} WHERE Journal = ? COLLATE NOCASE", (query_journal,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                fqb_info = dict(zip(columns, row))
                break

        # 3. 查询预警信息（优先2025年，降级到2024/2023）
        warning_info = None
        for year_table in ["GJQKYJMD2025", "GJQKYJMD2024", "GJQKYJMD2023"]:
            cursor.execute(f"SELECT * FROM {year_table} WHERE Journal = ? COLLATE NOCASE", (query_journal,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                warning_info = dict(zip(columns, row))
                break

        conn.close()

        # 4. 合并结果
        result = {
            "journal": jcr_info["Journal"],
            "issn": jcr_info.get("ISSN", ""),
            "eissn": jcr_info.get("eISSN", ""),
            "impact_factor": float(jcr_info.get(f"IF({jcr_info['jcr_year']})", 0.0)),
            "jcr_year": jcr_info["jcr_year"],
            "jcr_category": jcr_info.get("Category", ""),
            "jcr_quartile": jcr_info.get(f"IF Quartile({jcr_info['jcr_year']})", ""),
            "jcr_rank": jcr_info.get(f"IF Rank({jcr_info['jcr_year']})", ""),
        }

        # 添加中科院分区信息
        if fqb_info:
            result.update({
                "cas_year": str(fqb_info.get("年份", "")),
                "wos_type": fqb_info.get("Web of Science", ""),  # SCI, SCIE, SSCI等
                "cas_category": fqb_info.get("大类", ""),  # 中科院大类
                "cas_division": fqb_info.get("大类分区", ""),  # 中科院大类分区
                "is_top": fqb_info.get("Top", "") == "是",
                "subcategories": []
            })

            # 提取小类信息（最多6个小类）
            for i in range(1, 7):
                subcat = fqb_info.get(f"小类{i}", "")
                subdiv = fqb_info.get(f"小类{i}分区", "")
                if subcat:
                    result["subcategories"].append({
                        "name": subcat,
                        "division": subdiv
                    })
        else:
            result.update({
                "cas_year": "",
                "wos_type": "",
                "cas_category": "",
                "cas_division": "",
                "is_top": False,
                "subcategories": []
            })

        # 添加预警信息
        if warning_info:
            warning_reason = warning_info.get("预警原因（2025）") or \
                           warning_info.get("预警原因（2024）") or \
                           warning_info.get("预警原因（2023）") or \
                           warning_info.get("预警等级（2021）") or \
                           warning_info.get("预警等级（2020）")
            result["is_warning"] = True
            result["warning_reason"] = warning_reason
        else:
            result["is_warning"] = False
            result["warning_reason"] = ""

        return result

    except Exception as e:
        print(f"[错误] 数据库查询失败: {e}")
        return None

def format_journal_info(info: Dict) -> str:
    """
    格式化期刊信息为可读字符串

    Args:
        info: 期刊信息字典

    Returns:
        格式化后的字符串
    """
    lines = [
        f"期刊名称: {info['journal']}",
        f"ISSN: {info['issn']}",
        f"eISSN: {info['eissn']}",
        f"\n=== JCR {info['jcr_year']} ===",
        f"影响因子: {info['impact_factor']}",
        f"JCR分类: {info['jcr_category']}",
        f"JCR分区: {info['jcr_quartile']}",
        f"JCR排名: {info['jcr_rank']}"
    ]

    # 中科院分区
    if info.get("cas_year"):
        lines.extend([
            f"\n=== 中科院分区表 {info['cas_year']} ===",
            f"WOS类型: {info['wos_type']}",
            f"大类: {info['cas_category']}",
            f"大类分区: {info['cas_division']}",
            f"TOP期刊: {'是' if info['is_top'] else '否'}"
        ])

        if info.get("subcategories"):
            lines.append("\n小类分区:")
            for sub in info["subcategories"]:
                lines.append(f"  - {sub['name']}: {sub['division']}")

    # 预警信息
    if info.get("is_warning"):
        lines.extend([
            f"\n=== 预警信息 ===",
            f"⚠️  预警期刊",
            f"预警原因: {info['warning_reason']}"
        ])

    return "\n".join(lines)

def score_papers(papers: List[Dict]) -> List[Dict]:
    """
    为论文列表添加期刊评分信息

    兼容旧的impact_factor.py接口，用于managing-literature工作流

    Args:
        papers: 论文列表，每个论文包含journal、issn、eissn字段

    Returns:
        添加了journal_info和quality_score的论文列表
    """
    for paper in papers:
        journal = paper.get("journal", "")
        issn = paper.get("issn")
        eissn = paper.get("eissn")

        # 查询期刊信息
        journal_info = query_journal_info(journal_name=journal, issn=issn, eissn=eissn)

        if journal_info:
            paper["journal_info"] = journal_info
            paper["impact_factor"] = journal_info["impact_factor"]

            # 计算质量评分
            if_score = min(journal_info["impact_factor"] / 100, 1.0)  # 归一化到0-1
            year_score = min((2025 - paper.get("year", 2000)) / 10, 1.0)
            citations_score = min(paper.get("citations", 0) / 100, 1.0)

            # TOP期刊和低分区额外加分
            bonus = 0.0
            if journal_info.get("is_top"):
                bonus += 0.1
            if "1区" in journal_info.get("cas_division", "") or "Q1" in journal_info.get("jcr_quartile", ""):
                bonus += 0.05

            # 预警期刊扣分
            if journal_info.get("is_warning"):
                bonus -= 0.15

            quality_score = (
                if_score * 0.3 +
                year_score * 0.3 +
                citations_score * 0.2 +
                paper.get("validation_score", 0.8) * 0.2 +
                bonus
            )

            paper["quality_score"] = max(0.0, min(1.0, quality_score))
        else:
            # 未找到期刊信息，使用默认值
            paper["journal_info"] = None
            paper["impact_factor"] = 0.0
            paper["quality_score"] = 0.5  # 中等评分

    # 按quality_score降序排序
    return sorted(papers, key=lambda x: x.get("quality_score", 0), reverse=True)

def main():
    parser = argparse.ArgumentParser(description="查询期刊影响因子及分区信息")

    # 查询模式
    parser.add_argument("--journal", help="期刊名称")
    parser.add_argument("--issn", help="Print ISSN")
    parser.add_argument("--eissn", help="Electronic ISSN")

    # 批量评分模式（兼容旧接口）
    parser.add_argument("--input", help="输入JSON文件（论文列表）")
    parser.add_argument("--output", help="输出JSON文件（添加评分后的论文列表）")

    args = parser.parse_args()

    # 批量评分模式
    if args.input and args.output:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)

            scored = score_papers(data.get("papers", []))

            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump({"papers": scored}, f, indent=2, ensure_ascii=False)

            print(f"[完成] 已评分 {len(scored)} 篇论文，输出到 {args.output}")
        except Exception as e:
            print(f"[错误] 批量评分失败: {e}")
            return

    # 单期刊查询模式
    elif args.journal or args.issn or args.eissn:
        info = query_journal_info(
            journal_name=args.journal,
            issn=args.issn,
            eissn=args.eissn
        )

        if info:
            print("\n" + format_journal_info(info))
            print(f"\n[JSON输出]:")
            print(json.dumps(info, indent=2, ensure_ascii=False))
        else:
            print("[失败] 未找到期刊信息")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
