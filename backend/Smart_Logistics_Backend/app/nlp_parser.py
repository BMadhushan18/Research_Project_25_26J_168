import re
import logging
from typing import List, Dict, Optional

from .labour_profiles import WORK_TYPE_LABOUR_PROFILES

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

VEHICLE_TOKEN_MAP = [
    (re.compile(r"\btipper(s)?\b", re.I), "Tipper Truck"),
    (re.compile(r"\bdump(er)? truck\b", re.I), "Dump Truck"),
    (re.compile(r"\bconcrete mixer truck\b", re.I), "Concrete Mixer Truck"),
    (re.compile(r"\bmixer truck\b", re.I), "Concrete Mixer Truck"),
    (re.compile(r"\bpickup( truck)?\b", re.I), "Pickup Truck"),
    (re.compile(r"\bpanel van\b", re.I), "Panel Van"),
    (re.compile(r"\blow[-\s]?bed\b", re.I), "Low-bed Trailer"),
    (re.compile(r"\bflatbed\b", re.I), "Large Truck"),
    (re.compile(r"\bcrane truck\b", re.I), "Mobile Crane"),
    (re.compile(r"\btractor\b", re.I), "Small Truck"),
]

MACHINERY_TOKEN_MAP = [
    (re.compile(r"\bconcrete pump\b", re.I), "Concrete Pump"),
    (re.compile(r"\bboom pump\b", re.I), "Concrete Pump"),
    (re.compile(r"\bconcrete mixer\b", re.I), "Concrete Mixer"),
    (re.compile(r"\btransit mixer\b", re.I), "Concrete Mixer Truck"),
    (re.compile(r"\bexcavator\b", re.I), "Excavator"),
    (re.compile(r"\bbulldozer\b", re.I), "Bulldozer"),
    (re.compile(r"\bwheel loader\b", re.I), "Loader"),
    (re.compile(r"\bloader\b", re.I), "Loader"),
    (re.compile(r"\bscissor lift\b", re.I), "Scissor Lift"),
    (re.compile(r"\bboom lift\b", re.I), "Boom Lift"),
    (re.compile(r"\bjack hammer\b", re.I), "Jack Hammer"),
    (re.compile(r"\bformwork\b", re.I), "Formwork System"),
]

BRAND_RE = re.compile(r"\b([A-Z][A-Za-z0-9\-]+)\b")


def parse_boq(boq_text: str) -> Dict:
    """Simple BOQ parser that extracts material names, quantities, units, and possible brand tokens.
    This is a heuristic parser intended for prototyping. For production, adapt with domain ontologies or
    an annotated dataset + a trained NER model.
    """
    text = boq_text or ""
    detected_work_type = _detect_work_type(text)
    materials = []
    vehicle_hints = set()
    machinery_hints = set()

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
        lowered = sent.lower()
        for pattern, label in VEHICLE_TOKEN_MAP:
            if pattern.search(lowered):
                vehicle_hints.add(label)
        for pattern, label in MACHINERY_TOKEN_MAP:
            if pattern.search(lowered):
                machinery_hints.add(label)

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

    return {
        'materials': materials,
        'raw_text': text,
        'work_type': detected_work_type,
        'vehicle_hints': sorted(vehicle_hints),
        'machinery_hints': sorted(machinery_hints),
    }


def _detect_work_type(text: str) -> Optional[str]:
    """Match the BOQ narrative against curated work-type keywords."""
    lowered = (text or '').lower()
    for work_type, profile in WORK_TYPE_LABOUR_PROFILES.items():
        for keyword in profile.get('keywords', []):
            if keyword.lower() in lowered:
                return work_type
        for token in profile.get('fallback_tokens', []):
            if token and token.lower() in lowered:
                return work_type
    return None
