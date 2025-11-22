#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
show_journal_information.py

基于 impact_factor.py 内的数据库查询能力，提供两种模式：
1) 单期刊查询：通过 --journal / --issn / --eissn 指定任一标识，打印该期刊的完整信息。
2) 批量查询：通过 --input 指定包含期刊名称或 ISSN/eISSN 的文本文件（每行一个），
   自动识别类型并批量查询，结果保存为 Excel 表格。
"""

import argparse
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None  # type: ignore

from impact_factor import query_journal_info, format_journal_info  # noqa: E402


def detect_identifier(identifier: str) -> Tuple[str, str]:
    """根据字符串内容判断是 journal / issn / eissn。"""
    text = identifier.strip()
    issn_pattern = re.compile(r"^\d{4}-\d{3}[\dxX]$")
    if issn_pattern.match(text):
        return ("issn", text.upper())
    # eISSN 与 ISSN 格式相同，这里统一识别后在查询函数里复用
    return ("journal", text)


def query_single(journal: Optional[str], issn: Optional[str], eissn: Optional[str]) -> None:
    info = query_journal_info(journal_name=journal, issn=issn, eissn=eissn)
    if not info:
        print("[未找到] 请检查输入的期刊信息。")
        return
    print(format_journal_info(info))


def ensure_workbook_available() -> None:
    if Workbook is None:
        raise RuntimeError("openpyxl 未安装，无法输出 Excel。请先安装 openpyxl。")


def flatten_journal_info(info: Dict) -> List:
    subcats = info.get("subcategories") or []
    subcat_str = "; ".join(
        f"{item.get('name', '')}({item.get('division', '')})"
        for item in subcats
        if item.get("name")
    )
    return [
        info.get("journal", ""),
        info.get("issn", ""),
        info.get("eissn", ""),
        info.get("impact_factor", ""),
        info.get("jcr_year", ""),
        info.get("jcr_category", ""),
        info.get("jcr_quartile", ""),
        info.get("jcr_rank", ""),
        info.get("cas_year", ""),
        info.get("wos_type", ""),
        info.get("cas_category", ""),
        info.get("cas_division", ""),
        "是" if info.get("is_top") else "否",
        "是" if info.get("is_warning") else "否",
        info.get("warning_reason", ""),
        subcat_str,
    ]


def batch_query(input_file: str, output_file: str) -> None:
    ensure_workbook_available()
    src = Path(input_file)
    if not src.exists():
        raise FileNotFoundError(f"未找到输入文件: {input_file}")
    entries = [line.strip() for line in src.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not entries:
        raise ValueError("输入文件为空。")

    wb = Workbook()
    ws = wb.active
    ws.title = "JournalInfo"
    headers = [
        "Journal",
        "ISSN",
        "eISSN",
        "Impact Factor",
        "JCR Year",
        "JCR Category",
        "JCR Quartile",
        "JCR Rank",
        "CAS Year",
        "WOS Type",
        "CAS Category",
        "CAS Division",
        "Is TOP",
        "Is Warning",
        "Warning Reason",
        "Subcategories",
    ]
    ws.append(headers)

    for entry in entries:
        id_type, value = detect_identifier(entry)
        print(f"[批量] 查询 {id_type}: {value}")
        if id_type == "journal":
            info = query_journal_info(journal_name=value)
        else:
            info = query_journal_info(issn=value)
        if info:
            ws.append(flatten_journal_info(info))
            if info.get("is_warning") and info.get("warning_reason"):
                print(f"  ⚠️ 预警信息: {info.get('warning_reason')}")
        else:
            ws.append([value, "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    print(f"[完成] 批量结果已保存至 {out_path}")


def main():
    parser = argparse.ArgumentParser(description="查询期刊信息（单条/批量）")
    parser.add_argument("--journal", help="期刊名称")
    parser.add_argument("--issn", help="Print ISSN")
    parser.add_argument("--eissn", help="Electronic ISSN")
    parser.add_argument("--input", help="批量输入文件（每行一个期刊名称或ISSN）")
    parser.add_argument("--output", help="批量模式输出的Excel文件路径", default="journal_info.xlsx")

    args = parser.parse_args()

    if args.input:
        batch_query(args.input, args.output)
        return

    if not any([args.journal, args.issn, args.eissn]):
        parser.error("请指定 --journal / --issn / --eissn 之一，或使用 --input 进行批量查询。")

    query_single(args.journal, args.issn, args.eissn)


if __name__ == "__main__":
    main()
