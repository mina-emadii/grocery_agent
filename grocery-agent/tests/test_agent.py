import pytest
from typing import List
from src.models.grocery_item import GroceryItem, DietaryFlag
from src.agent import GroceryAgent
from src.stores.base_store import BaseStore

class MockStore(BaseStore):
    def __init__(self, store_name: str, base_url: str):
        super().__init__(store_name, base_url)
        self.items = {
            "milk": [
                GroceryItem(
                    name="Milk",
                    brand="Dairy Co",
                    form="whole",
                    size="1 gallon",
                    price=3.99,
                    store_name=store_name,
                    store_url=f"{base_url}/milk",
                    dietary_flags=[DietaryFlag.DAIRY_FREE],
                ),
                GroceryItem(
                    name="Milk",
                    brand="Organic Co",
                    form="whole",
                    size="1 gallon",
                    price=4.99,
                    store_name=store_name,
                    store_url=f"{base_url}/milk-organic",
                    dietary_flags=[DietaryFlag.DAIRY_FREE, DietaryFlag.ORGANIC],
                ),
            ],
            "bread": [
                GroceryItem(
                    name="Bread",
                    brand="Bakery Co",
                    form="sliced",
                    size="1 loaf",
                    price=2.99,
                    store_name=store_name,
                    store_url=f"{base_url}/bread",
                    dietary_flags=[],
                ),
                GroceryItem(
                    name="Bread",
                    brand="Health Co",
                    form="sliced",
                    size="1 loaf",
                    price=3.99,
                    store_name=store_name,
                    store_url=f"{base_url}/bread-gluten-free",
                    dietary_flags=[DietaryFlag.GLUTEN_FREE],
                ),
            ],
        }

    async def search_items(self, query: str) -> List[GroceryItem]:
        return self.items.get(query.lower(), [])

    async def get_item_details(self, item_url: str) -> GroceryItem:
        for items in self.items.values():
            for item in items:
                if item.store_url == item_url:
                    return item
        return None

    async def filter_by_dietary_restrictions(
        self,
        items: List[GroceryItem],
        restrictions: List[DietaryFlag]
    ) -> List[GroceryItem]:
        return [
            item for item in items
            if item.matches_dietary_restrictions(restrictions)
        ]

    async def get_current_deals(self) -> List[GroceryItem]:
        return []

    async def check_in_stock(self, item_url: str) -> bool:
        return True

@pytest.mark.asyncio
async def test_search_shopping_list():
    # Initialize stores
    store1 = MockStore("store1", "https://store1.com")
    store2 = MockStore("store2", "https://store2.com")
    agent = GroceryAgent([store1, store2])
    
    # Test basic search
    results = await agent.search_shopping_list(["milk", "bread"])
    assert "milk" in results
    assert "bread" in results
    assert len(results["milk"]) == 4  # 2 items from each store
    assert len(results["bread"]) == 4  # 2 items from each store
    
    # Test with dietary restrictions
    results = await agent.search_shopping_list(
        ["milk", "bread"],
        dietary_restrictions=[DietaryFlag.GLUTEN_FREE]
    )
    assert len(results["bread"]) == 2  # Only gluten-free bread
    assert len(results["milk"]) == 0  # No milk items match gluten-free restriction

@pytest.mark.asyncio
async def test_get_best_deals():
    store1 = MockStore("store1", "https://store1.com")
    store2 = MockStore("store2", "https://store2.com")
    agent = GroceryAgent([store1, store2])
    
    best_deals = await agent.get_best_deals(["milk", "bread"])
    assert "milk" in best_deals
    assert "bread" in best_deals
    assert best_deals["milk"].price == 3.99  # Cheapest milk
    assert best_deals["bread"].price == 2.99  # Cheapest bread

@pytest.mark.asyncio
async def test_get_store_summary():
    store1 = MockStore("store1", "https://store1.com")
    store2 = MockStore("store2", "https://store2.com")
    agent = GroceryAgent([store1, store2])
    
    summary = await agent.get_store_summary(["milk", "bread"])
    assert "store1" in summary
    assert "store2" in summary
    assert summary["store1"]["total"] == 6.98  # 3.99 + 2.99
    assert summary["store2"]["total"] == 6.98  # 3.99 + 2.99 