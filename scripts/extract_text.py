#!/usr/bin/env python3
"""Extract text from various document formats (.docx, .txt, .md, .pdf).

Usage:
    python extract_text.py <input_file> [-o output.txt]
"""

import sys
import os
import argparse


def extract_txt(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_md(path):
    return extract_txt(path)


def extract_docx(path):
    import zipfile
    from xml.etree import ElementTree as ET

    z = zipfile.ZipFile(path)
    xml_content = z.read('word/document.xml')
    tree = ET.fromstring(xml_content)
    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

    lines = []
    for para in tree.iter(f'{ns}p'):
        texts = []
        for t in para.iter(f'{ns}t'):
            if t.text:
                texts.append(t.text)
        line = ''.join(texts)
        lines.append(line)

    z.close()
    return '\n'.join(lines)


def extract_pdf(path):
    import fitz
    doc = fitz.open(path)
    lines = []
    for page in doc:
        text = page.get_text()
        if text:
            lines.append(text.strip())
    doc.close()
    return '\n\n'.join(lines)


EXTRACTORS = {
    '.txt': extract_txt,
    '.md': extract_md,
    '.docx': extract_docx,
    '.pdf': extract_pdf,
}


def main():
    parser = argparse.ArgumentParser(description='Extract text from documents')
    parser.add_argument('input', help='Input file path')
    parser.add_argument('-o', '--output', help='Output text file (default: stdout)')
    args = parser.parse_args()

    ext = os.path.splitext(args.input)[1].lower()
    if ext not in EXTRACTORS:
        print(f"Unsupported format: {ext}. Supported: {', '.join(EXTRACTORS.keys())}")
        sys.exit(1)

    text = EXTRACTORS[ext](args.input)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Extracted {len(text)} chars → {args.output}")
    else:
        print(text)


if __name__ == '__main__':
    main()
