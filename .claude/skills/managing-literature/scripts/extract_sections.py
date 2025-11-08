#!/usr/bin/env python3
"""
Extract standard manuscript sections from biomedical research articles.
Extracts: Abstract, Introduction, Methods, Results, Discussion
"""

import argparse
import re
from pathlib import Path


def find_section_boundaries(lines):
    """Find line numbers for section boundaries"""

    # Common section header patterns
    section_patterns = {
        'abstract': [r'^##?\s+abstract\b', r'^abstract$'],
        'introduction': [r'^##?\s+(introduction|background)\b', r'^(introduction|background)$'],
        'methods': [r'^##?\s+methods?\b', r'^methods?$', r'materials? and methods?'],
        'results': [r'^##?\s+results?\b', r'^results?$'],
        'discussion': [r'^##?\s+discussion\b', r'^discussion$'],
        'references': [r'^##?\s+references?\b', r'^references?$', r'^\d+\.']
    }

    sections = {}

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip().lower()

        # Skip very long lines (not headers)
        if len(line_stripped) > 100:
            continue

        for section_name, patterns in section_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    # Check if it's a short standalone line (likely a header)
                    if len(line_stripped) < 80:
                        if section_name not in sections:
                            sections[section_name] = i
                        break

    return sections


def extract_section(lines, start_line, end_line):
    """Extract lines between start and end"""
    if start_line is None:
        return ""

    # Adjust for 0-indexed list
    start_idx = start_line - 1
    end_idx = end_line - 1 if end_line else len(lines)

    section_lines = lines[start_idx:end_idx]

    # Remove the header line itself
    if section_lines and (section_lines[0].strip().startswith('#') or
                         len(section_lines[0].strip()) < 80):
        section_lines = section_lines[1:]

    # Join and clean
    content = '\n'.join(section_lines).strip()

    return content


def extract_all_sections(markdown_file):
    """Extract all standard sections from a markdown file"""

    with open(markdown_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find section boundaries
    boundaries = find_section_boundaries(lines)

    # Sort boundaries by line number
    sorted_sections = sorted(boundaries.items(), key=lambda x: x[1])

    # Extract each section
    extracted = {}

    # Define the sections we want to extract
    target_sections = ['abstract', 'introduction', 'methods', 'results', 'discussion']

    for section in target_sections:
        if section not in boundaries:
            print(f"  Warning: {section.title()} section not found")
            extracted[section] = ""
            continue

        start = boundaries[section]

        # Find the end (next section or end of file)
        end = None
        for name, line_num in sorted_sections:
            if line_num > start:
                end = line_num
                break

        content = extract_section(lines, start, end)
        extracted[section] = content

        # Show preview
        preview = content[:150].replace('\n', ' ')
        print(f"  ✓ {section.title():15} {len(content):6} chars  \"{preview}...\"")

    return extracted


def save_sections(sections, output_dir, paper_id):
    """Save extracted sections to separate files"""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    section_map = {
        'abstract': 'abstract',
        'introduction': 'introduction',
        'methods': 'methods',
        'results': 'results',
        'discussion': 'discussion'
    }

    for section_key, section_name in section_map.items():
        if section_key in sections and sections[section_key]:
            filename = f"{paper_id}_{section_name}.md"
            filepath = output_path / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                # Write section header
                f.write(f"# {section_name.title()}\n\n")
                f.write(f"*Extracted from {paper_id}*\n\n")
                f.write("---\n\n")
                f.write(sections[section_key])

            print(f"  Saved: {filepath}")


def main():
    parser = argparse.ArgumentParser(description='Extract sections from biomedical research articles')
    parser.add_argument('input_file', help='Input markdown file')
    parser.add_argument('-o', '--output-dir', default='sections', help='Output directory for extracted sections')
    parser.add_argument('--paper-id', help='Paper identifier (default: filename stem)')

    args = parser.parse_args()

    input_path = Path(args.input_file)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return

    paper_id = args.paper_id or input_path.stem

    print(f"\nExtracting sections from: {input_path.name}")
    print("="*70)

    # Extract sections
    sections = extract_all_sections(input_path)

    # Save sections
    print(f"\nSaving sections to: {args.output_dir}/")
    print("="*70)
    save_sections(sections, args.output_dir, paper_id)

    print(f"\n✓ Extraction complete")


if __name__ == '__main__':
    main()
