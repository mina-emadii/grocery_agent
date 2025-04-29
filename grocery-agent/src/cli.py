import asyncio
import argparse
from typing import List
from .agent import GroceryAgent
from .models.grocery_item import DietaryFlag
from .stores.generic_store import GenericStore

async def main():
    parser = argparse.ArgumentParser(description="Grocery Price Finder Agent")
    parser.add_argument(
        "--items",
        nargs="+",
        required=True,
        help="List of items to search for"
    )
    parser.add_argument(
        "--stores",
        nargs="+",
        default=["store1", "store2"],
        help="List of stores to search in"
    )
    parser.add_argument(
        "--dietary",
        nargs="+",
        choices=[flag.value for flag in DietaryFlag],
        help="Dietary restrictions to apply"
    )
    
    args = parser.parse_args()
    
    # Convert dietary restrictions to enum values
    dietary_restrictions = [
        DietaryFlag(restriction)
        for restriction in (args.dietary or [])
    ]
    
    # Initialize stores
    stores = [
        GenericStore(
            store_name=store,
            base_url=f"https://{store}.com"  # This would be replaced with actual store URLs
        )
        for store in args.stores
    ]
    
    # Initialize agent
    agent = GroceryAgent(stores)
    
    # Search for items
    print("\nSearching for items...")
    results = await agent.search_shopping_list(
        args.items,
        dietary_restrictions,
        args.stores
    )
    
    # Print results
    print("\nSearch Results:")
    print("=" * 50)
    
    for item, matches in results.items():
        print(f"\n{item}:")
        if not matches:
            print("  No matches found")
            continue
            
        for match in matches:
            print(f"  {match}")
            if match.is_on_sale():
                print(f"    SALE! Regular price: ${match.price:.2f}")
    
    # Get best deals
    print("\nBest Deals:")
    print("=" * 50)
    best_deals = await agent.get_best_deals(
        args.items,
        dietary_restrictions,
        args.stores
    )
    
    for item, deal in best_deals.items():
        print(f"\n{item}:")
        print(f"  {deal}")
    
    # Get store summary
    print("\nStore Summary:")
    print("=" * 50)
    store_summary = await agent.get_store_summary(
        args.items,
        dietary_restrictions,
        args.stores
    )
    
    for store, summary in store_summary.items():
        print(f"\n{store}:")
        print(f"  Total: ${summary['total']:.2f}")
        print("  Items:")
        for item, price in summary["items"].items():
            print(f"    {item}: ${price:.2f}")

if __name__ == "__main__":
    asyncio.run(main()) 