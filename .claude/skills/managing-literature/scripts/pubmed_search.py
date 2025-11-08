#!/usr/bin/env python3
"""
PubMed文献检索工具

使用NCBI E-utilities API检索学术文献，返回结构化结果和开放获取状态
"""

import argparse
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
import requests
from xml.etree import ElementTree as ET

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# NCBI API配置（E-utilities要求提供邮箱）
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "research@example.com")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")  # 可选，提供后可提高速率限制

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def search_pubmed(
    query: str,
    max_results: int = 10,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    open_access_only: bool = False
) -> List[Dict]:
    """
    检索PubMed文献

    参数:
        query: 检索关键词
        max_results: 最大返回结果数
        min_year: 最小发表年份（可选）
        max_year: 最大发表年份（可选）
        open_access_only: 仅返回开放获取文章（可选）

    返回:
        文献字典列表，包含元数据
    """
    print(f"[PubMed检索] 查询: {query}")
    print(f"[PubMed检索] 正在检索PubMed...")

    # 构建检索条件
    from datetime import datetime
    current_year = datetime.now().year

    search_term = query
    if min_year or max_year:
        year_filter = ""
        if min_year and max_year:
            year_filter = f"{min_year}:{max_year}[pdat]"
        elif min_year:
            year_filter = f"{min_year}:{current_year}[pdat]"
        elif max_year:
            year_filter = f"1900:{max_year}[pdat]"
        search_term = f"({query}) AND {year_filter}"

    if open_access_only:
        search_term = f"({search_term}) AND open access[filter]"

    # 步骤1: ESearch获取PMID列表
    pmids = esearch(search_term, max_results)
    if not pmids:
        print(f"[PubMed检索] 未找到结果")
        return []

    print(f"[PubMed检索] 找到 {len(pmids)} 篇文献")

    # 步骤2: EFetch获取详细元数据
    results = efetch_details(pmids)

    print(f"[PubMed检索] 结果: 获取到 {len(results)} 篇文献")
    return results

def esearch(query: str, max_results: int) -> List[str]:
    """执行ESearch查询获取PMID列表"""
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "email": NCBI_EMAIL,
        "sort": "relevance"
    }

    if NCBI_API_KEY:
        params["api_key"] = NCBI_API_KEY

    try:
        response = requests.get(ESEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        pmids = data.get("esearchresult", {}).get("idlist", [])
        return pmids

    except Exception as e:
        print(f"[错误] ESearch失败: {e}")
        return []

def efetch_details(pmids: List[str]) -> List[Dict]:
    """使用EFetch获取PMID的详细元数据"""
    if not pmids:
        return []

    # 速率限制: 无API key时3请求/秒，有API key时10请求/秒
    delay = 0.1 if NCBI_API_KEY else 0.34

    results = []
    batch_size = 200  # 批量处理

    for i in range(0, len(pmids), batch_size):
        batch = pmids[i:i+batch_size]
        pmid_str = ",".join(batch)

        params = {
            "db": "pubmed",
            "id": pmid_str,
            "retmode": "xml",
            "email": NCBI_EMAIL
        }

        if NCBI_API_KEY:
            params["api_key"] = NCBI_API_KEY

        try:
            response = requests.get(EFETCH_URL, params=params, timeout=30)
            response.raise_for_status()

            # 解析XML响应
            root = ET.fromstring(response.content)
            articles = root.findall(".//PubmedArticle")

            for article in articles:
                metadata = extract_metadata(article)
                if metadata:
                    results.append(metadata)
                    print(f"  [{len(results)}] {metadata.get('title', '无标题')[:60]}... ({metadata.get('year', 'N/A')})")

            time.sleep(delay)

        except Exception as e:
            print(f"[警告] EFetch批次失败: {e}")
            continue

    return results

def extract_metadata(article_elem) -> Optional[Dict]:
    """从PubMed XML文章中提取标准化元数据"""
    try:
        medline_citation = article_elem.find(".//MedlineCitation")
        if medline_citation is None:
            return None

        # PMID
        pmid_elem = medline_citation.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""

        # 标题
        title_elem = medline_citation.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else ""

        # 作者
        authors = []
        author_list = medline_citation.find(".//AuthorList")
        if author_list is not None:
            for author in author_list.findall(".//Author"):
                lastname = author.find(".//LastName")
                forename = author.find(".//ForeName")
                if lastname is not None:
                    name = lastname.text
                    if forename is not None:
                        name = f"{forename.text} {name}"
                    authors.append(name)

        # 年份
        pub_date = medline_citation.find(".//PubDate")
        year = 0
        if pub_date is not None:
            year_elem = pub_date.find(".//Year")
            if year_elem is not None:
                try:
                    year = int(year_elem.text)
                except (ValueError, TypeError):
                    year = 0

        # 期刊
        journal_elem = medline_citation.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""

        # 摘要
        abstract_text = medline_citation.find(".//Abstract/AbstractText")
        abstract = ""
        if abstract_text is not None:
            # 处理结构化摘要
            if abstract_text.text:
                abstract = abstract_text.text
            else:
                # 合并所有摘要部分
                abstract_parts = []
                for abstract_elem in medline_citation.findall(".//Abstract/AbstractText"):
                    label = abstract_elem.get("Label", "")
                    text = abstract_elem.text or ""
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
                abstract = " ".join(abstract_parts)

        # DOI
        doi = ""
        article_id_list = article_elem.find(".//PubmedData/ArticleIdList")
        if article_id_list is not None:
            for article_id in article_id_list.findall(".//ArticleId"):
                if article_id.get("IdType") == "doi":
                    doi = article_id.text
                    break

        # 开放获取状态
        is_oa = False
        pmc_id = ""
        if article_id_list is not None:
            for article_id in article_id_list.findall(".//ArticleId"):
                if article_id.get("IdType") == "pmc":
                    pmc_id = article_id.text
                    is_oa = True
                    break

        # 引用次数（EFetch基础接口不提供，设为0）
        citations = 0

        # 构建URL
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        return {
            "title": title,
            "authors": authors,
            "year": year,
            "journal": journal,
            "abstract": abstract,
            "citations": citations,
            "doi": doi,
            "pmid": pmid,
            "pmcid": pmc_id,
            "is_open_access": is_oa,
            "url": url,
            "pdf_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/" if pmc_id else "",
            "source": "pubmed"
        }

    except Exception as e:
        print(f"[警告] 提取元数据失败: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="使用NCBI E-utilities检索PubMed")
    parser.add_argument("--query", required=True, help="检索关键词")
    parser.add_argument("--max_results", type=int, default=10,
                       help="最大返回结果数")
    parser.add_argument("--min_year", type=int, help="最小发表年份")
    parser.add_argument("--max_year", type=int, help="最大发表年份")
    parser.add_argument("--open_access_only", action="store_true",
                       help="仅返回开放获取文章")
    parser.add_argument("--max_oa", type=int, default=0,
                       help="额外检索的开放获取文章数量")
    parser.add_argument("--output", required=True,
                       help="输出JSON文件路径")

    args = parser.parse_args()

    # 基础检索
    results = search_pubmed(
        query=args.query,
        max_results=args.max_results,
        min_year=args.min_year,
        max_year=args.max_year,
        open_access_only=args.open_access_only
    )

    # OA专项检索(如果指定)
    if args.max_oa > 0 and not args.open_access_only:
        print(f"\n[PubMed] 执行OA专项检索,目标{args.max_oa}篇...")

        oa_results = search_pubmed(
            query=args.query,
            max_results=args.max_oa,
            min_year=args.min_year,
            max_year=args.max_year,
            open_access_only=True
        )

        # 合并结果并去重(基于PMID)
        existing_pmids = {paper.get("pmid") for paper in results if paper.get("pmid")}
        added = 0
        for paper in oa_results:
            if paper.get("pmid") and paper.get("pmid") not in existing_pmids:
                results.append(paper)
                existing_pmids.add(paper.get("pmid"))
                added += 1

        print(f"[PubMed] OA检索新增{added}篇,去重后总计{len(results)}篇")

    output_data = {
        "query": args.query,
        "max_oa": args.max_oa,
        "timestamp": datetime.now().isoformat(),
        "total_results": len(results),
        "open_access_count": sum(1 for p in results if p.get("is_open_access", False)),
        "papers": results
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"[PubMed检索] 结果已保存到 {args.output}")
    print(f"[PubMed检索] 开放获取: {output_data['open_access_count']}/{len(results)}")

if __name__ == "__main__":
    main()
