"""
Extract clean Devanagari verse blocks from a GRETIL corpustei HTML file.

GRETIL corpustei bodies are linear IAST verse text, but the verse-delimiting
reference marker comes in two flavours across files:
  A) a bare label on its own line after the verse   -> `KMgD_1`
  B) an inline reference wrapping the verse end      -> `... // KUrmP_1,1.1 //`
We split on BOTH, drop the markers, then IAST->Devanagari + full clean pass.
Plain single/double dandas (`/`, `//`) that are NOT references stay as line
breaks inside a verse.
"""
import re
import html as _html

from common import strip_iast_markers, iast_to_devanagari, clean_devanagari_block

_TAG = re.compile(r"<[^>]+>")
_SCRIPT = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S)
_SPLIT = ""  # verse-boundary sentinel (never in text)

# Inline reference: `//` then, on the same line, some reference chars containing
# at least one digit, then EITHER a closing `/`/`//` OR the end of the line.
# Examples across GRETIL files:
#   `// KUrmP_1,1.1 //`   `//ViP_1,1.0*2//`   `/AP_1.001ab/`   `// MSpv_4.19`
# A digit after the opening slash(es) is what separates a reference from a plain
# danda: cleaned IAST verse text never contains digits, so any `/` or `//` whose
# content (up to the next slash / line end) holds a digit is a reference, while a
# plain danda (no following digit before the break) is preserved as a line break.
# Opening and closing slash counts both vary across files (1 or 2), and some
# cantos drop the closing slash entirely (`// MSpv_4.19` at line end).
_INLINE_REF = re.compile(r"/{1,2}[^/\n]*?\d[^/\n]*?(?:/{1,2}|$)", re.M)

# A bare label line (format A): short ASCII token, no IAST diacritics.
_LABEL_CORE = re.compile(r"[0-9\s,._*:;@()\[\]{}<>=+/|~%\-]")

# English critical-apparatus text (esp. in *-crit editions) that would otherwise
# be transliterated into Devanagari gibberish. These words never occur in IAST
# Sanskrit, so a single hit means the line is editorial, not verse.
_ENGLISH = re.compile(
    r"\b(before|after|foll?ow(ed|ing)?|by|the|of|and|with|ins|insert(s|ed)?|"
    r"omit(s|ted)?|add(s|ed)?|reading|manuscripts?|mss|edition|editor|notes?|"
    r"variants?|colophon|corr|corrupt|conj|cf|see|line|verse|chapter|page|folio)\b",
    re.I,
)


def _is_label(line: str) -> bool:
    core = _LABEL_CORE.sub("", line)
    if core == "":
        return True                      # pure punctuation / number line
    return core.isascii() and len(core) <= 12


def _is_english(line: str) -> bool:
    return bool(_ENGLISH.search(line))


def html_to_iast_verses(raw_html: str):
    """Yield raw IAST verse blocks (str) from a GRETIL corpustei HTML string."""
    t = _SCRIPT.sub(" ", raw_html)
    t = _TAG.sub("\n", t)
    t = _html.unescape(t)
    lines = [ln.strip() for ln in t.splitlines()]

    # Body starts after the literal 'Text' divider the transform emits.
    try:
        start = next(i for i, ln in enumerate(lines) if ln == "Text")
    except StopIteration:
        start = 0

    # Mark bare-label lines (format A) as boundaries; keep verse lines.
    kept = []
    for ln in lines[start + 1:]:
        if not ln:
            continue
        kept.append(_SPLIT if (_is_label(ln) or _is_english(ln)) else ln)
    text = "\n".join(kept)

    # Mark inline references (format B) as boundaries.
    text = _INLINE_REF.sub(_SPLIT, text)

    for chunk in text.split(_SPLIT):
        chunk = chunk.strip()
        if chunk:
            yield chunk


def legacy_epic_iast_lines(raw_html: str):
    """Yield IAST verse text from a GRETIL legacy 2_epic file (full Mahabharata).

    Each body line is `reference<TAB>verse text`, e.g.
    `01,001.070a\\tabhivādya munīṃs tāṃs tu ...`. We take the text after the tab
    for lines whose reference looks like `NN,NNN.NNN` (book,chapter.verse+pada),
    which also skips the header/transliteration-key block."""
    import re as _re
    t = _SCRIPT.sub(" ", raw_html)
    t = _TAG.sub("\n", t)
    t = _html.unescape(t)
    ref_rx = _re.compile(r"^\d\d,\d")
    for line in t.splitlines():
        line = line.rstrip()
        if "\t" not in line:
            continue
        ref, _, text = line.partition("\t")
        if ref_rx.match(ref.strip()) and text.strip():
            yield text.strip()


def extract_legacy_epic_verses(raw_html: str, strip_accents: bool = True):
    """Full pipeline for a GRETIL legacy epic file -> cleaned Devanagari verses."""
    out = []
    for iast in legacy_epic_iast_lines(raw_html):
        cleaned_iast = strip_iast_markers(iast)
        if not cleaned_iast.strip():
            continue
        try:
            dev = iast_to_devanagari(cleaned_iast)
        except Exception:
            continue
        block = clean_devanagari_block(dev, strip_accents=strip_accents)
        if block and "़" not in block:
            out.append(block)
    return out


def extract_devanagari_verses(raw_html: str, strip_accents: bool = True):
    """Full pipeline: GRETIL HTML -> list of cleaned Devanagari verse blocks."""
    out = []
    for iast in html_to_iast_verses(raw_html):
        cleaned_iast = strip_iast_markers(iast)
        if not cleaned_iast.strip():
            continue
        try:
            dev = iast_to_devanagari(cleaned_iast)
        except Exception:
            continue
        block = clean_devanagari_block(dev, strip_accents=strip_accents)
        # Nukta (़, U+093C) marks Persian/English loan sounds (f, z, q) and is
        # effectively absent from classical Sanskrit verse -> its presence means
        # the block is transliterated editorial/English apparatus. Drop it.
        if block and "़" not in block:
            out.append(block)
    return out
