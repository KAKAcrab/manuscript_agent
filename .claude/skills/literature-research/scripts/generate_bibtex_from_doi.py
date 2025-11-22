#!/usr/bin/env python3
"""
根据references.json中的DOI，使用citation-js生成BibTeX文件
保存到literature/citations/目录，命名格式为"doi.bib"
例如: "10.1038/s41587-023-02060-8.bib"

BibTeX格式可以被EndNote、Zotero、Mendeley等文献管理工具导入

依赖:
- Node.js和npm
- citation-js: npm install citation-js

使用:
  python3 generate_bibtex_from_doi.py --references /path/to/references.json --output /path/to/literature/citations
"""

import json
import subprocess
import argparse
from pathlib import Path
import sys

def sanitize_filename(doi):
    """将DOI转换为安全的文件名"""
    filename = doi.replace('/', '-')
    filename = filename.replace('\\', '-')
    filename = ''.join(c for c in filename if c.isalnum() or c in '.-_')
    return filename

def check_citation_js():
    """检查citation-js是否可用"""
    try:
        result = subprocess.run(
            ['npx', 'citation-js', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def fetch_and_convert_doi(doi, output_path):
    """
    使用citation-js从DOI获取元数据并转换为BibTeX格式

    命令: npx citation-js -t "DOI" -f string -s bibtex
    """
    try:
        # 构建citation-js命令
        cmd = [
            'npx', 'citation-js',
            '-t', doi,
            '-f', 'string',
            '-s', 'bibtex'
        ]

        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout:
            # 保存BibTeX内容到文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            return True, "Success"
        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            return False, f"citation-js failed: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, "Timeout: citation-js took too long"
    except Exception as e:
        return False, f"Error: {str(e)}"

def generate_bibtex_fallback(doi, citation_data, output_path):
    """
    当citation-js失败时，使用文献数据手动生成基本的BibTeX格式
    """
    # 提取第一作者姓氏
    authors_str = citation_data.get('authors', 'Unknown')
    first_author = authors_str.split(',')[0].strip()
    last_name = first_author.split()[-1] if first_author else "Unknown"

    # 生成cite key
    year = citation_data.get('year', '')
    title_words = citation_data.get('title', '').split()
    first_word = title_words[0] if title_words else "Article"
    cite_key = f"{last_name}{year}{first_word}"

    # 清理字段中的特殊字符
    def clean_field(text):
        if not text:
            return ""
        return text.replace('{', '').replace('}', '').replace('\\', '')

    bibtex_content = f"""@article{{{cite_key},
    author = {{{clean_field(citation_data.get('authors', 'Unknown'))}}},
    title = {{{clean_field(citation_data.get('title', 'Unknown'))}}},
    journal = {{{clean_field(citation_data.get('journal', 'Unknown'))}}},
    year = {{{citation_data.get('year', '')}}},
    volume = {{{citation_data.get('volume', '')}}},
    number = {{{citation_data.get('issue', '')}}},
    pages = {{{citation_data.get('pages', '')}}},
    doi = {{{doi}}}
}}
"""

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(bibtex_content)
        return True
    except Exception as e:
        print(f"  ❌ Fallback failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Generate BibTeX files from DOIs using citation.js'
    )
    parser.add_argument(
        '--references',
        type=str,
        required=True,
        help='Path to references.json file'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Output directory for BibTeX files (e.g., literature/citations)'
    )
    parser.add_argument(
        '--fallback',
        action='store_true',
        help='Use fallback BibTeX generation when citation-js is not available'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("使用citation-js生成BibTeX文件")
    print("=" * 70)

    # 检查citation-js
    print("\n步骤1: 检查citation-js...")
    has_citation_js = check_citation_js()

    if has_citation_js:
        print("✓ citation-js可用 (通过npx)")
    else:
        print("⚠️  citation-js不可用")
        if args.fallback:
            print("✓ 将使用fallback方式生成基本BibTeX格式")
        else:
            print("\n请确保已安装Node.js和citation-js:")
            print("  npm install citation-js")
            print("\n或使用 --fallback 选项生成基本BibTeX格式")
            sys.exit(1)

    # 加载references.json
    print("\n步骤2: 加载references.json...")
    references_path = Path(args.references)

    if not references_path.exists():
        print(f"❌ 文件不存在: {references_path}")
        sys.exit(1)

    with open(references_path, 'r', encoding='utf-8') as f:
        ref_data = json.load(f)

    citations = ref_data.get('citations', [])
    print(f"✓ 已加载 {len(citations)} 条引用")

    # 筛选有DOI的引用
    citations_with_doi = [c for c in citations if c.get('doi')]
    print(f"✓ 其中有DOI: {len(citations_with_doi)} 条")

    if not citations_with_doi:
        print("\n⚠️  没有找到任何有DOI的引用")
        sys.exit(0)

    # 创建输出目录
    print("\n步骤3: 创建输出目录...")
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ 输出目录: {output_dir}")

    # 生成BibTeX文件
    print("\n步骤4: 生成BibTeX文件...")

    success_count = 0
    fallback_count = 0
    failed_count = 0

    for citation in citations_with_doi:
        doi = citation['doi']
        filename = sanitize_filename(doi) + '.bib'
        output_path = output_dir / filename

        print(f"\n  处理: {doi}")
        print(f"    [{citation.get('id')}] {citation.get('harvard_cite', 'Unknown')}")

        if has_citation_js and not args.fallback:
            # 使用citation-js
            success, message = fetch_and_convert_doi(doi, output_path)

            if success:
                print(f"    ✓ 已生成: {filename}")
                success_count += 1
            else:
                print(f"    ⚠️  citation-js失败: {message[:80]}")
                # 尝试fallback
                if generate_bibtex_fallback(doi, citation, output_path):
                    print(f"    ✓ 已使用fallback生成: {filename}")
                    fallback_count += 1
                else:
                    failed_count += 1
        else:
            # 使用fallback
            if generate_bibtex_fallback(doi, citation, output_path):
                print(f"    ✓ 已生成(fallback): {filename}")
                fallback_count += 1
            else:
                failed_count += 1

    # 统计报告
    print("\n" + "=" * 70)
    print("生成完成！")
    print("=" * 70)
    print(f"\n统计:")
    print(f"  总DOI数: {len(citations_with_doi)}")
    print(f"  成功(citation-js): {success_count}")
    print(f"  成功(fallback): {fallback_count}")
    print(f"  失败: {failed_count}")
    print(f"\n输出目录: {output_dir}")

    if success_count + fallback_count > 0:
        print(f"\n✓ 已生成 {success_count + fallback_count} 个BibTeX文件")
        print(f"  可使用EndNote、Zotero、Mendeley等文献管理工具导入")

        # 列出生成的文件
        bib_files = list(output_dir.glob('*.bib'))
        print(f"\n生成的BibTeX文件示例:")
        for bib_file in bib_files[:5]:
            print(f"  - {bib_file.name}")

if __name__ == '__main__':
    main()
