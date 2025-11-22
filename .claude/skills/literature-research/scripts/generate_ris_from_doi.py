#!/usr/bin/env python3
"""
根据references.json中的DOI，使用citation.js生成RIS文件
保存到literature/citations/目录，命名格式为"doi.ris"
例如: "10.1038/s41587-023-02060-8.ris"

依赖:
- Node.js和npm
- citation-js: npm install -g citation-js

使用:
  python3 generate_ris_from_doi.py --references /path/to/references.json --output /path/to/literature/citations
"""

import json
import subprocess
import argparse
from pathlib import Path
import sys

def sanitize_filename(doi):
    """将DOI转换为安全的文件名"""
    # 替换/为-，移除其他特殊字符
    filename = doi.replace('/', '-')
    filename = filename.replace('\\', '-')
    # 确保不包含其他非法字符
    filename = ''.join(c for c in filename if c.isalnum() or c in '.-_')
    return filename

def check_citation_js():
    """检查citation-js是否已安装"""
    try:
        result = subprocess.run(
            ['citation-js', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def fetch_and_convert_doi(doi, output_path):
    """
    使用citation-js从DOI获取元数据并转换为RIS格式

    命令: citation-js --input "doi:10.1234/example" --output ris
    """
    try:
        # 构建citation-js命令
        cmd = [
            'citation-js',
            '--input', f'doi:{doi}',
            '--output', 'ris'
        ]

        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 and result.stdout:
            # 保存RIS内容到文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            return True, result.stdout
        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            return False, f"citation-js failed: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, "Timeout: citation-js took too long"
    except Exception as e:
        return False, f"Error: {str(e)}"

def generate_ris_fallback(doi, citation_data, output_path):
    """
    当citation-js失败时，使用文献数据手动生成基本的RIS格式
    """
    ris_content = f"""TY  - JOUR
DO  - {doi}
AU  - {citation_data.get('authors', 'Unknown')}
TI  - {citation_data.get('title', 'Unknown')}
JO  - {citation_data.get('journal', 'Unknown')}
PY  - {citation_data.get('year', '')}
VL  - {citation_data.get('volume', '')}
IS  - {citation_data.get('issue', '')}
SP  - {citation_data.get('pages', '').split('-')[0] if citation_data.get('pages') else ''}
EP  - {citation_data.get('pages', '').split('-')[1] if '-' in citation_data.get('pages', '') else ''}
ER  -
"""

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ris_content)
        return True
    except Exception as e:
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Generate RIS files from DOIs using citation.js'
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
        help='Output directory for RIS files (e.g., literature/citations)'
    )
    parser.add_argument(
        '--fallback',
        action='store_true',
        help='Use fallback RIS generation when citation-js is not available'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("使用citation.js生成RIS文件")
    print("=" * 70)

    # 检查citation-js
    print("\n步骤1: 检查citation-js...")
    has_citation_js = check_citation_js()

    if has_citation_js:
        print("✓ citation-js已安装")
    else:
        print("⚠️  citation-js未安装")
        if args.fallback:
            print("✓ 将使用fallback方式生成基本RIS格式")
        else:
            print("\n请安装citation-js:")
            print("  npm install -g citation-js")
            print("\n或使用 --fallback 选项生成基本RIS格式")
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
        print("   请先运行 enrich_references_with_doi.py 补全DOI")
        sys.exit(0)

    # 创建输出目录
    print("\n步骤3: 创建输出目录...")
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ 输出目录: {output_dir}")

    # 生成RIS文件
    print("\n步骤4: 生成RIS文件...")

    success_count = 0
    fallback_count = 0
    failed_count = 0

    for citation in citations_with_doi:
        doi = citation['doi']
        filename = sanitize_filename(doi) + '.ris'
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
                print(f"    ⚠️  citation-js失败: {message}")
                # 尝试fallback
                if generate_ris_fallback(doi, citation, output_path):
                    print(f"    ✓ 已使用fallback生成: {filename}")
                    fallback_count += 1
                else:
                    print(f"    ❌ fallback也失败")
                    failed_count += 1
        else:
            # 使用fallback
            if generate_ris_fallback(doi, citation, output_path):
                print(f"    ✓ 已生成(fallback): {filename}")
                fallback_count += 1
            else:
                print(f"    ❌ 生成失败")
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
        print(f"\n✓ 已生成 {success_count + fallback_count} 个RIS文件")
        print(f"  可使用EndNote、Zotero等文献管理工具导入")

        # 列出生成的文件
        ris_files = list(output_dir.glob('*.ris'))
        print(f"\n生成的RIS文件示例:")
        for ris_file in ris_files[:5]:
            print(f"  - {ris_file.name}")

if __name__ == '__main__':
    main()
