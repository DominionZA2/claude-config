# Translating English PDFs to Bengali

I know how to translate an English PDF into Bengali (বাংলা) while keeping the original visual layout, images, logos, colours, and contact details intact. Bengali is left-to-right, which removes RTL complexity, but it is a complex Indic script with conjuncts and vowel signs (matras) that require HarfBuzz shaping to render correctly.

## What I do

I open the original English PDF, identify each text block's position and styling, translate the text to Bengali, visually white-out the original text, and write the Bengali replacement in the same position. The layout is preserved visually — see Limitations for what this approach does and does not guarantee.

## The core technique

### Font

Bengali requires a font covering Unicode block 0x0980–0x09FF. On Windows, probe for available Bengali fonts in order:

```python
import os

BENGALI_FONT_CANDIDATES = [
    "C:/Windows/Fonts/Nirmala.ttc",        # Nirmala UI — confirmed present on Windows 10/11
    "C:/Windows/Fonts/NirmalaUI.ttf",
    "C:/Windows/Fonts/vrinda.ttf",          # older Windows versions
]

FONT = next((f for f in BENGALI_FONT_CANDIDATES if os.path.exists(f)), None)
if FONT is None:
    raise RuntimeError("No Bengali-capable font found. Install Nirmala UI or Vrinda.")
```

Nirmala UI ships as `Nirmala.ttc` (a TrueType collection) on most Windows 10/11 machines. Do not assume `NirmalaS.ttf` or `NirmalaSB.ttf` — these do not exist on a standard install.

Prefer the source PDF's embedded font if it covers the Bengali Unicode block, as it preserves original metrics and line breaks. Use the probe list only as a fallback.

### Inspecting the source PDF

```python
import fitz
doc = fitz.open("input.pdf")
for page_num, page in enumerate(doc):
    for block in page.get_text("dict")["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    print(page_num, span["bbox"], span["size"], span["color"],
                          span["flags"], span["text"])
```

`span["flags"]` encodes bold (bit 4) and italic (bit 1). `span["color"]` is a packed int:

```python
def ic(c):
    return ((c >> 16) & 0xFF) / 255.0, ((c >> 8) & 0xFF) / 255.0, (c & 0xFF) / 255.0
```

### Rendering Bengali text: use `insert_htmlbox()` not `fill_textbox()`

`TextWriter.fill_textbox()` does not use HarfBuzz shaping — it lays glyphs out without forming proper conjuncts or positioning matras. For Bengali, PyMuPDF's correct rendering path is `page.insert_htmlbox()` (the Story API), which uses HarfBuzz internally:

```python
def wipe(page, x0, y0, x1, y1, text, size, color_rgb, bold=False):
    # White-out the area
    page.draw_rect(fitz.Rect(x0-1, y0-2, x1+1, y1+2),
                   color=(1,1,1), fill=(1,1,1), width=0)
    if not text:
        return
    r, g, b = color_rgb
    hex_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    weight = "bold" if bold else "normal"
    # insert_htmlbox uses HarfBuzz for correct Bengali shaping
    html = (f'<p style="font-family: Nirmala UI, Vrinda; '
            f'font-size: {size}pt; color: {hex_color}; font-weight: {weight}; '
            f'margin: 0; padding: 0;">{text}</p>')
    rect = fitz.Rect(x0, y0, x1, y1)
    rc = page.insert_htmlbox(rect, html, css="* { line-height: 1.2; }")
    if rc > 0:
        print(f"WARNING: Bengali text overflowed rect {rect} — {rc} lines dropped")
```

`insert_htmlbox()` returns the number of lines that did not fit. A return value > 0 means overflow — log it and consider reducing font size or adjusting the rect.

### Translating at block level, not span level

PDF spans are often split mid-sentence by styling or kerning. Always:

1. Collect all spans within a block and join them into one string
2. Translate the full block as a unit
3. Re-flow the translation into the block's bounding box

### Saving

```python
with open(dst, "wb") as f:
    f.write(doc.tobytes(garbage=4, deflate=True))
doc.close()
```

Note: this helps with some file-path locking scenarios but does not prevent errors if the destination is open in a viewer. Close the viewer first.

## What I've learned about Bengali specifically

### Complex script shaping
Bengali conjuncts (যুক্তাক্ষর) and vowel signs (মাত্রা) require OpenType shaping. `fill_textbox()` does not do this — use `insert_htmlbox()`. For most health information content (short sentences, common vocabulary), `insert_htmlbox()` with Nirmala UI produces correct output.

### Bengali numerals
Bengali has its own numeral forms (০ ১ ২ ৩...) but modern Bengali commonly uses Western Arabic numerals. Follow the source document's convention. For NHS-style health documents, Western numerals are generally acceptable.

### No separate bold font file needed
`insert_htmlbox()` with `font-weight: bold` in the HTML style handles bold via the font's internal bold variant — no separate `.ttf` file path needed.

### Font size
Bengali characters are typically taller than Latin at the same declared size. Start at the original English font size and reduce by 1–2pt if overflow is reported.

## Limitations

- **White-out is visual only**: Drawing a white rectangle paints over the English text in the rendered view but does not remove it from the PDF's internal text layer. The English text may remain selectable or found by search. For true redaction, use `page.add_redact_annot()` + `page.apply_redactions()` before placing the translation.
- **Non-white backgrounds**: The white rect assumption breaks if text sits over a coloured box, gradient, watermark, or image. Use `add_redact_annot()` instead, or handle those areas separately.
- **Scanned/image PDFs**: If `page.get_text("text").strip()` returns very little, the PDF is likely image-only. `get_text("dict")` will return no usable spans. The workflow fails and OCR must be run first.
- **Broken encodings**: Some PDFs have missing `/ToUnicode` maps. `get_text()` may return garbage characters. Use `get_text("rawdict")` to diagnose, and cross-check extracted text visually before translating.
- **Alignment**: `insert_htmlbox()` defaults to left-aligned text. Adjust the HTML `text-align` style for blocks that were originally centred or right-aligned.

## Applying this to any English PDF

1. Check `page.get_text("text")` is non-empty — if not, OCR is needed first
2. Inspect blocks with `get_text("dict")` to map bboxes, sizes, colours, and flags
3. Join spans within each block and translate at block level
4. Call `wipe()` per block using `insert_htmlbox()` for correct Bengali shaping; watch for overflow warnings
5. Adjust alignment per block if the original used centre or right alignment
6. Save to `<original name> - Bengali.pdf`
