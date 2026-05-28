#!/usr/bin/env python3
"""Convert plain text into an ultra-compact A4 HTML page for print review.

Usage:
    python to_html.py <input.txt> [-o output.html] [--title "Title"]

Note: This script provides basic auto-formatting. For best results, use the
text-to-a4 skill through Claude Code, which intelligently generates HTML
tailored to the document's content structure.
"""

import sys
import os
import re
import argparse


CSS = """  @page { size: A4; margin: 2.5mm; }
  body {
    font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
    font-size: 7.5px; line-height: 1.15; color: #000; background: #fff;
    width: 210mm; margin: 0 auto; padding: 2.5mm 2.5mm; box-sizing: border-box;
  }
  h1 { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 10px; text-align: center; margin: 0 0 1px; }
  .subtitle { text-align: center; font-size: 6px; color: #333; margin: 0 0 2px; }
  h2 { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 8px; margin: 3px 0 0; border-bottom: 0.5px solid #000; }
  h3 { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 7.5px; margin: 2px 0 0; }
  p { margin: 0; }
  b { font-weight: bold; }
  .essay p { text-indent: 1em; }
  .txt { font-weight: bold; margin: 1px 0 0; }
  .note { font-size: 6px; margin: 0; color: #555; }
  /* Answer table: 2 columns, no borders, fixed layout prevents overlap */
  .ans { border-collapse: collapse; margin: 0 0 1px; width: 100%; table-layout: fixed; }
  .ans td { padding: 0 3px; }
  /* Cloze/grid table: max 5 pairs per row to avoid cell overflow */
  .ct { border-collapse: collapse; margin: 0; width: 100%; table-layout: fixed; }
  .ct th { border: none; padding: 0 1px 0 0; font-weight: bold; font-size: 7px; }
  .ct td { padding: 0 3px 0 0; font-size: 7px; }
  /* Data table: for actual tabular data with headers */
  .dt { border-collapse: collapse; margin: 0 0 1px; width: 100%; table-layout: fixed; }
  .dt th { border: 0.3px solid #ccc; padding: 0 2px; font-weight: bold; background: #eee; }
  .dt td { border: 0.3px solid #ccc; padding: 0 2px; }
  @media print { body { padding: 0; } }"""


# ── content detection ──────────────────────────────────────────────

def is_chapter_heading(line):
    """一、 二、 三、 style headings."""
    return bool(re.match(r'^[一二三四五六七八九十]+、', line))


def is_numbered_heading(line):
    """2021 年英语... style year headings."""
    return bool(re.match(r'^\d{4}\s*年', line))


def is_text_heading(line):
    """Text 1, Part A, Section 1 style headings."""
    return bool(re.match(r'^(Text|Part|Section|Chapter)\s*\d', line, re.IGNORECASE))


def is_section_label(line):
    """一、选择  二、名词解释  style."""
    return bool(re.match(r'^[一二三四五六七八九十]+、\S+', line))


def is_bold_label_line(line):
    """Line with a key term followed by colon + explanation.
    e.g. '69. 客户：定义内容...' or '10. 关系营销的核心：保持客户'"""
    # Numbered term: "1. Term：explanation" or "1. Term: explanation"
    if re.match(r'^\d{1,3}[\.\、]\s*\S+[：:]', line):
        return True
    # Short bold label with colon and longer text after
    if '：' in line or ':' in line:
        parts = re.split(r'[：:]', line, maxsplit=1)
        if len(parts) == 2 and len(parts[0]) <= 30 and len(parts[1]) > 0:
            return True
    return False


def is_table_data(line):
    """Line with tabs or multiple spaces suggesting columns."""
    if '\t' in line:
        return True
    if line.count('  ') >= 3:
        return True
    return False


def is_cloze_item(line):
    """Single numbered cloze/answer item like '21. [B] answer text'"""
    return bool(re.match(r'^\d{1,3}[\.\)]\s*\[[A-D]\]', line))


def is_short_list_item(line):
    """Short bullet/numbered item that could be inline."""
    return bool(re.match(r'^[\d①-⑳][\.\)、]', line))


# ── HTML builders ──────────────────────────────────────────────────

def escape(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def build_bold_label_p(line):
    """Convert 'Term：explanation' into <p><b>Term：</b>explanation</p>"""
    for sep in ['：', ':']:
        if sep in line:
            parts = line.split(sep, 1)
            label = parts[0] + sep
            rest = parts[1] if len(parts) > 1 else ''
            return f'<p><b>{escape(label)}</b>{escape(rest)}</p>'
    return f'<p>{escape(line)}</p>'


def build_ans_table(items, cols=3):
    """Build a 2-column answer table from a list of items.
    For 5 items: rows = (1,4), (2,5), (3,empty)"""
    n = len(items)
    rows_needed = (n + 1) // 2  # ceil(n/2) for 2 columns
    html_rows = []
    for r in range(rows_needed):
        left = items[r] if r < n else ''
        right = items[r + rows_needed] if (r + rows_needed) < n else ''
        html_rows.append(f'<tr><td>{escape(left)}</td><td>{escape(right)}</td></tr>')
    return f'<table class="ans">{"".join(html_rows)}</table>'


def build_cloze_table(items):
    """Build a cloze table: 5 pairs per row (max 10 cells/row to prevent overlap)."""
    pairs_per_row = 5
    html_rows = []
    for i in range(0, len(items), pairs_per_row):
        chunk = items[i:i + pairs_per_row]
        cells = []
        for j, item in enumerate(chunk):
            num = i + j + 1
            cells.append(f'<th>{num}</th><td>{escape(item)}</td>')
        html_rows.append(f'<tr>{"".join(cells)}</tr>')
    return f'<table class="ct">{"".join(html_rows)}</table>'


def build_data_table(rows_data):
    """Build a .dt table from list of lists."""
    if not rows_data:
        return ''
    max_cols = max(len(r) for r in rows_data)
    html_rows = []
    for i, row in enumerate(rows_data):
        tag = 'th' if i == 0 else 'td'
        cells = ''.join(f'<{tag}>{escape(c)}</{tag}>' for c in row)
        html_rows.append(f'<tr>{cells}</tr>')
    return f'<table class="dt">{"".join(html_rows)}</table>'


# ── main conversion ───────────────────────────────────────────────

def text_to_html(text, title="Document"):
    lines = text.strip().split('\n')

    # Auto-compact: if content is long, use tighter settings to fit 1 page
    char_count = len(text)
    if char_count > 8000:
        compact_css = CSS.replace('font-size: 7.5px', 'font-size: 7px')\
                         .replace('line-height: 1.15', 'line-height: 1.1')\
                         .replace('padding: 2.5mm 2.5mm', 'padding: 2mm 2mm')\
                         .replace('margin: 2.5mm;', 'margin: 2mm;')\
                         .replace('h1 { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 10px', 'h1 { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 9px')\
                         .replace('h2 { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 8px', 'h2 { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 7.5px')\
                         .replace('h3 { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 7.5px', 'h3 { font-family: "Microsoft YaHei", "PingFang SC", sans-serif; font-size: 7px')
    elif char_count > 5000:
        compact_css = CSS.replace('font-size: 7.5px', 'font-size: 7px')\
                         .replace('line-height: 1.15', 'line-height: 1.1')
    else:
        compact_css = CSS

    body = [f'<h1>{escape(title)}</h1>']

    i = 0
    cloze_buffer = []      # consecutive cloze items (numbered [A-D])
    table_buffer = []      # consecutive tabular data lines
    list_buffer = []       # consecutive short list items

    def flush_cloze():
        nonlocal cloze_buffer
        if cloze_buffer:
            # Extract answer text from items like "21. [B] answer text"
            answers = []
            for item in cloze_buffer:
                m = re.match(r'^\d+[\.\)]\s*\[([A-D])\]\s*(.+)', item)
                if m:
                    answers.append(f'[{m.group(1)}] {m.group(2)}')
                else:
                    answers.append(item)
            body.append(build_cloze_table(answers))
            cloze_buffer = []

    def flush_table():
        nonlocal table_buffer
        if table_buffer:
            rows = [re.split(r'\t|\s{2,}', row) for row in table_buffer]
            rows = [[c.strip() for c in r if c.strip()] for r in rows]
            body.append(build_data_table(rows))
            table_buffer = []

    def flush_list():
        nonlocal list_buffer
        if list_buffer:
            # Put short related items into an answer table if they look like Q&A
            if len(list_buffer) >= 3 and all(is_cloze_item(x) for x in list_buffer):
                flush_cloze()  # they were collected in cloze_buffer, not list_buffer
            else:
                for item in list_buffer:
                    body.append(f'<p>{escape(item)}</p>')
            list_buffer = []

    while i < len(lines):
        line = lines[i].strip()

        # Empty line → flush buffers
        if not line:
            flush_cloze()
            flush_table()
            flush_list()
            i += 1
            continue

        # Chapter headings
        if is_chapter_heading(line):
            flush_cloze(); flush_table(); flush_list()
            body.append(f'<h2>{escape(line)}</h2>')
            i += 1
            continue

        # Section labels like "一、选择"
        if is_section_label(line):
            flush_cloze(); flush_table(); flush_list()
            body.append(f'<h2>{escape(line)}</h2>')
            i += 1
            continue

        # Year or numbered headings
        if is_numbered_heading(line) or is_text_heading(line):
            flush_cloze(); flush_table(); flush_list()
            body.append(f'<h3>{escape(line)}</h3>')
            i += 1
            continue

        # Cloze items (numbered with [A-D])
        if is_cloze_item(line):
            flush_table(); flush_list()
            cloze_buffer.append(line)
            i += 1
            continue
        else:
            flush_cloze()

        # Tabular data
        if is_table_data(line):
            flush_cloze(); flush_list()
            table_buffer.append(line)
            i += 1
            continue
        else:
            flush_table()

        # Bold label: "Term：explanation"
        if is_bold_label_line(line):
            flush_cloze(); flush_table(); flush_list()
            body.append(build_bold_label_p(line))
            i += 1
            continue

        # Note line
        if line.startswith('首句') or line.startswith('注'):
            flush_cloze(); flush_table(); flush_list()
            body.append(f'<p class="note">{escape(line)}</p>')
            i += 1
            continue

        # Short standalone label (likely a sub-heading or topic title)
        if len(line) <= 40 and ('·' in line or '（' in line or '/' in line):
            flush_cloze(); flush_table(); flush_list()
            body.append(f'<p class="txt">{escape(line)}</p>')
            i += 1
            continue

        # Default: paragraph
        flush_cloze(); flush_table(); flush_list()
        body.append(f'<p>{escape(line)}</p>')
        i += 1

    # Flush remaining
    flush_cloze()
    flush_table()
    flush_list()

    body_html = '\n'.join(body)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
{compact_css}
</style>
</head>
<body>
{body_html}
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description='Convert text to A4 review-sheet HTML')
    parser.add_argument('input', help='Input text file')
    parser.add_argument('-o', '--output', help='Output HTML file')
    parser.add_argument('--title', help='Document title')
    args = parser.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    title = args.title or os.path.splitext(os.path.basename(args.input))[0]
    html = text_to_html(text, title)

    out_path = args.output or args.input.rsplit('.', 1)[0] + '.html'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML saved → {out_path}")


if __name__ == '__main__':
    main()
