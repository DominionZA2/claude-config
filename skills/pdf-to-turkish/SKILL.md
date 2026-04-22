# Translating English PDFs to Turkish

I know how to translate an English PDF into Turkish (Türkçe) while keeping the original visual layout, images, logos, colours, and contact details intact. Turkish uses the Latin alphabet and is left-to-right, making it simpler than RTL or complex-script languages. The main things to get right are special characters, translation register, and a few workflow traps.

## What I do

I open the original English PDF, identify each text block's position and styling, translate the text to Turkish, visually white-out the original text, and write the Turkish replacement in the same position. The layout is preserved visually — the PDF's underlying text layer is replaced at the rendering level, not at the internal structure level (see Limitations below).

## The core technique

### Font

Turkish requires a font that covers the Latin Extended characters used by Turkish:

| Character | Unicode | Name |
|-----------|---------|------|
| ğ / Ğ | U+011F / U+011E | g with breve |
| ş / Ş | U+015F / U+015E | s with cedilla |
| ı / İ | U+0131 / U+0130 | dotless i / dotted I |
| ö / Ö | U+00F6 / U+00D6 | o with diaeresis |
| ü / Ü | U+00FC / U+00DC | u with diaeresis |
| ç / Ç | U+00E7 / U+00C7 | c with cedilla |

Prefer the source PDF's own embedded font if it covers these codepoints — it preserves original metrics and line breaks. Fall back to Arial only when the source font is unavailable or missing coverage:

```python
FONT    = "C:/Windows/Fonts/arial.ttf"   # fallback only; prefer extracted source font
FONT_BD = "C:/Windows/Fonts/arialbd.ttf"
```

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

`span["flags"]` encodes bold (bit 4) and italic (bit 1). `span["color"]` is a packed int, convert with:

```python
def ic(c):
    return ((c >> 16) & 0xFF) / 255.0, ((c >> 8) & 0xFF) / 255.0, (c & 0xFF) / 255.0
```

### Translating at block level, not span level

PDF spans are often split mid-sentence by styling or kerning changes. Translating span-by-span produces fragmented, ungrammatical Turkish because Turkish agglutination means suffixes depend on full-sentence context. Always:

1. Collect all spans within a block and join them into one string
2. Translate the full block as a unit
3. Re-flow the translated text back into the block's bounding box

### The wipe function

```python
def wipe(page, x0, y0, x1, y1, text, size, color, bold=False):
    page.draw_rect(fitz.Rect(x0-1, y0-2, x1+1, y1+2),
                   color=(1,1,1), fill=(1,1,1), width=0)
    if not text:
        return
    font = fitz.Font(fontfile=FONT_BD if bold else FONT)
    rect = fitz.Rect(x0, y0, x1, y1)
    last_tw = None
    last_unused = None
    for s in [size, size-1, size-2, size-3, size-4]:
        if s < 5:
            break
        try:
            tw = fitz.TextWriter(page.rect, color=color)
            unused = tw.fill_textbox(rect, text, font=font, fontsize=s,
                                     align=fitz.TEXT_ALIGN_LEFT)
            last_tw = tw
            last_unused = unused
            if not unused:
                break  # fits cleanly
        except ValueError:
            continue   # text starts outside rect at this size; try smaller
    if last_tw:
        if last_unused:
            print(f"WARNING: overflow at smallest size — text truncated in {rect}")
        last_tw.write_text(page)
```

### Saving

```python
with open(dst, "wb") as f:
    f.write(doc.tobytes(garbage=4, deflate=True))
doc.close()
```

Note: this helps avoid some file-path locking issues but does not guarantee success if the destination file is already open in another process (e.g., a PDF viewer). Close the viewer first.

## What I've learned about Turkish specifically

### The dotless-i problem
Turkish has two distinct i characters: `ı` (U+0131, dotless, lowercase) and `İ` (U+0130, dotted, uppercase). The standard Latin `i`/`I` pair is different. Python's `.upper()` / `.lower()` use Unicode case mappings, which are not Turkish-locale-aware — so `"i".upper()` returns `"I"` (not `"İ"`), and `"I".lower()` returns `"i"` (not `"ı"`).

Always produce Turkish text with the correct characters directly in the translation string. If programmatic case conversion is unavoidable:

```python
# Turkish-aware uppercase/lowercase
def tr_upper(s): return s.replace('i', 'İ').replace('ı', 'I').upper()
def tr_lower(s): return s.replace('İ', 'i').replace('I', 'ı').lower()
```

### Translation length
Turkish words are often longer than their English equivalents due to agglutination. The font size fallback loop handles most cases. If overflow persists after the smallest size, log the warning from `wipe()` and consider widening the wipe rect (`x0` leftward) on a case-by-case basis.

### Formal register
Medical and patient information documents use formal second-person: **siz** (formal) not **sen** (informal). All translations should use formal register throughout.

### Proper nouns and abbreviations
Keep NHS, NICE, GOSH, UCLH, CI, ABR, CMV, and similar abbreviations in their original Latin form.

## Limitations

- **White-out is visual only**: Drawing a white rectangle paints over the original text in the rendered view but does not remove it from the PDF's internal text layer. The English text may still be selectable or found by search. For PDFs requiring true redaction, use `page.add_redact_annot()` + `page.apply_redactions()` before placing the translation.
- **Scanned/image PDFs**: If the source PDF is image-only or has poor OCR, `get_text("dict")` will return no usable spans. This entire workflow fails in that case. Check first: if `page.get_text("text").strip()` returns very little, the PDF likely needs OCR before translation.
- **Alignment and styling**: The `wipe()` function always left-aligns replacement text. It does not capture original centre/right alignment, italic, or rotation. For documents with centred headings, adjust `align=fitz.TEXT_ALIGN_CENTER` as needed per block.
- **Non-white backgrounds**: The white rect assumption breaks if text sits over a coloured or image background. In that case, skip `draw_rect` and use `page.add_redact_annot()` instead.

## Applying this to any English PDF

1. Check `page.get_text("text")` is non-empty — if not, OCR is needed first
2. Inspect blocks with `get_text("dict")` to map bboxes, sizes, colours, and flags
3. Join spans within each block and translate at block level in formal register
4. Call `wipe()` per block with its bbox, size, and colour; check for overflow warnings
5. Adjust alignment per block if the original used centre or right alignment
6. Save to `<original name> - Turkish.pdf`
