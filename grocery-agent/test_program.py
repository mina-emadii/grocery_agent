#!/usr/bin/env python3

import asyncio
import sys
import os

# Add both src and parent directories to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.extend([current_dir, parent_dir])

# Import the CLI module
from src.cli import GroceryListProcessor, print_results

async def test_grocery_agent():
    """Test the grocery agent with a sample shopping list"""
    print("Testing Grocery Agent with Gemini API...")
    
    # Sample shopping list
    shopping_list = """milk
bread
eggs
bananas
chicken
rice
vegetables"""
    
    # Sample dietary restrictions
    dietary_restrictions = ["organic", "halal", "gluten-free"]
    
    print("\nShopping List:")
    print(shopping_list)
    
    print("\nDietary Restrictions:")
    print(", ".join(dietary_restrictions))
    
    # Initialize the processor
    processor = GroceryListProcessor()
    
    print("\nProcessing your shopping list...")
    items = await processor.process_shopping_list(shopping_list, dietary_restrictions)
    
    print("\nProcessed Items:")
    for item in items:
        print(f"- {item}")
    
    print("\nSearching for the best deals...")
    results = await processor.find_best_deals(items, dietary_restrictions)
    
    print_results(results)
    
    print("\n✅ Grocery Agent test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_grocery_agent()) 