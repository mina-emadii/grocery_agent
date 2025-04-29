from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class DietaryFlag(Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    GLUTEN_FREE = "gluten_free"
    NUT_FREE = "nut_free"
    DAIRY_FREE = "dairy_free"
    LOW_SUGAR = "low_sugar"
    ORGANIC = "organic"

@dataclass
class GroceryItem:
    name: str
    brand: str
    form: str  # e.g., "whole", "sliced", "powdered"
    size: str  # e.g., "16oz", "1lb"
    price: float
    store_name: str
    store_url: str
    dietary_flags: List[DietaryFlag]
    in_stock: bool = True
    sale_price: Optional[float] = None
    sale_end_date: Optional[str] = None

    def matches_dietary_restrictions(self, restrictions: List[DietaryFlag]) -> bool:
        """Check if the item matches all dietary restrictions."""
        return all(flag in self.dietary_flags for flag in restrictions)

    def get_current_price(self) -> float:
        """Get the current price, considering any active sales."""
        return self.sale_price if self.sale_price is not None else self.price

    def is_on_sale(self) -> bool:
        """Check if the item is currently on sale."""
        return self.sale_price is not None

    def __str__(self) -> str:
        return f"{self.brand} {self.name} ({self.size}) - ${self.get_current_price():.2f} at {self.store_name}" 