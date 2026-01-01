import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    logger.warning(f'spaCy model not loaded; using regex fallback: {e}')
    nlp = None

qty_unit_re = re.compile(r"(?P<qty>\d+(?:[\.,]\d+)?)\s*(?P<unit>m2|m3|m|kg|ltr|pcs|units|no\.|number|sq\.m|cubic\s*m|cu\.m|ton|tons)?", re.I)

MATERIAL_KEYWORDS = [
    "cement", "sand", "gravel", "aggregate", "steel", "rebar", "brick", "block", "concrete", "pch", "tile", "paint", "wood", "timber"
]

BRAND_RE = re.compile(r"\b([A-Z][A-Za-z0-9\-]+)\b")


def parse_boq(boq_text: str) -> Dict:
    """Simple BOQ parser that extracts material names, quantities, units, and possible brand tokens.
    This is a heuristic parser intended for prototyping. For production, adapt with domain ontologies or
    an annotated dataset + a trained NER model.
    """
    text = boq_text or ""
    materials = []

    # Basic sentence-level processing with spaCy if available
    sents = [text]
    if nlp:
        doc = nlp(text)
        sents = [sent.text for sent in doc.sents]

    for sent in sents:
        # Try to find quantity + unit
        m = qty_unit_re.search(sent)
        qty = None
        unit = None
        if m:
            qty = m.group('qty')
            unit = m.group('unit')
        # Detect material by keywords
        found = None
        for kw in MATERIAL_KEYWORDS:
            if re.search(rf"\b{kw}\b", sent, re.I):
                found = kw
                break
        # Try to detect brand tokens (heuristic: capitalized words)
        brands = BRAND_RE.findall(sent)
        if found or qty:
            materials.append({
                'raw': sent.strip(),
                'material': found or None,
                'quantity': float(qty.replace(',','.')) if qty else None,
                'unit': unit,
                'brands': brands
            })
    # If nothing found, try noun chunking or fallback to token list
    if not materials:
        tokens = re.findall(r"[A-Za-z0-9\-]+", text)
        materials = [{'raw': text, 'material': None, 'quantity': None, 'unit': None, 'brands': []}]

    return {'materials': materials, 'raw_text': text}
