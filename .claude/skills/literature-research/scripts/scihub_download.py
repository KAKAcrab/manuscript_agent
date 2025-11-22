#!/usr/bin/env python3
"""
文献下载与转换工具(Sci-Hub + PMC + MarkItDown集成版)

功能:
1. 通过Sci-Hub下载PDF (基于scihub-cn项目)
2. 通过PMC OA Web Service获取XML全文
3. 使用MarkItDown转换PDF/XML/DOCX等为Markdown

使用方法:
  # 单篇下载
  python scihub_download.py download --doi "10.1038/nature12373" --output papers/

  # 批量下载
  python scihub_download.py batch --input validated_papers.json --output papers/

  # 仅转换已下载文件
  python scihub_download.py convert --input paper.pdf --output paper.md
"""

import argparse
import json
import os
import re
import sys
import time
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import threading
from builtins import print as builtin_print

DEBUG = False

def debug_print(*args, **kwargs):
    if DEBUG:
        builtin_print(*args, **kwargs)

def info(*args, **kwargs):
    builtin_print(*args, **kwargs)

print = debug_print

# 可选依赖: PaddleOCR / PP-Structure / PyMuPDF / Pillow / NumPy
PADDLE_AVAILABLE = False
PPSTRUCT_AVAILABLE = False
Fitz = None
Image = None
np = None
try:
    from paddleocr import PaddleOCR, PPStructure  # type: ignore
    PADDLE_AVAILABLE = True
    PPSTRUCT_AVAILABLE = True
except Exception:
    PADDLE_AVAILABLE = False
    PPSTRUCT_AVAILABLE = False

try:
    import fitz as Fitz  # PyMuPDF
except Exception:
    Fitz = None

try:
    from PIL import Image as PILImage
    Image = PILImage
except Exception:
    Image = None

try:
    import numpy as numpy
    np = numpy
except Exception:
    np = None

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# MinerU API 配置（通过环境变量加载）
MINERU_BASE_URL = os.getenv("MINERU_BASE_URL", "https://mineru.net")
MINERU_API_TOKEN = os.getenv("MINERU_API_TOKEN")
MINERU_API_TOKEN_1 = os.getenv("MINERU_API_TOKEN_1")
MINERU_API_TOKEN_2 = os.getenv("MINERU_API_TOKEN_2")
MINERU_API_TOKEN_3 = os.getenv("MINERU_API_TOKEN_3")
MINERU_API_TOKEN_4 = os.getenv("MINERU_API_TOKEN_4")
MINERU_MODEL_VERSION = os.getenv("MINERU_MODEL_VERSION", "vlm")  # 可选: pipeline / vlm
MINERU_SUBMIT_RPM = int(os.getenv("MINERU_SUBMIT_RPM", "300"))   # 提交频控：300次/分钟
MINERU_POLL_RPM = int(os.getenv("MINERU_POLL_RPM", "1000"))      # 查询频控：1000次/分钟
MINERU_TRUST_ENV = os.getenv("MINERU_TRUST_ENV", "0")
MINERU_PROXIES = os.getenv("MINERU_PROXIES")  # 例如: http://127.0.0.1:7890
MINERU_TIMEOUT = float(os.getenv("MINERU_TIMEOUT", "60"))
MINERU_FORCE_IPV4 = os.getenv("MINERU_FORCE_IPV4", "0")
EXTRACTION_TIMESTAMP_ENV = os.getenv("EXTRACTION_TIMESTAMP", "")
TARGET_MANUSCRIPT_SECTION_ENV = os.getenv("TARGET_MANUSCRIPT_SECTION", "")
CITATION_POINT_ID_ENV = os.getenv("CITATION_POINT_ID", "")
EXTRACTION_PURPOSE_ENV = os.getenv("EXTRACTION_PURPOSE", "")

# 配置
SCIHUB_URLS = [
    "https://sci-hub.se",
    "https://sci-hub.st",
    "https://sci-hub.ru"
]

PMC_OA_SERVICE = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi"
PMC_ID_CONVERTER = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def _create_retry_session() -> requests.Session:
    sess = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods={"GET", "POST"},
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=32)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    sess.headers.update(HEADERS)
    sess.trust_env = False
    return sess

def _build_front_md_from_xml(xml_path: str) -> str:
    """从JATS(XML)提取题目/作者/文献信息/摘要，组装为Markdown前置片段。
    仅做补全，不做裁剪；字段缺失则跳过。
    """
    try:
        from bs4 import BeautifulSoup as _BS
    except Exception:
        return ""
    try:
        import re as _re
        with open(xml_path, 'r', encoding='utf-8') as f:
            soup = _BS(f, 'xml')

        def _get_text(node):
            if not node:
                return ""
            txt = node.get_text(" ", strip=True)
            return _re.sub(r"\s+", " ", txt).strip()

        title = _get_text(soup.find('article-title'))

        # authors
        authors = []
        for c in soup.select('contrib-group contrib'):
            if c.get('contrib-type') and c['contrib-type'] not in ("author", ""):
                continue
            surname = _get_text(c.find('surname'))
            given = _get_text(c.find('given-names'))
            string_name = _get_text(c.find('string-name'))
            collab = _get_text(c.find('collab'))
            name = (given + " " + surname).strip()
            if not name:
                name = string_name or collab
            if name:
                authors.append(name)

        # article info
        journal = _get_text(soup.find('journal-title'))
        year = _get_text(soup.find('pub-date', {'pub-type': 'ppub'}).find('year') if soup.find('pub-date', {'pub-type': 'ppub'}) else soup.find('year'))
        volume = _get_text(soup.find('volume'))
        issue = _get_text(soup.find('issue'))
        fpage = _get_text(soup.find('fpage'))
        lpage = _get_text(soup.find('lpage'))
        doi = ""
        for aid in soup.find_all('article-id'):
            if aid.get('pub-id-type') == 'doi':
                doi = _get_text(aid)
                break

        # abstract
        abs_node = soup.find('abstract')
        abstract = _get_text(abs_node)

        parts = []
        if title:
            parts.append(f"# {title}\n\n")
        if authors:
            parts.append("**Authors**: " + ", ".join(authors) + "\n\n")
        info = []
        if journal:
            info.append(journal)
        if year:
            info.append(year)
        vi = ""
        if volume:
            vi = volume
            if issue:
                vi += f"({issue})"
            info.append(vi)
        pages = ""
        if fpage:
            pages = fpage
            if lpage:
                pages += f"-{lpage}"
            info.append(pages)
        if doi:
            info.append(f"DOI: {doi}")
        if info:
            parts.append("**Article Info**: " + "; ".join([p for p in info if p]) + "\n\n")
        if abstract:
            parts.append("## Abstract\n\n" + abstract + "\n\n")
        return "".join(parts)
    except Exception:
        return ""

def _trim_markdown_by_heading_levels(md_text: str, stop_keywords: List[str], levels: Tuple[int, ...] = (1, 2)) -> Optional[str]:
    """按标题级别裁剪：当H1/H2标题包含停止关键字时，从该标题开始截断到文末。

    - md_text: Pandoc 产出的Markdown文本
    - stop_keywords: 截断关键词列表（大小写不敏感）
    - levels: 参与截断的标题级别（默认 (1,2) 表示 # 和 ##）
    返回裁剪后的文本；若无需裁剪返回原文；若入参为空返回None。
    """
    if not md_text:
        return None
    lines = md_text.splitlines()
    stop_l = [s.lower() for s in (stop_keywords or [])]
    if not stop_l:
        return md_text
    def is_stop_heading(line: str) -> bool:
        l = line.lstrip()
        if not l.startswith('#'):
            return False
        # 统计 # 数量
        i = 0
        while i < len(l) and l[i] == '#':
            i += 1
        if i == 0:
            return False
        if i not in levels:
            return False
        title = l[i:].strip().lower()
        return any(k in title for k in stop_l)
    for idx, line in enumerate(lines):
        if is_stop_heading(line):
            return "\n".join(lines[:idx]).rstrip() + "\n"
    return md_text


def download_via_scihub(identifier: str, output_path: str) -> bool:
    """
    通过Sci-Hub下载文献PDF

    Args:
        identifier: DOI、PMID或论文URL
        output_path: PDF输出路径

    Returns:
        下载是否成功
    """
    print(f"[Sci-Hub] 尝试下载: {identifier}")

    session = _create_retry_session()

    for scihub_url in SCIHUB_URLS:
        try:
            print(f"[Sci-Hub] 使用镜像: {scihub_url}")

            # 访问Sci-Hub页面
            response = session.get(f"{scihub_url}/{identifier}", timeout=30)

            if response.status_code != 200:
                print(f"[Sci-Hub] 镜像访问失败: {response.status_code}")
                continue

            # 解析PDF链接
            soup = BeautifulSoup(response.content, 'html.parser')

            # 方法1: iframe中的PDF
            iframe = soup.find('iframe', id='pdf')
            if iframe and iframe.get('src'):
                pdf_url = iframe['src']
                if not pdf_url.startswith('http'):
                    pdf_url = urljoin(scihub_url, pdf_url)

                print(f"[Sci-Hub] 找到PDF链接: {pdf_url}")

                # 下载PDF
                pdf_response = session.get(pdf_url, timeout=60)
                if pdf_response.status_code == 200 and pdf_response.content[:4] == b'%PDF':
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(pdf_response.content)
                    print(f"[Sci-Hub] 下载成功: {output_path} ({len(pdf_response.content)} bytes)")
                    return True

            # 方法2: 嵌入式PDF链接
            embed = soup.find('embed', {'type': 'application/pdf'})
            if embed and embed.get('src'):
                pdf_url = embed['src']
                if not pdf_url.startswith('http'):
                    pdf_url = urljoin(scihub_url, pdf_url)

                print(f"[Sci-Hub] 找到PDF链接(embed): {pdf_url}")

                pdf_response = session.get(pdf_url, timeout=60)
                if pdf_response.status_code == 200 and pdf_response.content[:4] == b'%PDF':
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(pdf_response.content)
                    print(f"[Sci-Hub] 下载成功: {output_path}")
                    return True

            # 方法3: 直接PDF按钮
            button = soup.find('button', {'onclick': re.compile(r'location\.href')})
            if button:
                onclick = button.get('onclick', '')
                pdf_match = re.search(r"location\.href='([^']+)'", onclick)
                if pdf_match:
                    pdf_url = pdf_match.group(1)
                    if not pdf_url.startswith('http'):
                        pdf_url = urljoin(scihub_url, pdf_url)

                    print(f"[Sci-Hub] 找到PDF链接(button): {pdf_url}")

                    pdf_response = session.get(pdf_url, timeout=60)
                    if pdf_response.status_code == 200 and pdf_response.content[:4] == b'%PDF':
                        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"[Sci-Hub] 下载成功: {output_path}")
                        return True

            print(f"[Sci-Hub] 未找到有效PDF链接")

        except Exception as e:
            print(f"[Sci-Hub] 镜像错误: {e}")
            continue

    print(f"[Sci-Hub] 所有镜像均失败")
    return False


def convert_doi_to_pmid(doi: str) -> Optional[str]:
    """
    使用PMC ID Converter API将DOI转换为PMID

    Args:
        doi: DOI标识符

    Returns:
        PMID字符串,失败返回None
    """
    try:
        # 构造API请求参数（tool和email为必填项）
        params = {
            "tool": "manuscript_agent",
            "email": NCBI_EMAIL,
            "ids": doi,
            "idtype": "doi",
            "format": "json"
        }

        session = _create_retry_session()
        response = session.get(PMC_ID_CONVERTER, params=params, timeout=15)

        if response.status_code != 200:
            return None

        data = response.json()

        # 检查响应结构
        if "records" in data and len(data["records"]) > 0:
            record = data["records"][0]
            pmid = record.get("pmid")
            if pmid:
                print(f"[PMC ID Converter] DOI {doi} → PMID {pmid}")
                return pmid

        return None

    except Exception as e:
        print(f"[PMC ID Converter] 转换失败: {e}")
        return None


def download_via_pmc(identifier: str, output_dir: str) -> Optional[str]:
    """
    通过PMC OA Web Service下载XML全文

    Args:
        identifier: DOI或PMID或PMCID
        output_dir: 输出目录

    Returns:
        下载的文件路径,失败返回None
    """
    print(f"[PMC] 尝试获取XML: {identifier}")

    try:
        session = _create_retry_session()
        # 确定查询ID类型
        query_id = identifier

        # 如果是DOI，先转换为PMID
        if identifier.startswith("10."):
            pmid = convert_doi_to_pmid(identifier)
            if pmid:
                query_id = pmid
            else:
                print(f"[PMC] DOI转PMID失败，尝试直接使用DOI")

        # 如果是纯数字的PMID（不是以PMC开头），先转换为PMCID
        elif identifier.isdigit():
            # 纯数字是PMID，需要转换为PMCID
            pmid_to_pmcid_params = {
                "tool": "manuscript_agent",
                "email": NCBI_EMAIL,
                "ids": identifier,
                "idtype": "pmid",
                "format": "json"
            }
            try:
                id_response = session.get(PMC_ID_CONVERTER, params=pmid_to_pmcid_params, timeout=15)
                if id_response.status_code == 200:
                    id_data = id_response.json()
                    if "records" in id_data and len(id_data["records"]) > 0:
                        pmcid = id_data["records"][0].get("pmcid")
                        if pmcid:
                            print(f"[PMC ID Converter] PMID {identifier} → PMCID {pmcid}")
                            query_id = pmcid
            except Exception as e:
                print(f"[PMC] PMID转PMCID失败: {e}")

        # 查询PMC ID
        params = {
            "id": query_id,
            "format": "tgz"  # 获取完整文件包
        }

        response = session.get(PMC_OA_SERVICE, params=params, timeout=30)

        if response.status_code != 200:
            print(f"[PMC] API请求失败: {response.status_code}")
            return None

        # 解析响应XML
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)

        # 查找error
        error = root.find('.//error')
        if error is not None:
            print(f"[PMC] API错误: {error.text}")
            return None

        # 查找link元素
        link = root.find('.//link')
        if link is None or 'href' not in link.attrib:
            print(f"[PMC] 未找到下载链接")
            return None

        download_url = link.attrib['href']
        pmcid = root.find('.//record').attrib.get('id', 'unknown')

        # FTP链接转换为HTTPS (PMC支持HTTPS访问)
        if download_url.startswith('ftp://ftp.ncbi.nlm.nih.gov'):
            download_url = download_url.replace('ftp://ftp.ncbi.nlm.nih.gov', 'https://ftp.ncbi.nlm.nih.gov')

        print(f"[PMC] PMCID: {pmcid}, 下载URL: {download_url}")

        # 下载tar.gz文件
        tgz_response = session.get(download_url, timeout=60, stream=True)
        if tgz_response.status_code != 200:
            print(f"[PMC] 下载失败: {tgz_response.status_code}")
            return None

        # 保存并解压
        import tarfile
        import tempfile

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as tmp_file:
            for chunk in tgz_response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_path = tmp_file.name

        # 解压查找XML
        extracted_xml = None
        with tarfile.open(tmp_path, 'r:gz') as tar:
            for member in tar.getmembers():
                if member.name.endswith('.nxml') or member.name.endswith('.xml'):
                    # 提取XML文件
                    tar.extract(member, output_dir)
                    extracted_xml = os.path.join(output_dir, member.name)
                    print(f"[PMC] XML已提取: {extracted_xml}")
                    break

        # 清理临时文件
        os.unlink(tmp_path)

        if extracted_xml:
            # 移动到标准位置
            final_path = os.path.join(output_dir, f"{pmcid}.xml")
            if extracted_xml != final_path:
                os.rename(extracted_xml, final_path)
                extracted_xml = final_path

            return extracted_xml
        else:
            print(f"[PMC] tar.gz中未找到XML文件")
            return None

    except Exception as e:
        print(f"[PMC] 下载错误: {e}")
        return None


# ------------------------
# 转换辅助与实现
# ------------------------

DEFAULT_SECTIONS = [
    "title",
    "authors",
    "abstract",
    "introduction",
    "methods",
    "results",
    "discussion",
    "conclusion",
]

DEFAULT_STOP_AFTER = [
    "reference", "references",
    "acknowledgement", "acknowledgements",
    "acknowledgment", "acknowledgments",
    "supplement", "supplemental", "supplementary", "supplementary material", "supplementary materials",
    "appendix", "appendices",
]

READING_REPORT_TEMPLATE_JSON = r"""
{
  "core_content": {
    "primary_finding": {
      "statement": "",
      "confidence_score": 0.0,
      "location": ""
    },
    "methodological_details": {
      "technique": "",
      "sample_size": "",
      "statistical_method": "",
      "validation": "",
      "reproducibility_info": "",
      "extraction_relevance": 0.0
    },
    "quantitative_results": {
      "key_metrics": [
        {
          "metric": "",
          "value": "",
          "p_value": "",
          "confidence_interval": null,
          "comparison_baseline": ""
        }
      ],
      "suitable_for_citation": true
    }
  },
  "contextual_layers": {
    "novelty_assessment": {
      "innovation_type": "",
      "advancement_over_previous": "",
      "citation_impact": ""
    },
    "biological_relevance": {
      "disease_context": "",
      "tissue_type": "",
      "species": "",
      "clinical_translation": ""
    },
    "technical_compatibility": {
      "matches_our_methods": false,
      "data_type": "",
      "complementary_to_our_approach": true,
      "integration_possibility": ""
    }
  },
  "citation_recommendations": {
    "primary_citation_text": "",
    "citation_strength": "",
    "alternative_uses": [
      "",
      ""
    ],
    "potential_conflicts": null
  }
}
"""

def _reading_report_template() -> Dict:
    try:
        return json.loads(READING_REPORT_TEMPLATE_JSON)
    except Exception:
        return {}


def _build_extraction_context() -> Dict[str, str]:
    return {
        "extraction_timestamp": EXTRACTION_TIMESTAMP_ENV,
        "target_manuscript_section": TARGET_MANUSCRIPT_SECTION_ENV,
        "citation_point_id": CITATION_POINT_ID_ENV,
        "extraction_purpose": EXTRACTION_PURPOSE_ENV,
    }


def _is_stop_heading(text: str) -> bool:
    """严格判定章节级早停标题（仅限真正的References / Acknowledgements / Supplementary / Appendix）。

    注意：不应匹配正文中的“Supplement Table I”等；仅允许匹配短行、疑似纯章节标题的文本。
    """
    if not text:
        return False
    t = (text or "").strip()
    if not t:
        return False
    # 太长的行不可能是标准章节标题
    if len(t) > 80:
        return False
    tl = t.lower()
    # 排除包含易混淆词的正文行
    if any(x in tl for x in ["table", "figure", "movie", "video"]):
        return False
    import re as _re
    # 允许前缀中包含序号 / 标号等噪声
    pat = _re.compile(
        r"^[\s\(\)\[\]\-–—:,.0-9ivx]{0,8}\b("
        r"references?|acknowledg(?:e)?ments?|"
        r"supplement(?:al|ary)(?:\s+materials?)?|"
        r"supplementary(?:\s+materials?)?|"
        r"appendix|appendices"
        r")\b[\s\-–—:,.]*$",
        flags=_re.I,
    )
    return bool(pat.match(tl))


# ------------------------
# 路径/文件名辅助
# ------------------------
def _safe_stem(doi: Optional[str], pmid: Optional[str], pmcid: Optional[str], url: Optional[str]) -> str:
    """根据标识符生成安全文件名前缀，与 download_single_paper 内部规则保持一致。"""
    ident = doi or pmid or pmcid or url or "paper"
    # 只替换容易影响文件名的字符，保持与既有逻辑一致
    return ident.replace("/", "_").replace(":", "_").replace(".", "_")


def _ensure_relevance_score(paper: Dict) -> None:
    if not isinstance(paper.get("relevance_score"), dict):
        paper["relevance_score"] = {
            "theme_relevance": {"score": 0.0, "evaluation": ""},
            "methods_relevance": {"score": 0.0, "evaluation": ""},
            "results_relevance": {"score": 0.0, "evaluation": ""},
            "argumentative_value": {"score": 0.0, "evaluation": ""},
        }


def _ensure_extraction_context(paper: Dict) -> None:
    if not isinstance(paper.get("extraction_context"), dict):
        paper["extraction_context"] = _build_extraction_context()


def _ensure_reading_report(paper: Dict) -> None:
    if not isinstance(paper.get("Reading_Report"), dict):
        paper["Reading_Report"] = _reading_report_template()


# ------------------------
# DOI 索引管理
# ------------------------
def _normalize_doi(doi: Optional[str]) -> Optional[str]:
    if not doi:
        return None
    d = str(doi).strip()
    d = d.replace('\n', ' ').replace('\r', ' ').strip()
    d = d.lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "http://dx.doi.org/", "doi:"):
        if d.startswith(prefix):
            d = d[len(prefix):]
            break
    return d.strip() or None


def _load_doi_index(index_path: Path) -> Dict[str, str]:
    try:
        if index_path.exists():
            return json.loads(index_path.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {}


def _save_doi_index(index_path: Path, idx: Dict[str, str]) -> None:
    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(idx, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception as e:
        info(f"[Index] 写入失败: {e}")


def _reconcile_index_with_md(index_path: Path, output_dir: Path) -> Dict[str, str]:
    """清理索引中指向不存在的md文件；不新增未知md条目。"""
    idx = _load_doi_index(index_path)
    changed = False
    for doi, md_name in list(idx.items()):
        md_path = output_dir / md_name
        if not md_path.exists():
            idx.pop(doi, None)
            changed = True
    if changed:
        _save_doi_index(index_path, idx)
    return idx


def _refresh_doi_index_from_jsons(output_dir: Path) -> Dict[str, str]:
    """扫描输出目录下所有 .json 成功集文件，提取 doi→md_file 映射并保存到索引文件 doi_index（无扩展名）。

    仅保留 md 文件实际存在的映射，避免索引与文件不一致。
    """
    mapping: Dict[str, str] = {}
    try:
        for jf in output_dir.glob('*.json'):
            try:
                data = json.loads(jf.read_text(encoding='utf-8'))
            except Exception:
                continue
            papers = data.get('papers') or []
            if not isinstance(papers, list):
                continue
            for p in papers:
                if not isinstance(p, dict):
                    continue
                doi = _normalize_doi(p.get('doi'))
                mdf = p.get('md_file')
                if doi and mdf:
                    mapping[doi] = str(mdf)
    except Exception:
        pass
    # 仅保留存在的 md 文件
    mapping2: Dict[str, str] = {}
    for d, m in mapping.items():
        if (output_dir / m).exists():
            mapping2[d] = m
    _save_doi_index(output_dir / 'doi_index', mapping2)
    return mapping2

# 去重：_is_stop_heading 已在上方定义（保留单一定义）

def _convert_pdf_with_pymupdf4llm(
    input_pdf: str,
    output_md: str,
    max_pages: Optional[int] = None,
) -> bool:
    """使用 PyMuPDF4LLM 将PDF转换为Markdown，仅保留“页面级裁剪”，不做任何主体/标题/噪声微调。"""
    t0 = time.perf_counter()
    try:
        import pymupdf4llm
    except Exception:
        return False
    try:
        # 先做页面级裁剪（保留出现停止标题的那一页）
        src_pdf = _trim_pdf_to_subject_pages(input_pdf, max_pages=max_pages)
        md_src = pymupdf4llm.to_markdown(src_pdf or input_pdf)
        if not md_src or not md_src.strip():
            return False
        Path(output_md).parent.mkdir(parents=True, exist_ok=True)
        Path(output_md).write_text(md_src, encoding='utf-8')
        print(f"[Convert] PDF转换成功(PyMuPDF4LLM)")
        t1 = time.perf_counter()
        print(f"[时间][PDF] PyMuPDF4LLM total={t1 - t0:.2f}s")
        return True
    except Exception as e:
        print(f"[Convert] PyMuPDF4LLM失败: {e}")
        return False

# 去重：_is_stop_heading 已在上方定义（保留单一定义）

# ------------------------
# MinerU API 集成（批量/单文件）
# ------------------------

def _mineru_tokens() -> List[str]:
    toks = []
    if MINERU_API_TOKEN:
        toks.append(MINERU_API_TOKEN)
    if MINERU_API_TOKEN_1 and MINERU_API_TOKEN_1 not in toks:
        toks.append(MINERU_API_TOKEN_1)
    if MINERU_API_TOKEN_2 and MINERU_API_TOKEN_2 not in toks:
        toks.append(MINERU_API_TOKEN_2)
    if MINERU_API_TOKEN_3 and MINERU_API_TOKEN_3 not in toks:
        toks.append(MINERU_API_TOKEN_3)
    if MINERU_API_TOKEN_4 and MINERU_API_TOKEN_4 not in toks:
        toks.append(MINERU_API_TOKEN_4)
    return toks


def _mineru_api_available() -> bool:
    return len(_mineru_tokens()) > 0


def _page_contains_stop_heading(text: str) -> bool:
    if not text:
        return False
    for ln in text.splitlines():
        if _is_stop_heading(ln):
            return True
    return False


def _trim_pdf_to_subject_pages(src_pdf: str, max_pages: Optional[int] = None, stop_after: Optional[List[str]] = None) -> Optional[str]:
    """按页扫描，遇到章节级停止标题则在该页之后截断（保留该页）。返回裁剪后的临时PDF路径。"""
    try:
        import fitz
    except Exception:
        return None
    try:
        doc = fitz.open(src_pdf)
    except Exception:
        return None

    try:
        total = len(doc)
        limit = min(total, max_pages or total)
        cut = limit
        for i in range(limit):
            try:
                txt = doc[i].get_text("text") or ""
            except Exception:
                txt = ""
            if _page_contains_stop_heading(txt):
                cut = i + 1  # 保留该页，截断从下一页开始
                break

        # 至少保留1页
        keep_to = max(1, cut)
        if keep_to >= total:
            # 无需裁剪
            out_path = None
        else:
            out_path = str(Path(src_pdf).with_suffix("") ) + ".trimmed.pdf"
            newdoc = fitz.open()
            newdoc.insert_pdf(doc, from_page=0, to_page=keep_to - 1)
            newdoc.save(out_path)
            newdoc.close()
        doc.close()
        return out_path or src_pdf
    except Exception:
        try:
            doc.close()
        except Exception:
            pass
        return None


def _mineru_request_headers(token: Optional[str] = None) -> Dict[str, str]:
    tok = token or MINERU_API_TOKEN
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {tok}",
    }


# 简易令牌桶/滑动窗口频控（不足量级但足够保护6-8篇/批的场景）
from collections import deque, defaultdict
_submit_times_map: Dict[str, deque] = defaultdict(deque)
_poll_times_map: Dict[str, deque] = defaultdict(deque)


def _rate_limit(tq: deque, rpm: int) -> None:
    """阻塞式频控：确保过去60秒内调用次数 ≤ rpm。"""
    now = time.time()
    window = 60.0
    while tq and (now - tq[0]) > window:
        tq.popleft()
    if len(tq) >= rpm:
        # 需等待至窗口滚动
        wait = window - (now - tq[0]) + 0.01
        if wait > 0:
            time.sleep(wait)
        # 清理过期
        now = time.time()
        while tq and (now - tq[0]) > window:
            tq.popleft()
    tq.append(time.time())


def _env_bool(v: Optional[str], default: bool = True) -> bool:
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in {"1", "true", "yes", "on"}:
        return True
    if s in {"0", "false", "no", "off"}:
        return False
    return default


def _mineru_session() -> requests.Session:
    """创建MinerU专用会话, 支持显式代理/禁用系统代理/关闭证书校验/自动重试。"""
    from requests.adapters import HTTPAdapter
    try:
        from urllib3.util.retry import Retry
    except Exception:
        Retry = None  # type: ignore

    sess = requests.Session()
    # 代理策略
    if _env_bool(MINERU_TRUST_ENV, False):
        sess.trust_env = True
    else:
        sess.trust_env = False
    if MINERU_PROXIES:
        sess.proxies = {"http": MINERU_PROXIES, "https": MINERU_PROXIES}
    # 证书校验
    # 重试
    if Retry is not None:
        # 兼容 urllib3 1.x / 2.x 的参数名
        kwargs = {
            "total": 5,
            "connect": 5,
            "read": 5,
            "backoff_factor": 0.6,
            "status_forcelist": [429, 502, 503, 504],
        }
        try:
            retry = Retry(allowed_methods={"GET", "POST", "PUT"}, **kwargs)  # urllib3>=1.26
        except TypeError:
            retry = Retry(method_whitelist={"GET", "POST", "PUT"}, **kwargs)  # 旧版命名
        adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=16)
        sess.mount("http://", adapter)
        sess.mount("https://", adapter)
    return sess


def _mineru_batch_upload(files: List[Dict[str, str]], model_version: str = None, token: Optional[str] = None) -> Optional[Tuple[str, List[str]]]:
    """申请批量上传URL并返回 (batch_id, file_urls)。files: [{name, path, data_id}]"""
    try:
        sess = _mineru_session()
        # 频控：提交接口（300次/分钟）
        t = (token or MINERU_API_TOKEN) or "default"
        _rate_limit(_submit_times_map[t], MINERU_SUBMIT_RPM)
        url = f"{MINERU_BASE_URL}/api/v4/file-urls/batch"
        payload = {
            "files": [{"name": f["name"], "data_id": f.get("data_id") or f["name"]} for f in files],
            "model_version": (model_version or MINERU_MODEL_VERSION) or "vlm",
        }
        r = sess.post(url, headers=_mineru_request_headers(token), json=payload, timeout=MINERU_TIMEOUT)
        r.raise_for_status()
        j = r.json()
        if j.get("code") != 0:
            print(f"[MinerU] 申请上传URL失败: {j}")
            return None
        data = j.get("data") or {}
        batch_id = data.get("batch_id")
        urls = data.get("file_urls") or []
        if not (batch_id and urls and len(urls) == len(files)):
            print("[MinerU] 返回的URL数量不匹配")
            return None
        # 执行上传
        for i, u in enumerate(urls):
            fp = files[i]["path"]
            with open(fp, "rb") as f:
                # 上传本身不在频控范围，但算作本次提交链路的一部分
                put = sess.put(u, data=f, timeout=max(MINERU_TIMEOUT, 120))
                if put.status_code != 200:
                    print(f"[MinerU] 上传失败: {files[i]['name']} status={put.status_code}")
                    return None
        return batch_id, urls
    except Exception as e:
        print(f"[MinerU] 批量上传异常: {e}")
        return None


def _mineru_poll_batch_results(batch_id: str, timeout_sec: int = 900, poll_interval: int = 5, token: Optional[str] = None) -> Optional[List[Dict]]:
    """轮询批量结果直到全部完成或超时。返回 extract_result 列表。"""
    url = f"{MINERU_BASE_URL}/api/v4/extract-results/batch/{batch_id}"
    headers = _mineru_request_headers(token)
    sess = _mineru_session()
    deadline = time.time() + timeout_sec
    last_state = None
    while time.time() < deadline:
        try:
            # 频控：查询接口（1000次/分钟）
            t = (token or MINERU_API_TOKEN) or "default"
            _rate_limit(_poll_times_map[t], MINERU_POLL_RPM)
            r = sess.get(url, headers=headers, timeout=MINERU_TIMEOUT)
            r.raise_for_status()
            j = r.json()
            if j.get("code") != 0:
                print(f"[MinerU] 结果查询失败: {j}")
                time.sleep(poll_interval)
                continue
            data = j.get("data") or {}
            results = data.get("extract_result") or []
            states = [it.get("state") for it in results]
            last_state = states
            if results and all(s in ("done", "failed") for s in states):
                return results
        except Exception as e:
            print(f"[MinerU] 轮询异常: {e}")
        time.sleep(poll_interval)
    print(f"[MinerU] 轮询超时, 最后状态: {last_state}")
    return None


def _mineru_download_zip_and_read_markdown(zip_url: str) -> Optional[str]:
    """下载 MinerU 结果zip并提取首个Markdown内容（流式 + 多次重试，使用MinerU会话配置）。"""
    import zipfile, io
    sess = _mineru_session()
    headers = {"User-Agent": HEADERS.get("User-Agent", "Mozilla/5.0"), "Accept": "*/*"}
    attempts = 0
    while attempts < 5:
        attempts += 1
        try:
            with sess.get(zip_url, headers=headers, timeout=max(MINERU_TIMEOUT, 120), stream=True) as r:
                r.raise_for_status()
                buf = io.BytesIO()
                for chunk in r.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        buf.write(chunk)
                data = buf.getvalue()
            # 校验ZIP头
            if not data.startswith(b"PK\x03\x04"):
                # 再尝试一次非流式直接下载
                r2 = sess.get(zip_url, headers=headers, timeout=max(MINERU_TIMEOUT, 120))
                r2.raise_for_status()
                data = r2.content
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                md_names = [n for n in zf.namelist() if n.lower().endswith('.md')]
                if not md_names:
                    return None
                md_name = sorted(md_names, key=lambda s: (s.count('/'), len(s)))[0]
                with zf.open(md_name) as mf:
                    txt = mf.read().decode('utf-8', errors='ignore')
                    return txt
        except Exception as e:
            if attempts >= 5:
                print(f"[MinerU] 下载/解压失败: {e}")
                return None
            time.sleep(1.0 * attempts)


def _convert_pdf_with_mineru_api(
    input_pdf: str,
    output_md: str,
    keep_sections: Optional[List[str]] = None,
    stop_after: Optional[List[str]] = None,
    max_pages: Optional[int] = None,
    mineru_token: Optional[str] = None,
) -> bool:
    """使用 MinerU API 将PDF解析为Markdown。

    - 先用 PyMuPDF 裁剪：遇到章节级停止标题所在页，则仅保留之前页；并遵守 max_pages 限制。
    - 通过 file-urls/batch 申请上传链接并PUT上传；随后轮询 batch 结果，下载zip并读取Markdown。
    - 不做任何章节/标题/噪声微调；仅做页面级截断。
    """
    if not _mineru_api_available():
        return False
    try:
        t0 = time.perf_counter()
        # 页面级裁剪
        t_trim0 = time.perf_counter()
        trimmed = _trim_pdf_to_subject_pages(input_pdf, max_pages=max_pages, stop_after=stop_after)
        t_trim1 = time.perf_counter()
        if not trimmed:
            return False
        name = Path(trimmed).name
        data_id = Path(output_md).with_suffix("").name
        files = [{"name": name, "path": trimmed, "data_id": data_id}]
        # 上传
        t_up0 = time.perf_counter()
        got = _mineru_batch_upload(files, model_version=MINERU_MODEL_VERSION, token=mineru_token)
        t_up1 = time.perf_counter()
        if not got:
            return False
        batch_id, _ = got
        # 轮询
        t_poll0 = time.perf_counter()
        results = _mineru_poll_batch_results(batch_id, token=mineru_token)
        t_poll1 = time.perf_counter()
        if not results:
            return False
        # 定位当前文件
        target = None
        for it in results:
            if it.get("file_name") == name or it.get("data_id") == data_id:
                target = it
                break
        if not target:
            # 回退：取第一个完成的结果
            target = next((it for it in results if it.get("state") == "done"), None)
        if not target or target.get("state") != "done":
            print(f"[MinerU] 解析失败: {target}")
            return False
        zip_url = target.get("full_zip_url")
        if not zip_url:
            print("[MinerU] 缺少full_zip_url")
            return False
        # 下载
        t_dl0 = time.perf_counter()
        md_txt = _mineru_download_zip_and_read_markdown(zip_url)
        t_dl1 = time.perf_counter()
        if not (md_txt and md_txt.strip()):
            return False
        # 写出
        t_wr0 = time.perf_counter()
        Path(output_md).parent.mkdir(parents=True, exist_ok=True)
        Path(output_md).write_text(md_txt, encoding='utf-8')
        t_wr1 = time.perf_counter()
        print("[Convert] PDF转换成功(MinerU API)")
        t1 = time.perf_counter()
        print(
            f"[时间][MinerU] trim={t_trim1 - t_trim0:.2f}s upload={t_up1 - t_up0:.2f}s "
            f"poll={t_poll1 - t_poll0:.2f}s download={t_dl1 - t_dl0:.2f}s write={t_wr1 - t_wr0:.2f}s "
            f"total={t1 - t0:.2f}s"
        )
        return True
    except Exception as e:
        print(f"[MinerU] 单文件转换异常: {e}")
        return False


def _convert_pdfs_with_mineru_api_batch(
    inputs: List[Tuple[str, str]],
    keep_sections: Optional[List[str]] = None,
    stop_after: Optional[List[str]] = None,
    max_pages: Optional[int] = None,
) -> bool:
    """将多份本地PDF通过 MinerU 批量解析为 Markdown。

    inputs: [(input_pdf, output_md), ...]
    """
    if not _mineru_api_available() or not inputs:
        return False
    try:
        t0 = time.perf_counter()
        # 预裁剪并准备批量上传
        files: List[Dict[str, str]] = []
        for inp, outp in inputs:
            trimmed = _trim_pdf_to_subject_pages(inp, max_pages=max_pages, stop_after=stop_after) or inp
            files.append({
                "name": Path(trimmed).name,
                "path": trimmed,
                "data_id": Path(outp).with_suffix("").name,
            })
        t_up0 = time.perf_counter()
        got = _mineru_batch_upload(files, model_version=MINERU_MODEL_VERSION)
        t_up1 = time.perf_counter()
        if not got:
            return False
        batch_id, _ = got
        t_poll0 = time.perf_counter()
        results = _mineru_poll_batch_results(batch_id)
        t_poll1 = time.perf_counter()
        if not results:
            return False
        # 映射：data_id / file_name → result
        idx: Dict[str, Dict] = {}
        for it in results:
            if it.get("data_id"):
                idx[str(it.get("data_id"))] = it
            if it.get("file_name"):
                idx[str(it.get("file_name"))] = it
        ok_any = False
        t_dl_sum = 0.0
        for inp, outp in inputs:
            key1 = Path(outp).with_suffix("").name
            key2 = Path(inp).name
            target = idx.get(key1) or idx.get(key2)
            if not target or target.get("state") != "done":
                print(f"[MinerU] 批量项失败: {outp}")
                continue
            zip_url = target.get("full_zip_url")
            t_dl0 = time.perf_counter()
            md_txt = _mineru_download_zip_and_read_markdown(zip_url) if zip_url else None
            t_dl1 = time.perf_counter()
            t_dl_sum += max(0.0, (t_dl1 - t_dl0))
            if not (md_txt and md_txt.strip()):
                print(f"[MinerU] 批量项空Markdown: {outp}")
                continue
            Path(outp).parent.mkdir(parents=True, exist_ok=True)
            Path(outp).write_text(md_txt, encoding='utf-8')
            ok_any = True
        t1 = time.perf_counter()
        print(
            f"[时间][MinerU-Batch] upload={t_up1 - t_up0:.2f}s poll={t_poll1 - t_poll0:.2f}s "
            f"download_total={t_dl_sum:.2f}s total={t1 - t0:.2f}s"
        )
        return ok_any
    except Exception as e:
        print(f"[MinerU] 批量转换异常: {e}")
        return False


def _convert_xml_with_pandoc(
    input_xml: str,
    output_md: str,
    keep_sections: Optional[List[str]] = None,
    stop_after: Optional[List[str]] = None,
) -> bool:
    """使用 Pandoc 将JATS(XML)转换为Markdown（不使用Lua过滤），支持可选的H1/H2标题级截断。"""
    t0 = time.perf_counter()
    cmd = [
        "pandoc",
        str(input_xml),
        "-f",
        "jats",
        "-t",
        "gfm",
        "--wrap=none",
        "-o",
        str(output_md),
    ]
    try:
        Path(output_md).parent.mkdir(parents=True, exist_ok=True)
        import subprocess
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[Convert] Pandoc转换成功: {output_md}")
        # 若缺少题目/作者/摘要，则从XML补全到文首
        try:
            txt0 = Path(output_md).read_text(encoding='utf-8')
            need_title_block = not txt0.lstrip().startswith('# ')
            need_abstract_block = ('\n## Abstract\n' not in txt0[:4000])
            if need_title_block or need_abstract_block:
                front = _build_front_md_from_xml(input_xml)
                if front:
                    Path(output_md).write_text(front + txt0, encoding='utf-8')
                    txt0 = front + txt0
        except Exception:
            pass
        # 可选：对H1/H2标题做截断（默认启用，可通过环境变量关闭）
        try:
            if os.getenv('PANDOC_HEADING_TRIM', '1').lower() in ('1','true','yes','on'):
                txt = Path(output_md).read_text(encoding='utf-8')
                trimmed = _trim_markdown_by_heading_levels(
                    txt,
                    stop_keywords=stop_after or DEFAULT_STOP_AFTER,
                    levels=(1,2)
                )
                if trimmed is not None:
                    Path(output_md).write_text(trimmed, encoding='utf-8')
        except Exception:
            pass
        t1 = time.perf_counter()
        print(f"[时间][XML] Pandoc total={t1 - t0:.2f}s")
        return True
    except FileNotFoundError:
        print("[Convert] 未检测到pandoc, 回退到MarkItDown")
        return False
    except Exception as e:
        print(f"[Convert] Pandoc失败: {e}")
        return False


## 已屏蔽的章节抽取函数(_assemble_markdown_sections_from_lines)已移除，以保持逻辑精简


def _ocr_pdf_to_markdown(
    pdf_path: str,
    md_path: str,
    *,
    lang: str = "en",
    dpi: int = 180,
    max_pages: Optional[int] = 20,
    stop_after: Optional[List[str]] = None,
    wanted_sections: Optional[List[str]] = None,
    use_pp_structure: bool = True,
    render_threads: Optional[int] = None,
) -> bool:
    """使用PaddleOCR(+PP-Structure)对PDF执行OCR，仅保留“页面级裁剪”，不做章节/标题/噪声微调。"""
    t0 = time.perf_counter()
    if not (PADDLE_AVAILABLE and Fitz and Image):
        return False

    try:
        ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        pp = None
        if use_pp_structure and PPSTRUCT_AVAILABLE:
            try:
                pp = PPStructure(layout=True, show_log=False)
            except Exception:
                pp = None

        # 页面级裁剪（保留出现停止标题的那一页）
        src_pdf = _trim_pdf_to_subject_pages(pdf_path, max_pages=max_pages, stop_after=stop_after) or pdf_path
        doc = Fitz.open(src_pdf)
        total_pages = len(doc)
        limit = total_pages

        # 小规模线程页预渲染（OCR仍单实例串行）
        def _render(idx: int):
            d = Fitz.open(src_pdf)
            try:
                page = d[idx]
                zoom = dpi / 72.0
                mat = Fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                from io import BytesIO
                img_bytes = pix.tobytes("png")
                return idx, Image.open(BytesIO(img_bytes)).convert("RGB")
            finally:
                d.close()

        if render_threads:
            threads = max(1, render_threads)
        else:
            try:
                cpu = os.cpu_count() or 8
                threads = max(4, min(8, cpu))
            except Exception:
                threads = 4

        rendered: Dict[int, "PIL.Image.Image"] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as ex:
            for idx, im in ex.map(_render, range(limit)):
                rendered[idx] = im

        # 资产目录: {stem}_assets
        stem = Path(md_path).with_suffix("").name
        assets_dir_path = Path(md_path).parent / f"{stem}_assets"
        assets_dir_path.mkdir(parents=True, exist_ok=True)

        md_parts: List[str] = []
        for page_idx in range(limit):
            # 取预渲染图像，兜底单页渲染
            im = rendered.get(page_idx)
            if im is None:
                _, im = _render(page_idx)
            img_np = np.array(im) if np is not None else None

            page_lines: List[str] = []

            if pp is not None and img_np is not None:
                # PP-Structure版面/表格检测
                try:
                    res = pp(img_np)
                    tcount = 0
                    fcount = 0
                    for block in res:
                        btype = str(block.get("type", "")).lower()
                        box = block.get("bbox") or block.get("box")
                        if btype in ("table", "figure") and box:
                            # 裁剪并保存为占位图
                            x1, y1, x2, y2 = map(int, box)
                            crop = im.crop((x1, y1, x2, y2))
                            if btype == "table":
                                tcount += 1
                                img_name = f"page{page_idx+1}_table{tcount}.png"
                            else:
                                fcount += 1
                                img_name = f"page{page_idx+1}_figure{fcount}.png"
                            out_path = assets_dir_path / img_name
                            crop.save(out_path)
                            page_lines.append(f"![{btype}]({assets_dir_path.name}/{img_name})")
                        else:
                            ocr_res = block.get("res")
                            if isinstance(ocr_res, list):
                                for item in ocr_res:
                                    txt = item.get("text")
                                    if txt:
                                        page_lines.append(txt.strip())
                except Exception:
                    pp = None  # 失败后禁用, 退回整页OCR

            if pp is None:
                # 整页OCR
                try:
                    result = ocr.ocr(img_np if img_np is not None else im, cls=True)
                    items: List[Tuple[float, str]] = []
                    if result and result[0]:
                        for det in result[0]:
                            try:
                                box, (txt, conf) = det
                                if not txt or not isinstance(txt, str):
                                    continue
                                xs = [p[0] for p in box]; ys = [p[1] for p in box]
                                y_avg = sum(ys) / 4.0
                                items.append((y_avg, txt.strip()))
                            except Exception:
                                continue
                    items.sort(key=lambda x: x[0])
                    page_lines.extend([t for _, t in items if t])
                except Exception as e:
                    print(f"[OCR] 第{page_idx+1}页失败: {e}")
            md_parts.append(f"## Page {page_idx+1}\n\n")
            if page_lines:
                md_parts.append("\n".join(page_lines).strip() + "\n\n")

        out_md = "".join(md_parts)
        if not out_md.strip():
            return False

        Path(md_path).parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(out_md)
        print(f"[Convert] PDF转换成功(PaddleOCR)")
        t1 = time.perf_counter()
        print(f"[时间][PDF] OCR total={t1 - t0:.2f}s dpi={dpi} pages={limit}")
        return True

    except Exception as e:
        print(f"[OCR] 处理失败: {e}")
        return False


def convert_to_markdown(
    input_path: str,
    output_path: str,
    *,
    prefer_ocr: bool = True,
    use_pymupdf4llm: bool = False,
    wanted_sections: Optional[List[str]] = None,
    ocr_lang: str = "en",
    dpi: int = 180,
    max_pages: Optional[int] = 20,
    stop_after: Optional[List[str]] = None,
    use_pp_structure: bool = True,
    mineru_token: Optional[str] = None,
    render_threads: Optional[int] = None,
) -> bool:
    """根据文件类型选择最优转换路径（禁用章节/标题微调；仅对PDF执行页面级裁剪）。

    限制重试: 最多尝试3次不同转换路径, 避免无限循环。
    """
    print(f"[Convert] 转换文件: {input_path} → {output_path}")

    ext = Path(input_path).suffix.lower()
    attempts = 0
    MAX_RETRIES = 3

    # PDF: 若配置了 MinerU API Token，优先 MinerU 路线（单文献就绪即提交）
    if ext == ".pdf" and _mineru_api_available():
        t_rt0 = time.perf_counter()
        if attempts < MAX_RETRIES and _convert_pdf_with_mineru_api(
            input_path,
            output_path,
            keep_sections=wanted_sections,
            stop_after=stop_after,
            max_pages=max_pages,
            mineru_token=mineru_token,
        ):
            t_rt1 = time.perf_counter()
            print(f"[时间][Route] MinerU total={t_rt1 - t_rt0:.2f}s")
            return True
        attempts += 1

    # PDF: 尝试 PyMuPDF4LLM
    if ext == ".pdf" and use_pymupdf4llm:
        t_rt0 = time.perf_counter()
        if attempts < MAX_RETRIES and _convert_pdf_with_pymupdf4llm(
            input_path,
            output_path,
            max_pages=max_pages,
        ):
            t_rt1 = time.perf_counter()
            print(f"[时间][Route] PyMuPDF4LLM total={t_rt1 - t_rt0:.2f}s")
            return True
        attempts += 1

    # PDF: 默认优先OCR
    if ext == ".pdf" and prefer_ocr:
        t_rt0 = time.perf_counter()
        if attempts < MAX_RETRIES and _ocr_pdf_to_markdown(
            input_path,
            output_path,
            lang=ocr_lang,
            dpi=dpi,
            max_pages=max_pages,
            stop_after=stop_after,
            wanted_sections=wanted_sections,
            use_pp_structure=use_pp_structure,
            render_threads=render_threads,
        ):
            t_rt1 = time.perf_counter()
            print(f"[时间][Route] OCR total={t_rt1 - t_rt0:.2f}s")
            return True
        attempts += 1

    # XML: 默认优先Pandoc
    if ext in (".xml", ".nxml"):
        t_rt0 = time.perf_counter()
        if attempts < MAX_RETRIES and _convert_xml_with_pandoc(
            input_path,
            output_path,
            keep_sections=wanted_sections,
            stop_after=stop_after,
        ):
            t_rt1 = time.perf_counter()
            print(f"[时间][Route] Pandoc total={t_rt1 - t_rt0:.2f}s")
            return True
        attempts += 1

    # MarkItDown尝试
    if attempts < MAX_RETRIES:
        try:
            t_rt0 = time.perf_counter()
            from markitdown import MarkItDown
            md_converter = MarkItDown()
            result = md_converter.convert(input_path)
            if result and result.text_content:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.text_content)
                print(f"[Convert] 转换成功(MarkItDown): {output_path}")
                t_rt1 = time.perf_counter()
                print(f"[时间][Route] MarkItDown total={t_rt1 - t_rt0:.2f}s")
                return True
        except Exception as e:
            print(f"[Convert] MarkItDown失败: {e}")
        finally:
            attempts += 1

    # PDF备用 pdfplumber
    if ext == ".pdf":
        if attempts < MAX_RETRIES:
            try:
                import pdfplumber
                markdown_content: List[str] = []
                with pdfplumber.open(input_path) as pdf:
                    for page_num, page in enumerate(pdf.pages, 1):
                        if max_pages and page_num > max_pages:
                            break
                        text = page.extract_text()
                        if text:
                            markdown_content.append(f"## Page {page_num}\n\n{text}\n\n")
                if markdown_content:
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write("".join(markdown_content))
                    print(f"[Convert] PDF转换成功(pdfplumber)")
                    # pdfplumber 路线时长不精确（逐页提取），此处不再额外统计
                    return True
            except Exception as e:
                print(f"[Convert] pdfplumber失败: {e}")
            finally:
                attempts += 1

        # 最终兜底再尝试一次OCR
        if attempts < MAX_RETRIES and _ocr_pdf_to_markdown(
            input_path,
            output_path,
            lang=ocr_lang,
            dpi=dpi,
            max_pages=max_pages,
            stop_after=stop_after,
            wanted_sections=wanted_sections,
            use_pp_structure=use_pp_structure,
            render_threads=render_threads,
        ):
            return True
        attempts += 1

    # XML回退: BeautifulSoup
    if attempts < MAX_RETRIES and ext in (".xml", ".nxml"):
        return _fallback_convert(input_path, output_path)

    # 其他格式回退
    if attempts < MAX_RETRIES:
        return _fallback_convert(input_path, output_path)
    return False


def _fallback_convert(input_path: str, output_path: str) -> bool:
    """备用转换方法(使用pdfplumber/python-docx/BeautifulSoup)"""
    ext = Path(input_path).suffix.lower()

    try:
        if ext == '.pdf':
            # 使用pdfplumber
            import pdfplumber
            markdown_content = []

            with pdfplumber.open(input_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        markdown_content.append(f"## Page {page_num}\n\n{text}\n\n")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("".join(markdown_content))

            print(f"[Convert] PDF转换成功(pdfplumber)")
            return True

        elif ext == '.xml' or ext == '.nxml':
            # 使用BeautifulSoup解析XML
            from bs4 import BeautifulSoup

            with open(input_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'xml')

            # 提取标题、摘要、正文
            markdown_parts = []

            title = soup.find('article-title')
            if title:
                markdown_parts.append(f"# {title.get_text()}\n\n")

            abstract = soup.find('abstract')
            if abstract:
                markdown_parts.append(f"## Abstract\n\n{abstract.get_text()}\n\n")

            body = soup.find('body')
            if body:
                # 按章节提取
                for sec in body.find_all('sec'):
                    sec_title = sec.find('title')
                    if sec_title:
                        markdown_parts.append(f"## {sec_title.get_text()}\n\n")

                    for p in sec.find_all('p', recursive=False):
                        markdown_parts.append(f"{p.get_text()}\n\n")

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("".join(markdown_parts))

            print(f"[Convert] XML转换成功(BeautifulSoup)")
            return True

        else:
            print(f"[Convert] 不支持的格式: {ext}")
            return False

    except Exception as e:
        print(f"[Convert] 备用转换失败: {e}")
        return False


def download_single_paper(
    doi: Optional[str] = None,
    pmid: Optional[str] = None,
    pmcid: Optional[str] = None,
    url: Optional[str] = None,
    output_dir: str = "papers",
    convert_md: bool = True,
    *,
    prefer_ocr: bool = True,
    use_pymupdf4llm: bool = False,
    wanted_sections: Optional[List[str]] = None,
    ocr_lang: str = "en",
    dpi: int = 180,
    max_pages: Optional[int] = 20,
    stop_after: Optional[List[str]] = None,
    use_pp_structure: bool = True,
    mineru_token: Optional[str] = None,
    render_threads: Optional[int] = None,
) -> bool:
    """
    下载单篇文献并转换为Markdown

    Args:
        doi: 论文DOI
        pmid: PubMed ID
        pmcid: PMC ID (如PMC10594178)
        url: 论文URL
        output_dir: 输出目录
        convert_md: 是否转换为Markdown

    Returns:
        下载是否成功
    """
    identifier = doi or pmid or pmcid or url
    if not identifier:
        info("[错误] 必须提供DOI、PMID、PMCID或URL")
        return False

    safe_name = _safe_stem(doi, pmid, pmcid, url)
    pdf_path = os.path.join(output_dir, f"{safe_name}.pdf")
    xml_path = os.path.join(output_dir, f"{safe_name}.xml")
    md_path = os.path.join(output_dir, f"{safe_name}.md")

    if not convert_md:
        if download_via_scihub(identifier, pdf_path):
            info(f"[成功] PDF已下载: {pdf_path}")
            return True
        pmc_identifier = pmcid or pmid or doi
        if pmc_identifier:
            xml_file = download_via_pmc(pmc_identifier, output_dir)
            if xml_file:
                info(f"[成功] XML已下载: {xml_file}")
                return True
        info(f"[失败] 无法下载: {identifier}")
        return False

    pmc_identifier = pmcid or pmid or doi

    def _pmc_route() -> bool:
        if not pmc_identifier:
            return False
        xml_file = download_via_pmc(pmc_identifier, output_dir)
        if not xml_file:
            return False
        return convert_to_markdown(
            xml_file,
            md_path,
            prefer_ocr=prefer_ocr,
            use_pymupdf4llm=use_pymupdf4llm,
            wanted_sections=wanted_sections,
            ocr_lang=ocr_lang,
            dpi=dpi,
            max_pages=max_pages,
            stop_after=stop_after,
            use_pp_structure=use_pp_structure,
            mineru_token=mineru_token,
            render_threads=render_threads,
        )

    def _scihub_route() -> bool:
        if not download_via_scihub(identifier, pdf_path):
            return False
        return convert_to_markdown(
            pdf_path,
            md_path,
            prefer_ocr=prefer_ocr,
            use_pymupdf4llm=use_pymupdf4llm,
            wanted_sections=wanted_sections,
            ocr_lang=ocr_lang,
            dpi=dpi,
            max_pages=max_pages,
            stop_after=stop_after,
            use_pp_structure=use_pp_structure,
            mineru_token=mineru_token,
            render_threads=render_threads,
        )

    tasks = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        if pmc_identifier:
            tasks.append(executor.submit(_pmc_route))
        tasks.append(executor.submit(_scihub_route))
        for future in concurrent.futures.as_completed(tasks):
            try:
                if future.result():
                    for f in tasks:
                        if f is not future:
                            f.cancel()
                    return True
            except Exception as exc:
                info(f"[警告] 下载任务异常: {exc}")

    info(f"[失败] 无法下载: {identifier}")
    return False

def batch_download(
    input_json: str,
    output_dir: str,
    *,
    prefer_ocr: bool = True,
    use_pymupdf4llm: bool = False,
    wanted_sections: Optional[List[str]] = None,
    ocr_lang: str = "en",
    dpi: int = 180,
    max_pages: Optional[int] = 20,
    stop_after: Optional[List[str]] = None,
    use_pp_structure: bool = True,
    render_threads: Optional[int] = None,
    workers: Optional[int] = None,
    use_doi_index: bool = True,
) -> bool:
    """
    批量下载文献

    Args:
        input_json: 包含论文列表的JSON文件
        output_dir: 输出目录

    Returns:
        是否至少成功下载一篇
    """
    print("=" * 60)
    print("批量文献下载")
    print("=" * 60)

    try:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        with open(input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        papers = data.get("papers", [])
        total = len(papers)

        info(f"[批量] 总计: {total} 篇文献，输出目录: {output_dir}")

        success_count = 0
        failed_papers = []
        success_papers: List[Dict] = []

        # 文献级并行: 自适应4-8个线程（workers=None或'auto'）
        if not workers:
            try:
                cpu = os.cpu_count() or 8
                workers = max(4, min(8, cpu))
            except Exception:
                workers = 4

        if not render_threads:
            try:
                cpu = os.cpu_count() or 8
                render_threads = max(4, min(8, cpu))
            except Exception:
                render_threads = 4

        mineru_tokens = _mineru_tokens()

        # 刷新 DOI 索引（从输出目录下所有JSON提取）
        doi_index: Dict[str, str] = {}
        if use_doi_index:
            doi_index = _refresh_doi_index_from_jsons(Path(output_dir))

        def _process_one(idx_paper):
            i, paper = idx_paper
            p_t0 = time.perf_counter()
            doi = paper.get("doi")
            pmid = paper.get("pmid")
            pmcid = paper.get("pmcid")
            title = paper.get("title", "Unknown")[:60]
            print(f"[{i}/{total}] {title}")
            # 为MinerU分配token（若存在多个token则轮询分配）
            assigned_token = None
            if mineru_tokens:
                assigned_token = mineru_tokens[(i - 1) % len(mineru_tokens)]
            md_stem = _safe_stem(doi, pmid, pmcid, paper.get("url"))
            md_basename = f"{md_stem}.md"
            # 若启用索引且该DOI已存在（并且目标md存在），则跳过实际处理
            nd = _normalize_doi(doi)
            if use_doi_index and nd and nd in doi_index and (Path(output_dir) / doi_index.get(nd, "")).exists():
                md_from_idx = doi_index.get(nd)
                print(f"[Index] 已存在，跳过: {doi} → {md_from_idx}")
                p_t1 = time.perf_counter()
                print(f"[耗时][Paper] {i}/{total} elapsed={p_t1 - p_t0:.2f}s")
                enriched = dict(paper)
                enriched["md_file"] = md_from_idx or md_basename
                _ensure_relevance_score(enriched)
                _ensure_extraction_context(enriched)
                _ensure_reading_report(enriched)
                return (i, title, True, enriched, md_from_idx or md_basename)

            ok = download_single_paper(
                doi=doi,
                pmid=pmid,
                pmcid=pmcid,
                output_dir=output_dir,
                prefer_ocr=prefer_ocr,
                use_pymupdf4llm=use_pymupdf4llm,
                wanted_sections=wanted_sections,
                ocr_lang=ocr_lang,
                dpi=dpi,
                max_pages=max_pages,
                stop_after=stop_after,
                use_pp_structure=use_pp_structure,
                mineru_token=assigned_token,
                render_threads=render_threads,
            )
            p_t1 = time.perf_counter()
            print(f"[耗时][Paper] {i}/{total} elapsed={p_t1 - p_t0:.2f}s")
            return (i, title, ok, paper, md_basename)

        # 线程池(文献级并行)
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            for i, title, ok, paper, md_basename in ex.map(_process_one, list(enumerate(papers, 1))):
                if ok:
                    success_count += 1
                    try:
                        enriched = dict(paper)
                        enriched["md_file"] = md_basename
                    except Exception:
                        enriched = paper
                        try:
                            paper["md_file"] = md_basename
                        except Exception:
                            pass
                    _ensure_relevance_score(enriched)
                    _ensure_extraction_context(enriched)
                    _ensure_reading_report(enriched)
                    success_papers.append(enriched)
                    print(f"  ✓ 成功\n")
                else:
                    failed_papers.append({"title": title, "doi": paper.get("doi")})
                    print(f"  ✗ 失败\n")

        # 摘要
        info(f"[批量] 完成: 成功 {success_count}/{total}, 失败 {len(failed_papers)}")

        # 仅保留成功文献，输出JSON继承自输入文件的全部顶层字段（仅 papers 替换为成功子集）
        try:
            part_name = Path(input_json).stem  # 例如 Results_20251111-0945
            out_json = Path(output_dir) / f"{part_name}.json"
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_payload = {}
            try:
                if isinstance(data, dict):
                    # 复制输入的所有顶层字段
                    out_payload = dict(data)
                else:
                    out_payload = {}
            except Exception:
                out_payload = {}
            # 用成功子集替换 papers
            out_payload["papers"] = success_papers
            # 可选：若存在 meta.total，可尝试同步更新为成功数（不改变字段结构）
            try:
                if isinstance(out_payload.get("meta"), dict) and "total" in out_payload["meta"]:
                    out_payload["meta"]["total"] = len(success_papers)
            except Exception:
                pass
            with open(out_json, 'w', encoding='utf-8') as f:
                json.dump(out_payload, f, indent=2, ensure_ascii=False)
            info(f"[完成] 文献JSON保存在: {out_json}")
        except Exception as e:
            info(f"[警告] 写入文献JSON失败: {e}")

        # 批次结束后刷新并保存 doi 索引
        if use_doi_index:
            try:
                idx_path = Path(output_dir) / 'doi_index'
                _refresh_doi_index_from_jsons(Path(output_dir))
                if DEBUG:
                    info(f"[Index] 已刷新: {idx_path}")
            except Exception as e:
                info(f"[Index] 刷新失败: {e}")

        if failed_papers and DEBUG:
            info("\n失败列表:")
            for paper in failed_papers:
                info(f"  - {paper['title']}")

        return success_count > 0

    except Exception as e:
        info(f"[错误] 批量处理失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="文献下载与转换工具")
    subparsers = parser.add_subparsers(dest="command", required=True)
    parser.add_argument("--debug", action="store_true", help="启用详细日志")

    # 单篇下载
    download_parser = subparsers.add_parser("download", help="下载单篇文献")
    download_parser.add_argument("--doi", help="论文DOI")
    download_parser.add_argument("--pmid", help="PubMed ID")
    download_parser.add_argument("--url", help="论文URL")
    download_parser.add_argument("--output", default="papers", help="输出目录")
    download_parser.add_argument("--no-convert", action="store_true", help="不转换为Markdown")
    download_parser.add_argument("--prefer-ocr", action="store_true", default=True, help="(PDF) 优先使用PaddleOCR仅抽取主体章节")
    download_parser.add_argument("--use-pymupdf4llm", action="store_true", default=True, help="(PDF) 优先使用PyMuPDF4LLM解析")
    download_parser.add_argument("--sections", default=",".join(DEFAULT_SECTIONS), help="仅抽取这些章节, 逗号分隔")
    download_parser.add_argument("--ocr-lang", default="en", help="OCR语言, 默认en")
    download_parser.add_argument("--dpi", type=int, default=180, help="渲染DPI, 默认180")
    download_parser.add_argument("--max-pages", type=int, default=20, help="最大处理页数, 默认20")
    download_parser.add_argument("--stop-after", default=",".join(DEFAULT_STOP_AFTER), help="遇到这些关键字停止, 逗号分隔")
    download_parser.add_argument("--no-pp-structure", action="store_true", help="禁用PP-Structure版面/表格增强")

    # 批量下载
    batch_parser = subparsers.add_parser("batch", help="批量下载文献")
    batch_parser.add_argument("--input", required=True, help="输入JSON文件")
    batch_parser.add_argument("--output", required=True, help="输出目录")
    batch_parser.add_argument("--workers", default="auto", help="文献级并行线程数, auto为4-8自适应")
    batch_parser.add_argument("--render-threads", default="auto", help="PDF页渲染线程数, auto为4-8自适应")
    batch_parser.add_argument("--prefer-ocr", action="store_true", default=True, help="(PDF) 优先使用PaddleOCR仅抽取主体章节")
    batch_parser.add_argument("--use-pymupdf4llm", action="store_true", default=True, help="(PDF) 优先使用PyMuPDF4LLM解析")
    batch_parser.add_argument("--sections", default=",".join(DEFAULT_SECTIONS), help="仅抽取这些章节, 逗号分隔")
    batch_parser.add_argument("--ocr-lang", default="en", help="OCR语言, 默认en")
    batch_parser.add_argument("--dpi", type=int, default=180, help="渲染DPI, 默认180")
    batch_parser.add_argument("--max-pages", type=int, default=20, help="最大处理页数, 默认20")
    batch_parser.add_argument("--stop-after", default=",".join(DEFAULT_STOP_AFTER), help="遇到这些关键字停止, 逗号分隔")
    batch_parser.add_argument("--no-pp-structure", action="store_true", help="禁用PP-Structure版面/表格增强")

    # 转换命令
    convert_parser = subparsers.add_parser("convert", help="转换文件为Markdown")
    convert_parser.add_argument("--input", required=True, help="输入文件")
    convert_parser.add_argument("--output", required=True, help="输出Markdown文件")
    convert_parser.add_argument("--prefer-ocr", action="store_true", default=True, help="(PDF) 优先使用PaddleOCR仅抽取主体章节")
    convert_parser.add_argument("--use-pymupdf4llm", action="store_true", default=True, help="(PDF) 优先使用PyMuPDF4LLM解析")
    convert_parser.add_argument("--sections", default=",".join(DEFAULT_SECTIONS), help="仅抽取这些章节, 逗号分隔")
    convert_parser.add_argument("--ocr-lang", default="en", help="OCR语言, 默认en")
    convert_parser.add_argument("--dpi", type=int, default=180, help="渲染DPI, 默认180")
    convert_parser.add_argument("--max-pages", type=int, default=20, help="最大处理页数, 默认20")
    convert_parser.add_argument("--stop-after", default=",".join(DEFAULT_STOP_AFTER), help="遇到这些关键字停止, 逗号分隔")
    convert_parser.add_argument("--no-pp-structure", action="store_true", help="禁用PP-Structure版面/表格增强")

    args = parser.parse_args()
    global DEBUG
    DEBUG = args.debug

    if args.command == "download":
        # Ensure output directory exists for downloads
        try:
            Path(args.output).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        wanted = [s.strip() for s in (args.sections or "").split(",") if s.strip()]
        stop_list = [s.strip() for s in (args.stop_after or "").split(",") if s.strip()]
        success = download_single_paper(
            doi=args.doi,
            pmid=args.pmid,
            url=args.url,
            output_dir=args.output,
            convert_md=not args.no_convert,
            prefer_ocr=args.prefer_ocr,
            use_pymupdf4llm=args.use_pymupdf4llm,
            wanted_sections=wanted,
            ocr_lang=args.ocr_lang,
            dpi=args.dpi,
            max_pages=args.max_pages,
            stop_after=stop_list,
            use_pp_structure=(not args.no_pp_structure),
        )
    elif args.command == "batch":
        # Ensure output directory exists for batch
        try:
            Path(args.output).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        wanted = [s.strip() for s in (args.sections or "").split(",") if s.strip()]
        stop_list = [s.strip() for s in (args.stop_after or "").split(",") if s.strip()]
        # 解析并行参数
        rt = args.render_threads
        try:
            rt_val = int(rt)
        except Exception:
            rt_val = None
        wk = args.workers
        try:
            wk_val = int(wk)
        except Exception:
            wk_val = None
        success = batch_download(
            args.input,
            args.output,
            prefer_ocr=args.prefer_ocr,
            use_pymupdf4llm=args.use_pymupdf4llm,
            wanted_sections=wanted,
            ocr_lang=args.ocr_lang,
            dpi=args.dpi,
            max_pages=args.max_pages,
            stop_after=stop_list,
            use_pp_structure=(not args.no_pp_structure),
            render_threads=rt_val,
            workers=wk_val,
        )
    elif args.command == "convert":
        wanted = [s.strip() for s in (args.sections or "").split(",") if s.strip()]
        stop_list = [s.strip() for s in (args.stop_after or "").split(",") if s.strip()]
        success = convert_to_markdown(
            args.input,
            args.output,
            prefer_ocr=args.prefer_ocr,
            use_pymupdf4llm=args.use_pymupdf4llm,
            wanted_sections=wanted,
            ocr_lang=args.ocr_lang,
            dpi=args.dpi,
            max_pages=args.max_pages,
            stop_after=stop_list,
            use_pp_structure=(not args.no_pp_structure),
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
