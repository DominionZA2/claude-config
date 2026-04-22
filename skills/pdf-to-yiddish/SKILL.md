# Translating English PDFs to Yiddish

I know how to translate an English PDF into Yiddish while keeping the original layout, images, logos, colours, and contact details completely intact. I've learned this through multiple iterations and know exactly which approaches work and which ones fail.

## What I do

I open the original English PDF, identify each text block's position and styling, translate the text to Yiddish, white-out the original text, and write the Yiddish replacement in the same position using correct RTL rendering. The output PDF is a faithful Yiddish version of the original — same page structure, same visual design, only the words change.

## The core technique

### Inspecting the source PDF

I use PyMuPDF (`fitz`) to read the existing text blocks and their bounding boxes:

```python
import fitz
doc = fitz.open("input.pdf")
for page_num, page in enumerate(doc):
    for block in page.get_text("dict")["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    print(page_num, span["bbox"], span["size"], span["color"], span["text"])
```

`span["bbox"]` gives `(x0, y0, x1, y1)`. `span["color"]` is a packed integer I convert with:

```python
def ic(c):
    return ((c >> 16) & 0xFF) / 255.0, ((c >> 8) & 0xFF) / 255.0, (c & 0xFF) / 255.0
```

### The wipe function

This is the workhorse. It white-outs a region and writes RTL Yiddish text in its place:

```python
FONT    = "C:/Windows/Fonts/arial.ttf"   # has Hebrew Unicode block 0x0590-0x05FF
FONT_BD = "C:/Windows/Fonts/arialbd.ttf"

def wipe(page, x0, y0, x1, y1, text, size, color, bold=False):
    page.draw_rect(fitz.Rect(x0-1, y0-2, x1+1, y1+2),
                   color=(1,1,1), fill=(1,1,1), width=0)
    if not text:
        return
    font = fitz.Font(fontfile=FONT_BD if bold else FONT)

    # Single-line text: use append() — more reliable RTL for headings and titles
    for s in [size, size-1, size-2, size-3, size-4]:
        if s < 5:
            break
        tl = font.text_length(text, fontsize=s)
        if tl <= (x1 - x0):
            tw = fitz.TextWriter(page.rect, color=color)
            tw.append((x1 - tl, y0 + s * font.ascender), text,
                      font=font, fontsize=s, right_to_left=True)
            tw.write_text(page)
            return

    # Multi-line text: fill_textbox wraps automatically
    rect = fitz.Rect(x0, y0, x1, y1)
    tw = None
    for s in [size, size-1, size-2, size-3, size-4]:
        if s < 5:
            break
        tw = fitz.TextWriter(page.rect, color=color)
        unused = tw.fill_textbox(rect, text, font=font, fontsize=s,
                                 right_to_left=True, align=fitz.TEXT_ALIGN_RIGHT)
        if not unused:
            break
    if tw:
        tw.write_text(page)
```

### Saving without file-lock errors

```python
with open(dst, "wb") as f:
    f.write(doc.tobytes(garbage=4, deflate=True))
doc.close()
```

`doc.save(dst)` fails on Windows if the file is open in a viewer. `tobytes()` + `open("wb")` avoids that.

## What I've learned the hard way

### Never use `bidi.algorithm.get_display()`
Passing `get_display()` output to any PyMuPDF function that also has `right_to_left=True` **double-reverses** the characters and produces backwards text. I pass raw logical Unicode order (Yiddish typed normally). PyMuPDF handles the visual reordering internally.

### `append()` position for RTL text is the LEFT edge
`tw.append(pos, text, right_to_left=True)` reverses the characters then renders them **left-to-right** starting at `pos`. So for right-aligned text I set:

```
pos.x = x1 - font.text_length(text, fontsize=s)
```

Setting `pos.x = x1` (the right edge) pushes the entire string off the page to the right.

### Why two paths: `append()` vs `fill_textbox()`
`fill_textbox()` with `right_to_left=True` works correctly for multi-line body text but misbehaves on single-line text (like large headings). `append()` is reliable for single-line text at any font size. I detect which case applies by checking whether the text fits in the box width using `font.text_length()`.

### Font
Arial (`arial.ttf`, always present on Windows) contains the full Hebrew Unicode block and renders Yiddish correctly. No extra font installation needed.

### Font size fallback
Yiddish translations are often longer than their English source. I try up to 5 progressively smaller font sizes (`size` down to `size-4`, minimum 5pt) until the text fits.

## Applying this to any English PDF

When asked to translate a PDF I haven't seen before:
1. Open it with PyMuPDF and inspect each page's text blocks to understand the layout
2. Translate each text span to Yiddish
3. For each span, call `wipe()` with its `bbox`, `size`, and `color` from the inspection step
4. Keep page numbers, phone numbers, reference codes, URLs, and proper nouns (hospital names, NICE, GOSH, NHS, etc.) in their original form or lightly adapted to Yiddish phonetics
5. Save to `<original name> - Yiddish.pdf` (or with a prefix the user specifies)
