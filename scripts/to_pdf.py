#!/usr/bin/env python3
"""Render HTML to A4 PDF using Playwright (Chromium print emulation).

Usage:
    python to_pdf.py <input.html> [-o output.pdf]
"""

import sys
import os
import argparse


def html_to_pdf(html_path, pdf_path):
    from playwright.sync_api import sync_playwright

    abs_html = 'file:///' + os.path.abspath(html_path).replace('\\', '/')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(abs_html)
        page.wait_for_timeout(800)
        page.emulate_media(media='print')
        page.pdf(
            path=pdf_path,
            format='A4',
            margin={'top': '2.5mm', 'right': '2.5mm', 'bottom': '2.5mm', 'left': '2.5mm'},
            print_background=False,
            prefer_css_page_size=True,
        )
        browser.close()

    # Check page count
    import fitz
    doc = fitz.open(pdf_path)
    pages = doc.page_count
    doc.close()

    return pages


def main():
    parser = argparse.ArgumentParser(description='Render HTML to A4 PDF')
    parser.add_argument('input', help='Input HTML file')
    parser.add_argument('-o', '--output', help='Output PDF file (default: input.pdf)')
    args = parser.parse_args()

    pdf_path = args.output or args.input.rsplit('.', 1)[0] + '.pdf'
    pages = html_to_pdf(args.input, pdf_path)

    print(f"PDF saved → {pdf_path} ({pages} page(s))")

    # Open the PDF
    os.startfile(pdf_path)


if __name__ == '__main__':
    main()
