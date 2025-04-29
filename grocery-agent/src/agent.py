from typing import List, Dict, Optional
from .models.grocery_item import GroceryItem, DietaryFlag
from .stores.base_store import BaseStore

class GroceryAgent:
    def __init__(self, stores: List[BaseStore]):
        self.stores = stores

    async def search_shopping_list(
        self,
        items: List[str],
        dietary_restrictions: List[DietaryFlag] = None,
        target_stores: List[str] = None
    ) -> Dict[str, List[GroceryItem]]:
        """
        Search for items across multiple stores, applying dietary restrictions.
        
        Args:
            items: List of items to search for
            dietary_restrictions: List of dietary restrictions to apply
            target_stores: List of store names to search in (if None, search all stores)
            
        Returns:
            Dictionary mapping item names to lists of matching GroceryItems
        """
        results: Dict[str, List[GroceryItem]] = {}
        
        # Filter stores if target_stores is specified
        stores_to_search = [
            store for store in self.stores
            if target_stores is None or store.store_name in target_stores
        ]
        
        for item in items:
            item_results = []
            
            # Search in each store
            for store in stores_to_search:
                try:
                    # Search for the item
                    store_results = await store.search_items(item)
                    
                    # Apply dietary restrictions if specified
                    if dietary_restrictions:
                        store_results = await store.filter_by_dietary_restrictions(
                            store_results,
                            dietary_restrictions
                        )
                    
                    # Add store results to item results
                    item_results.extend(store_results)
                    
                except Exception as e:
                    print(f"Error searching for {item} in {store.store_name}: {e}")
            
            # Sort results by price
            item_results.sort(key=lambda x: x.get_current_price())
            results[item] = item_results
        
        return results

    async def get_best_deals(
        self,
        items: List[str],
        dietary_restrictions: List[DietaryFlag] = None,
        target_stores: List[str] = None
    ) -> Dict[str, GroceryItem]:
        """
        Find the best deals for each item in the shopping list.
        
        Args:
            items: List of items to search for
            dietary_restrictions: List of dietary restrictions to apply
            target_stores: List of store names to search in (if None, search all stores)
            
        Returns:
            Dictionary mapping item names to the best-priced GroceryItem
        """
        # Get all matching items
        all_results = await self.search_shopping_list(
            items,
            dietary_restrictions,
            target_stores
        )
        
        # Find the best deal for each item
        best_deals = {}
        for item, matches in all_results.items():
            if matches:
                # First item is the cheapest (due to sorting in search_shopping_list)
                best_deals[item] = matches[0]
        
        return best_deals

    async def get_store_summary(
        self,
        items: List[str],
        dietary_restrictions: List[DietaryFlag] = None,
        target_stores: List[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get a summary of total prices for each store.
        
        Args:
            items: List of items to search for
            dietary_restrictions: List of dietary restrictions to apply
            target_stores: List of store names to search in (if None, search all stores)
            
        Returns:
            Dictionary mapping store names to their total prices
        """
        # Get all matching items
        all_results = await self.search_shopping_list(
            items,
            dietary_restrictions,
            target_stores
        )
        
        # Calculate total price for each store
        store_totals: Dict[str, Dict[str, float]] = {}
        
        for item, matches in all_results.items():
            for match in matches:
                store_name = match.store_name
                if store_name not in store_totals:
                    store_totals[store_name] = {"total": 0.0, "items": {}}
                
                # Only update if this is the first/cheapest match for this item in this store
                if item not in store_totals[store_name]["items"]:
                    store_totals[store_name]["items"][item] = match.get_current_price()
                    store_totals[store_name]["total"] += match.get_current_price()
        
        return store_totals 