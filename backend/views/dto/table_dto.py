from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel

class StockTableRow(BaseModel):
    name: str
    basic_quantity: float
    remaining_quantity: float
    count: int

class Ingredient(BaseModel):
    name: str
    quantity: float
    unit: str

class RecipeTableRow(BaseModel):
    name: str
    recipe: str
    ingredients: List[Ingredient]
