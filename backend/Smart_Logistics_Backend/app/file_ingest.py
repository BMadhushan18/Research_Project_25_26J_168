"""Helpers to extract BOQ text/materials from uploaded documents.
Supports PDF, Excel, Word, CSV, and plain text. Each extractor is defensive and
returns best-effort text; optional structured material rows are emitted when a
sheet includes recognizable columns.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Tuple, TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # Optional parser types for static analysis only
    try:
        from PyPDF2 import PdfReader  # type: ignore
    except Exception:
        PdfReader = object  # type: ignore
    try:
        import docx  # type: ignore
    except Exception:
        docx = object  # type: ignore


class MissingDependencyError(RuntimeError):
    """Raised when an optional parser dependency is missing."""


@dataclass
class IngestResult:
    raw_text: str
    materials: List[Dict] | None = None


def _df_to_text(df) -> Tuple[str, List[Dict]]:
    """Flatten a DataFrame into text lines and optional structured materials."""
    try:
        import pandas as pd  # noqa: F401
    except Exception:
        # If pandas is absent this function wouldn't have been called
        pass
    df = df.fillna('')
    lines = df.astype(str).agg(' '.join, axis=1).tolist()

    # Try to map tabular rows into material dicts if common columns are present
    lower_cols = {c.lower(): c for c in df.columns}
    desc_col = next((lower_cols[c] for c in lower_cols if any(k in c for k in ('description', 'item', 'work', 'activity'))), None)
    qty_col = next((lower_cols[c] for c in lower_cols if any(k in c for k in ('qty', 'quantity'))), None)
    unit_col = next((lower_cols[c] for c in lower_cols if 'unit' in c), None)
    mats: List[Dict] = []
    if desc_col:
        for _, row in df.iterrows():
            desc = str(row.get(desc_col, '')).strip()
            if not desc:
                continue
            qty_val = row.get(qty_col) if qty_col else None
            try:
                qty = float(qty_val) if qty_val not in (None, '') else None
            except Exception:
                qty = None
            unit = str(row.get(unit_col)).strip() if unit_col and row.get(unit_col) not in (None, '') else None
            mats.append({
                'raw': desc,
                'material': None,
                'quantity': qty,
                'unit': unit,
                'brands': []
            })
    return '\n'.join(lines), (mats or None)


def _extract_pdf(data: bytes) -> str:
    try:
        from PyPDF2 import PdfReader  # type: ignore[import]
    except ImportError as exc:
        raise MissingDependencyError('Install PyPDF2 to parse PDF files') from exc
    reader = PdfReader(BytesIO(data))
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or '')
        except Exception as e:  # pragma: no cover - defensive only
            logger.warning(f'Failed to extract text from a PDF page: {e}')
    return '\n'.join(texts)


def _extract_docx(data: bytes) -> str:
    try:
        import docx  # type: ignore[import]
    except ImportError as exc:
        raise MissingDependencyError('Install python-docx to parse Word files') from exc
    document = docx.Document(BytesIO(data))
    return '\n'.join(p.text for p in document.paragraphs)


def _extract_excel(data: bytes) -> Tuple[str, List[Dict] | None]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise MissingDependencyError('Install pandas/openpyxl to parse Excel files') from exc
    df = pd.read_excel(BytesIO(data), engine=None)
    return _df_to_text(df)


def _extract_csv(data: bytes) -> Tuple[str, List[Dict] | None]:
    try:
        import pandas as pd
    except ImportError as exc:
        raise MissingDependencyError('Install pandas to parse CSV files') from exc
    df = pd.read_csv(BytesIO(data))
    return _df_to_text(df)


def ingest_boq_bytes(data: bytes, filename: str) -> IngestResult:
    if not data:
        raise ValueError('Uploaded file is empty')
    ext = Path(filename).suffix.lower()
    materials: List[Dict] | None = None

    if ext in {'.txt', '.log'}:
        text = data.decode('utf-8', errors='ignore')
    elif ext in {'.csv'}:
        text, materials = _extract_csv(data)
    elif ext in {'.xls', '.xlsx'}:
        text, materials = _extract_excel(data)
    elif ext == '.pdf':
        text = _extract_pdf(data)
    elif ext in {'.doc', '.docx'}:
        text = _extract_docx(data)
    else:
        # Best effort: treat as text
        text = data.decode('utf-8', errors='ignore')

    if not text.strip():
        raise ValueError('No readable text found in uploaded file')
    return IngestResult(raw_text=text, materials=materials)


def ingest_boq_upload(file) -> IngestResult:
    data = file.file.read() if hasattr(file, 'file') else None
    if data is None:
        # FastAPI UploadFile exposes .read (awaitable), but we accept sync for testing
        data = file.read()
    if hasattr(file, 'seek'):
        try:
            file.seek(0)
        except Exception:
            pass
    return ingest_boq_bytes(data, file.filename or 'boq.txt')
