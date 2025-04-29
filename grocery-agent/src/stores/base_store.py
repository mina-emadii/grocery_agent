from abc import ABC, abstractmethod
from typing import List, Optional
from ..models.grocery_item import GroceryItem, DietaryFlag

class BaseStore(ABC):
    def __init__(self, store_name: str, base_url: str):
        self.store_name = store_name
        self.base_url = base_url

    @abstractmethod
    async def search_items(self, query: str) -> List[GroceryItem]:
        """Search for items matching the query string."""
        pass

    @abstractmethod
    async def get_item_details(self, item_url: str) -> Optional[GroceryItem]:
        """Get detailed information about a specific item."""
        pass

    @abstractmethod
    async def filter_by_dietary_restrictions(
        self, 
        items: List[GroceryItem], 
        restrictions: List[DietaryFlag]
    ) -> List[GroceryItem]:
        """Filter items based on dietary restrictions."""
        pass

    @abstractmethod
    async def get_current_deals(self) -> List[GroceryItem]:
        """Get all items currently on sale."""
        pass

    @abstractmethod
    async def check_in_stock(self, item_url: str) -> bool:
        """Check if an item is currently in stock."""
        pass 