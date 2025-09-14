from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel


# ---------- Leaf nodes ----------

class Text(BaseModel):
    content: str
    link: Optional[str] = None


class Annotations(BaseModel):
    bold: bool
    italic: bool
    strikethrough: bool
    underline: bool
    code: bool
    color: str  # Notion 색상 문자열 그대로 유지 (e.g., "default")


class RichText(BaseModel):
    type: str
    text: Text
    annotations: Annotations
    plain_text: str


# ---------- Mid-level nodes ----------

class TableRow(BaseModel):
    cells: List[List[RichText]]


class Block(BaseModel):
    object: str
    id: str
    type: str
    table_row: Optional[TableRow] = None


# ---------- Top-level ----------

class BlockDetail(BaseModel):
    object: str
    results: List[Block]
    type: str