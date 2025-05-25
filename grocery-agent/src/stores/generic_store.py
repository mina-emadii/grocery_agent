from typing import List, Optional
from playwright.async_api import async_playwright, Browser, Page
from .base_store import BaseStore
from ..models.grocery_item import GroceryItem, DietaryFlag

class GenericStore(BaseStore):
    def __init__(self, store_name: str, base_url: str):
        super().__init__(store_name, base_url)
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None

    async def _ensure_browser(self):
        """Ensure browser is initialized."""
        if not self._browser:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(headless=True)
            self._page = await self._browser.new_page()

    async def _close_browser(self):
        """Close browser and cleanup resources."""
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None

    async def search_items(self, query: str) -> List[GroceryItem]:
        """Search for items matching the query string."""
        await self._ensure_browser()
        try:
            # Navigate to search page
            await self._page.goto(f"{self.base_url}/search?q={query}")
            
            # Wait for search results to load
            await self._page.wait_for_selector(".product-item")
            
            # Extract product information
            items = []
            for product in await self._page.query_selector_all(".product-item"):
                name = await product.query_selector(".product-name")
                price = await product.query_selector(".product-price")
                brand = await product.query_selector(".product-brand")
                
                if name and price and brand:
                    items.append(GroceryItem(
                        name=await name.text_content(),
                        brand=await brand.text_content(),
                        form="standard",  # This would need to be extracted from product details
                        size="standard",  # This would need to be extracted from product details
                        price=float(await price.text_content().replace("$", "")),
                        store_name=self.store_name,
                        store_url=await product.get_attribute("href"),
                        dietary_flags=[],  # This would need to be extracted from product details
                    ))
            
            return items
        except Exception as e:
            print(f"Error searching items: {e}")
            return []

    async def get_item_details(self, item_url: str) -> Optional[GroceryItem]:
        """Get detailed information about a specific item."""
        await self._ensure_browser()
        try:
            await self._page.goto(item_url)
            await self._page.wait_for_selector(".product-details")
            
            # Extract detailed product information
            name = await self._page.query_selector(".product-name")
            price = await self._page.query_selector(".product-price")
            brand = await self._page.query_selector(".product-brand")
            size = await self._page.query_selector(".product-size")
            dietary_info = await self._page.query_selector_all(".dietary-info")
            
            if not all([name, price, brand]):
                return None
            
            # Extract dietary flags
            dietary_flags = []
            for info in dietary_info:
                flag_text = await info.text_content()
                try:
                    dietary_flags.append(DietaryFlag(flag_text.lower()))
                except ValueError:
                    continue
            
            return GroceryItem(
                name=await name.text_content(),
                brand=await brand.text_content(),
                form="standard",  # This would need to be extracted from product details
                size=await size.text_content() if size else "standard",
                price=float(await price.text_content().replace("$", "")),
                store_name=self.store_name,
                store_url=item_url,
                dietary_flags=dietary_flags,
            )
        except Exception as e:
            print(f"Error getting item details: {e}")
            return None

    async def filter_by_dietary_restrictions(
        self, 
        items: List[GroceryItem], 
        restrictions: List[DietaryFlag]
    ) -> List[GroceryItem]:
        """Filter items based on dietary restrictions."""
        return [
            item for item in items 
            if item.matches_dietary_restrictions(restrictions)
        ]

    async def get_current_deals(self) -> List[GroceryItem]:
        """Get all items currently on sale."""
        await self._ensure_browser()
        try:
            await self._page.goto(f"{self.base_url}/deals")
            await self._page.wait_for_selector(".deal-item")
            
            deals = []
            for deal in await self._page.query_selector_all(".deal-item"):
                name = await deal.query_selector(".product-name")
                price = await deal.query_selector(".product-price")
                sale_price = await deal.query_selector(".sale-price")
                end_date = await deal.query_selector(".sale-end-date")
                
                if name and price and sale_price:
                    deals.append(GroceryItem(
                        name=await name.text_content(),
                        brand="Unknown",  # This would need to be extracted
                        form="standard",
                        size="standard",
                        price=float(await price.text_content().replace("$", "")),
                        store_name=self.store_name,
                        store_url=await deal.get_attribute("href"),
                        dietary_flags=[],
                        sale_price=float(await sale_price.text_content().replace("$", "")),
                        sale_end_date=await end_date.text_content() if end_date else None,
                    ))
            
            return deals
        except Exception as e:
            print(f"Error getting current deals: {e}")
            return []

    async def check_in_stock(self, item_url: str) -> bool:
        """Check if an item is currently in stock."""
        await self._ensure_browser()
        try:
            await self._page.goto(item_url)
            await self._page.wait_for_selector(".stock-status")
            
            stock_status = await self._page.query_selector(".stock-status")
            if stock_status:
                status_text = await stock_status.text_content()
                return "in stock" in status_text.lower()
            return False
        except Exception as e:
            print(f"Error checking stock status: {e}")
            return False 