#!/usr/bin/env python3
"""
JATS XML to Markdown Converter
Converts JATS (Journal Article Tag Suite) XML format to clean Markdown.
Specifically designed for PMC OA articles.
"""

import xml.etree.ElementTree as ET
import re
import argparse
from pathlib import Path


def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def extract_title(root):
    """Extract article title"""
    title_elem = root.find('.//article-title')
    if title_elem is not None:
        return clean_text(title_elem.text or '')
    return ""


def extract_authors(root):
    """Extract author list"""
    authors = []
    for contrib in root.findall('.//contrib[@contrib-type="author"]'):
        surname = contrib.find('.//surname')
        given_names = contrib.find('.//given-names')

        if surname is not None:
            author = clean_text(surname.text or '')
            if given_names is not None:
                author = f"{clean_text(given_names.text or '')} {author}"
            authors.append(author)

    return authors


def extract_abstract(root):
    """Extract abstract content"""
    abstract_elem = root.find('.//abstract')
    if abstract_elem is None:
        return ""

    # Get all text from abstract, handling paragraphs
    abstract_text = []
    for p in abstract_elem.findall('.//p'):
        text = ''.join(p.itertext())
        abstract_text.append(clean_text(text))

    return '\n\n'.join(abstract_text)


def extract_section(section_elem, level=2):
    """Recursively extract section content with proper markdown formatting"""
    if section_elem is None:
        return ""

    content = []

    # Get section title
    title_elem = section_elem.find('./title')
    if title_elem is not None:
        title_text = clean_text(''.join(title_elem.itertext()))
        if title_text:
            content.append(f"\n{'#' * level} {title_text}\n")

    # Get all direct paragraphs (not from subsections)
    for p in section_elem.findall('./p'):
        text = ''.join(p.itertext())
        content.append(clean_text(text))
        content.append("\n")

    # Get all direct tables
    for table in section_elem.findall('./table-wrap'):
        caption = table.find('.//caption')
        if caption is not None:
            cap_text = clean_text(''.join(caption.itertext()))
            content.append(f"\n**{cap_text}**\n")

    # Get all direct figures
    for fig in section_elem.findall('./fig'):
        caption = fig.find('.//caption')
        if caption is not None:
            cap_text = clean_text(''.join(caption.itertext()))
            content.append(f"\n*{cap_text}*\n")

    # Recursively process subsections
    for subsection in section_elem.findall('./sec'):
        content.append(extract_section(subsection, level + 1))

    return '\n'.join(content)


def extract_body(root):
    """Extract main body sections"""
    body = root.find('.//body')
    if body is None:
        return ""

    sections = []

    # Process each top-level section
    for sec in body.findall('./sec'):
        section_content = extract_section(sec, level=2)
        sections.append(section_content)

    return '\n\n'.join(sections)


def extract_references(root):
    """Extract references"""
    ref_list = root.find('.//ref-list')
    if ref_list is None:
        return ""

    references = []
    references.append("\n## References\n")

    for ref in ref_list.findall('.//ref'):
        ref_id = ref.get('id', '')

        # Get mixed-citation or element-citation
        citation = ref.find('.//mixed-citation') or ref.find('.//element-citation')
        if citation is not None:
            # Extract citation text
            cit_text = clean_text(''.join(citation.itertext()))
            references.append(f"{ref_id}. {cit_text}\n")

    return '\n'.join(references)


def jats_to_markdown(xml_path, output_path=None):
    """Convert JATS XML to Markdown"""

    # Parse XML
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None

    # Build markdown document
    markdown_parts = []

    # Title
    title = extract_title(root)
    if title:
        markdown_parts.append(f"# {title}\n")

    # Authors
    authors = extract_authors(root)
    if authors:
        markdown_parts.append(f"**Authors**: {', '.join(authors)}\n")

    # Extract publication info
    journal = root.find('.//journal-title')
    year = root.find('.//pub-date[@pub-type="epub"]/year') or root.find('.//pub-date[@pub-type="ppub"]/year')

    if journal is not None:
        journal_text = clean_text(journal.text or '')
        year_text = clean_text(year.text or '') if year is not None else ''
        markdown_parts.append(f"**Journal**: {journal_text} ({year_text})\n")

    # Abstract
    abstract = extract_abstract(root)
    if abstract:
        markdown_parts.append(f"\n## Abstract\n\n{abstract}\n")

    # Main body
    body = extract_body(root)
    if body:
        markdown_parts.append(f"\n{body}\n")

    # References
    references = extract_references(root)
    if references:
        markdown_parts.append(f"\n{references}\n")

    # Combine all parts
    markdown_content = '\n'.join(markdown_parts)

    # Save to file if output path provided
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Converted: {xml_path} → {output_path}")

    return markdown_content


def main():
    parser = argparse.ArgumentParser(description='Convert JATS XML to Markdown')
    parser.add_argument('xml_file', help='Input JATS XML file')
    parser.add_argument('-o', '--output', help='Output Markdown file (default: same name with .md extension)')

    args = parser.parse_args()

    xml_path = Path(args.xml_file)

    if not xml_path.exists():
        print(f"Error: File not found: {xml_path}")
        return

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = xml_path.with_suffix('.md')

    # Convert
    jats_to_markdown(xml_path, output_path)


if __name__ == '__main__':
    main()
