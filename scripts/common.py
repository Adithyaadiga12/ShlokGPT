"""
ShlokGPT — shared text-cleaning utilities.

Every source funnels through `clean_devanagari_block` before it lands in the
training corpus, so the cleaning rules from DATA_REQUIREMENTS.md live in exactly
one place. IAST sources (GRETIL) are first stripped of their romanized reference
markers, transliterated to Devanagari, then run through the same final pass.
"""

import re
import unicodedata

try:
    from indic_transliteration import sanscript
    _HAVE_SANSCRIPT = True
except Exception:  # pragma: no cover - only needed for IAST sources
    _HAVE_SANSCRIPT = False


# --- Unicode ranges -------------------------------------------------------

# Devanagari letters / phonemic signs we KEEP (anusvara, visarga, candrabindu,
# avagraha, vowel signs, viramas, the extra consonants at 0958-095F, and the
# vocalic-R/L vowels). We deliberately exclude digits, dandas and accents below.
_KEEP = (
    "ऀ-ः"   # inverted candrabindu, candrabindu, anusvara, visarga
    "ऄ-ह"   # independent vowels + consonants
    "ऺ-ॏ"   # vowel signs, virama (halant)
    "ॕ-ॣ"   # extra vowel signs + extra consonants + vocalic vowels
    "ॲ-ॿ"   # additional letters (candra a, etc.)
    "ऽ"          # avagraha (already inside range above, listed for clarity)
)

# Vedic pitch accents + Vedic extension blocks — stripped (they inflate vocab
# and only appear in Vedic text; DATA_REQUIREMENTS.md recommends removing them).
_ACCENTS = re.compile(
    "[॒॑॓॔"      # Devanagari stress/accent signs
    "᳐-᳿"                    # Vedic Extensions
    "꣠-ꣿ]"                  # Devanagari Extended (Vedic)
)

# Devanagari digits + dandas — removed from the *corpus* (verse numbers, not text)
_DIGITS = re.compile("[०-३४-९0-9]")
_DANDAS = re.compile("[।॥]")

# Anything that is NOT a kept Devanagari char or whitespace.
_NON_DEVANAGARI = re.compile("[^" + _KEEP + r"\s]")

# Reference / verse-number markers found in raw text, e.g. "॥२-४७॥", "(3.12)",
# "[1.2.3]", "// ViP_1,1.0*1 //", "{...}".
_MARKERS = [
    re.compile(r"//[^/]*//"),          # GRETIL metric reference //ViP_1,1.0//
    re.compile(r"\|\|[^|]*\|\|"),      # ||2-47|| style
    re.compile(r"\([^)]*\d[^)]*\)"),   # (3.12)
    re.compile(r"\[[^\]]*\d[^\]]*\]"), # [1.2.3]
    re.compile(r"\{[^}]*\}"),          # editorial {..}
    re.compile(r"§\S*"),               # GRETIL interlocutor markers
]

# A transliterated reference abbreviation (e.g. "AP ab" -> "अप् अब्", "MSpv") is a
# line whose consonants are ALL halant-terminated with no vowel signs — impossible
# in real Sanskrit, where consonants carry an inherent or marked vowel. Used as the
# final net for reference debris that slips past source-specific segmentation.
_CONSONANT = re.compile(r"[क-ह]")
_CONSONANT_HALANT = re.compile(r"[क-ह]्")
_MATRA = re.compile("[ा-ौॕ-ॣ]")  # vowel signs (matras)


def _is_ref_fragment(line: str) -> bool:
    cons = len(_CONSONANT.findall(line))
    if cons < 2:
        return False
    if len(_CONSONANT_HALANT.findall(line)) != cons:
        return False
    return not _MATRA.search(line)


_HTML_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t]+")
_MULTINL = re.compile(r"\n{2,}")


def strip_iast_markers(text: str) -> str:
    """Remove GRETIL reference markers from *romanized* text before transliterating."""
    text = _HTML_TAG.sub(" ", text)
    for rx in _MARKERS:
        text = rx.sub(" ", text)
    # metric dandas '/' '//' and prose danda '|' used as line separators in GRETIL
    text = text.replace("//", "\n").replace("/", "\n").replace("|", "\n")
    text = re.sub(r"\d+", " ", text)      # strip stray reference digits
    text = re.sub(r"[*@#:]", " ", text)   # insertion/appendix punctuation
    return text


def iast_to_devanagari(text: str) -> str:
    """Transliterate cleaned IAST -> Devanagari (lossless, correct conjuncts)."""
    if not _HAVE_SANSCRIPT:
        raise RuntimeError("indic_transliteration not installed")
    return sanscript.transliterate(text, sanscript.IAST, sanscript.DEVANAGARI)


def clean_devanagari_block(text: str, strip_accents: bool = True) -> str:
    """Apply the full corpus cleaning pass to a Devanagari verse block.

    Returns cleaned text (may be multi-line) or '' if nothing survives.
    """
    text = unicodedata.normalize("NFC", text)
    text = _HTML_TAG.sub(" ", text)
    for rx in _MARKERS:
        text = rx.sub(" ", text)
    text = _DANDAS.sub("\n", text)        # danda -> line break (drop the mark)
    text = _DIGITS.sub("", text)          # strip verse numbers / stray digits
    if strip_accents:
        text = _ACCENTS.sub("", text)
    text = _NON_DEVANAGARI.sub(" ", text) # drop Latin, punctuation, symbols
    # tidy whitespace, keep line structure inside the verse, drop reference debris
    lines = [_WS.sub(" ", ln).strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln and not _is_ref_fragment(ln)]
    out = "\n".join(lines)
    return unicodedata.normalize("NFC", out).strip()


def _akshara_len(s: str) -> int:
    return len(s.replace("\n", "").replace(" ", ""))


def resegment_long(block: str, max_aksharas: int = 200):
    """Split an over-long block (an unsegmented prose/verse run that slipped past
    reference-marker detection) into shloka-sized sub-blocks. Greedily packs the
    block's existing hemistich lines up to `max_aksharas`; a single monster line
    with no internal breaks is hard-split on word boundaries as a last resort.
    Blocks already within the limit are returned unchanged."""
    if _akshara_len(block) <= max_aksharas:
        return [block]
    lines = [ln for ln in block.split("\n") if ln.strip()]
    out, cur, cur_len = [], [], 0
    for ln in lines:
        l = _akshara_len(ln)
        if l > max_aksharas:
            if cur:
                out.append("\n".join(cur)); cur, cur_len = [], 0
            words, piece, plen = ln.split(), [], 0
            for w in words:
                if plen + len(w) > max_aksharas and piece:
                    out.append(" ".join(piece)); piece, plen = [], 0
                piece.append(w); plen += len(w)
            if piece:
                out.append(" ".join(piece))
        else:
            if cur_len + l > max_aksharas and cur:
                out.append("\n".join(cur)); cur, cur_len = [], 0
            cur.append(ln); cur_len += l
    if cur:
        out.append("\n".join(cur))
    return out


def is_valid_verse(text: str, min_chars: int = 10) -> bool:
    """Drop entries shorter than `min_chars` (counting non-space Devanagari)."""
    return len(text.replace("\n", "").replace(" ", "")) >= min_chars


def clean_for_rag(sanskrit: str) -> str:
    """Lighter clean for RAG `sanskrit` field: keep dandas/numbers as-authored,
    only normalize Unicode, strip HTML and accents. Preserves verse identity."""
    sanskrit = unicodedata.normalize("NFC", sanskrit)
    sanskrit = _HTML_TAG.sub("", sanskrit)
    sanskrit = _ACCENTS.sub("", sanskrit)
    return sanskrit.strip()
