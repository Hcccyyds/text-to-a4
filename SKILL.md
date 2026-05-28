---
name: text-to-a4
description: >-
  将任意文档（.docx/.txt/.md/.pdf）自动排版成极致紧凑的 A4 复习纸 PDF。
  一张 A4 纸搞定一份复习资料，方便打印携带。7.5px 微软雅黑，纯黑白，字不重叠。
  触发词："排版成A4"、"转成A4 PDF"、"导出PDF"、"复习纸"、"打印复习"、
  "text to a4"、"format for print"、"print to PDF"、"document to PDF"。
  适用于任何包含文字的文档，中英文均支持。
---

# text-to-a4 — 一份复习资料，一张 A4 纸

**CRITICAL: Claude MUST manually read the extracted text and generate HTML.**
The `to_html.py` script is a fallback only. Claude understands content structure
and can pack everything much tighter. **Target: 1 page. Only go to 2 pages if
content truly cannot fit at minimum readable size (7px, 1.1 line-height, 2mm margins).**

## Core Rules (ALWAYS follow)

1. **Never modify original text** — preserve every character, only format layout
2. **No text overlap** — use tables (not inline spans) for multi-item rows; max 5 columns per row for cloze/grid data; max 2 columns for Q&A pairs
3. **Group related content together** — one question's answers stay in one table; one term's definition stays in one paragraph
4. **Bold only key labels** — `<b>term/heading:</b>` normal-weight explanation
5. **Font: 7.5px body, Microsoft YaHei** — works for both Chinese and English, no Type 3 PDF issues
6. **Line height: 1.15, margins: 2.5mm** — compact but readable
7. **Check for overlap before exporting** — verify each table cell has enough width

---

## Workflow

### Step 1: Extract Text

```bash
python scripts/extract_text.py "<input_file>" -o extracted.txt
```

### Step 2: Read & Analyze Content

Read the extracted text. Identify ALL content types present in the document (there may be multiple).

### Step 3: Generate HTML with Correct Patterns

Use the CSS template at the bottom. Apply the right HTML pattern for each content type.

### Step 4: Verify No Overlap & Export

Check table columns are wide enough. Export:

```bash
python scripts/to_pdf.py "<output.html>" -o "<output.pdf>"
```

---

## Content Type Patterns (ALL supported)

### Type 1: Prose / Essays (连续段落)

```html
<div class="essay">
  <p>Paragraph one text with indent...</p>
  <p>Paragraph two text with indent...</p>
</div>
```
- Use `<p>` for each paragraph
- Full original text, no abbreviation

### Type 2: Q&A / Exam Reading Answers (5 题一组，如阅读理解)

```html
<p class="txt">Text 1 · Topic Name（主题）</p>
<table class="ans">
  <tr><td>21. [B] answer text for Q21</td><td>24. [C] answer text for Q24</td></tr>
  <tr><td>22. [A] answer text for Q22</td><td>25. [B] answer text for Q25</td></tr>
  <tr><td>23. [D] answer text for Q23</td><td></td></tr>
</table>
```
- 2 columns × 3 rows for 5 answers (left: Q1-3, right: Q4-5)
- `table-layout: fixed` prevents column width mismatch
- If answers are short, can also use 1 row with all answers inline: `<p><b>1.[A]</b> xxx <b>2.[B]</b> yyy <b>3.[C]</b> zzz</p>`

### Type 3: Cloze / Grid Numbered Items (20 题一组，如完形填空)

```html
<table class="ct">
  <tr><th>1</th><td>[B] answer1</td><th>2</th><td>[A] answer2</td><th>3</th><td>[D] answer3</td><th>4</th><td>[C] answer4</td><th>5</th><td>[B] answer5</td></tr>
  <tr><th>6</th><td>[A] answer6</td><th>7</th><td>[B] answer7</td><th>8</th><td>[C] answer8</td><th>9</th><td>[D] answer9</td><th>10</th><td>[D] answer10</td></tr>
  <tr><th>11</th><td>[C] answer11</td>...</tr>
  <tr><th>16</th><td>[D] answer16</td>...</tr>
</table>
```
- **Max 5 columns per row** (10 cells: 5 th+td pairs). Any more → too narrow → overlap
- 20 items = 4 rows × 5 pairs
- If items have very long answers, reduce to 4 pairs per row (5 rows total)

### Type 4: Key Term + Definition (名词解释 / 概念定义)

```html
<p><b>69. 术语名称：</b>定义内容，完整保留原文解释。</p>
<p><b>70. Another Term：</b>Definition text follows the bold label inline.</p>
```
- Bold only the term+colon, definition in normal weight
- Single `<p>` per term (not separate lines for term vs definition)

### Type 5: Multiple Choice Questions with Long Explanations (选择题 + 详细解释)

```html
<p><b>1. 题目/问题：</b>答案或解释内容，可以是完整句子或段落。保留全部原文内容。</p>
<p><b>2. Next Question：</b>Answer with full explanation text following inline.</p>
```
- Like Type 4 but with question numbers
- Bold the question part, normal weight for answer
- Single `<p>` keeps question+answer together

### Type 6: Data Tables (真正的表格数据，如生命周期表)

```html
<table class="dt">
  <tr><th>变量</th><th>考察期</th><th>形成期</th><th>稳定期</th><th>退化期</th></tr>
  <tr><td>交易量</td><td>总体很小</td><td>快速增长</td><td>最大并稳定</td><td>回落</td></tr>
  <tr><td>价格</td><td>基本价格</td><td>上升趋势</td><td>继续上升</td><td>开始下降</td></tr>
</table>
```
- Header row with `<th>`, data rows with `<td>`
- 3-6 columns max (depending on content width)
- Add `table-layout: fixed; width: 100%` to CSS class

### Type 7: Short Bullet Points / Characteristics (特点/原则列举)

```html
<p><b>Title/Question：</b>item1、item2、item3、item4、item5</p>
```
- Use Chinese comma `、` or semicolon `；` to join short items
- Keep all items for one topic in one `<p>`
- Or use compact inline: `①xxx ②yyy ③zzz`

### Type 8: Hierarchical Lists (层级列表，如大点套小点)

```html
<p><b>一、Main Topic：</b>（1）sub-point one；（2）sub-point two；（3）sub-point three with detail description</p>
<p><b>二、Second Topic：</b>（1）detail A；（2）detail B</p>
```
- Top-level as separate `<p>` blocks with bold labels
- Sub-items inline within the paragraph
- Use （1）（2）or ①②③ for nested numbering

### Type 9: Pure Lists (纯列表，无标题)

```html
<p>1. First list item text content here.</p>
<p>2. Second list item text content here.</p>
<p>3. Third list item text content here.</p>
```
- One `<p>` per list item
- Compact but clear separation

### Type 10: Mixed English-Chinese Content

No special treatment needed — Microsoft YaHei handles both. Just follow the pattern that matches the content structure. For inline English in Chinese text, no extra spacing needed.

---

## Section Headings

```html
<h1>Document Title</h1>
<p class="subtitle">Optional subtitle / description</p>

<h2>一、Major Section</h2>
<h3>Sub-section or Year Label</h3>
```

- `<h1>`: document title (10px, centered)
- `<h2>`: major sections (8px, bottom border line)
- `<h3>`: sub-sections (7.5px)

---

## Anti-Overlap Checklist (check before exporting)

- [ ] Q&A answers use `<table class="ans">` — NOT inline `<span>` blocks
- [ ] Cloze tables: max 5 th+td pairs per row (10 cells)
- [ ] Data tables: max 6 columns, headers wrap if needed
- [ ] No cell has text longer than ~25 characters (if so, split into more rows)
- [ ] Long definition text is in `<p>` (not in table cells)
- [ ] Check bottom of page 1 — content doesn't overflow off the page

---

## CSS Template (embed in every HTML)

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 2.5mm; }
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
  /* Answer table: 2 columns for 5-item Q&A groups */
  .ans { border-collapse: collapse; margin: 0 0 1px; width: 100%; table-layout: fixed; }
  .ans td { padding: 0 3px; }
  /* Cloze/grid table: max 5 pairs per row */
  .ct { border-collapse: collapse; margin: 0; width: 100%; table-layout: fixed; }
  .ct th { border: none; padding: 0 1px 0 0; font-weight: bold; font-size: 7px; }
  .ct td { padding: 0 3px 0 0; font-size: 7px; }
  /* Data table: for actual tabular data */
  .dt { border-collapse: collapse; margin: 0 0 1px; width: 100%; table-layout: fixed; }
  .dt th { border: 0.3px solid #ccc; padding: 0 2px; font-weight: bold; background: #eee; }
  .dt td { border: 0.3px solid #ccc; padding: 0 2px; }
  @media print { body { padding: 0; } }
</style>
</head>
<body>
  <!-- Content here -->
</body>
</html>
```

## Dependencies

- Python 3.11+
- Playwright: `pip install playwright && playwright install chromium`
- PyMuPDF: `pip install pymupdf` (for PDF input only)
