#!/usr/bin/env python3

import asyncio
import argparse
from typing import List, Dict, Any
import os
import sys
import google.generativeai as genai
import json

# Import our price fetcher
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.price_fetcher import PriceFetcher

# Direct API key
GEMINI_API_KEY = "AIzaSyACFB8g_GgFoVC8CSeDL4qJiPkWACnCeZ0"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Comprehensive list of dietary restrictions
DIETARY_RESTRICTIONS = {
    "religious": [
        "halal",
        "kosher",
        "jain",
        "hindu-vegetarian"
    ],
    "lifestyle": [
        "vegan",
        "vegetarian",
        "pescatarian",
        "keto",
        "paleo",
        "mediterranean",
        "dash",
        "low-carb",
        "low-fat",
        "low-sodium",
        "low-sugar",
        "low-calorie"
    ],
    "allergies": [
        "gluten-free",
        "nut-free",
        "dairy-free",
        "egg-free",
        "soy-free",
        "shellfish-free",
        "fish-free",
        "wheat-free",
        "corn-free"
    ],
    "preferences": [
        "organic",
        "non-gmo",
        "sugar-free",
        "artificial-sweetener-free",
        "preservative-free",
        "hormone-free",
        "antibiotic-free",
        "cage-free",
        "free-range",
        "grass-fed",
        "wild-caught",
        "sustainable",
        "fair-trade"
    ]
}

class GroceryListProcessor:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.price_fetcher = PriceFetcher()

    async def process_shopping_list(self, raw_input: str, dietary_restrictions: List[str]) -> List[Dict[str, Any]]:
        """Process the raw shopping list input using Gemini to standardize item names"""
        prompt = f"""
        Given this shopping list: {raw_input}
        And these dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}

        Please convert this into a standardized list of grocery items.
        For each item:
        1. Use common grocery store naming conventions
        2. Be specific about quantities if mentioned
        3. Consider the dietary restrictions when suggesting specific varieties
        4. If multiple dietary restrictions are specified, ensure the item meets ALL restrictions
        5. For religious restrictions (halal, kosher), ensure proper certification
        6. For lifestyle diets (keto, paleo), ensure macronutrient compliance
        7. For allergies, ensure complete avoidance of allergens
        8. For preferences (organic, non-gmo), ensure proper certification

        Return the list as a JSON array of strings, with each string being a standardized item name.
        Example: ["organic whole milk 1 gallon", "gluten-free bread 1 loaf"]
        """

        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            # Extract the text from the response and parse it as JSON
            response_text = response.text
            # Find the JSON array in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                items = json.loads(json_str)
                return items
            else:
                # If no JSON array found, return the raw input split by lines
                return [item.strip() for item in raw_input.split('\n') if item.strip()]
        except Exception as e:
            print(f"Error processing shopping list: {e}")
            # Return the raw input split by lines as a fallback
            return [item.strip() for item in raw_input.split('\n') if item.strip()]

    async def find_best_deals(self, items: List[str], dietary_restrictions: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Find the best deals for each item across all stores"""
        results = {}
        
        async with self.price_fetcher as pf:
            for item in items:
                print(f"\nSearching for: {item}")
                prices = await pf.get_all_prices(item, dietary_restrictions)
                results[item] = []
                
                for store, data in prices.items():
                    if data["availability"] and all(rest in data["dietary_info"]["restrictions_handled"] 
                                                  for rest in dietary_restrictions):
                        results[item].append({
                            "store": store,
                            "price": data["price"],
                            "dietary_info": data["dietary_info"]
                        })
                
                # Sort by price
                results[item].sort(key=lambda x: x["price"])
        
        return results

def print_results(results: Dict[str, List[Dict[str, Any]]]):
    """Print the results in a user-friendly format"""
    print("\n=== Shopping Results ===")
    total_by_store = {}
    
    for item, stores in results.items():
        print(f"\n{item}:")
        if not stores:
            print("  No compatible options found")
            continue
            
        for store_data in stores:
            store = store_data["store"]
            price = store_data["price"]
            print(f"  {store.title()}: ${price:.2f}")
            
            # Track total by store
            if store not in total_by_store:
                total_by_store[store] = 0
            if stores[0]["store"] == store:  # Only add the cheapest option
                total_by_store[store] += price
    
    print("\n=== Total Cost by Store (using cheapest compatible items) ===")
    for store, total in sorted(total_by_store.items(), key=lambda x: x[1]):
        print(f"{store.title()}: ${total:.2f}")

def print_dietary_restrictions_help():
    """Print all available dietary restrictions grouped by category"""
    print("\nAvailable Dietary Restrictions:")
    print("===============================")
    
    for category, restrictions in DIETARY_RESTRICTIONS.items():
        print(f"\n{category.title()}:")
        for restriction in restrictions:
            print(f"  - {restriction}")
    
    print("\nYou can combine multiple restrictions from any category.")
    print("Example: 'halal organic gluten-free keto'")

def validate_dietary_restrictions(restrictions: List[str]) -> List[str]:
    """Validate and normalize dietary restrictions"""
    all_restrictions = [r.lower() for category in DIETARY_RESTRICTIONS.values() for r in category]
    normalized = []
    
    for restriction in restrictions:
        restriction = restriction.lower()
        if restriction in all_restrictions:
            normalized.append(restriction)
        else:
            print(f"Warning: Unknown dietary restriction '{restriction}' will be ignored")
    
    return normalized

async def main():
    parser = argparse.ArgumentParser(description="Find the best grocery deals based on your shopping list")
    parser.add_argument("--list", "-l", help="Shopping list file (one item per line)")
    parser.add_argument("--dietary", "-d", nargs="+", help="Dietary restrictions (e.g., vegan gluten-free)")
    parser.add_argument("--show-restrictions", "-s", action="store_true", help="Show all available dietary restrictions")
    args = parser.parse_args()

    if args.show_restrictions:
        print_dietary_restrictions_help()
        return

    # Get shopping list
    if args.list:
        try:
            with open(args.list, 'r') as f:
                shopping_list = f.read()
        except Exception as e:
            print(f"Error reading shopping list file: {e}")
            return
    else:
        print("Enter your shopping list (one item per line, press Ctrl+D when done):")
        shopping_list = sys.stdin.read()

    # Get dietary restrictions if not provided
    dietary_restrictions = args.dietary if args.dietary else []
    if not args.dietary:
        print("\nEnter dietary restrictions (space-separated, press Enter if none):")
        print("Type '--show-restrictions' to see all available options")
        restrictions_input = input().strip()
        if restrictions_input == "--show-restrictions":
            print_dietary_restrictions_help()
            print("\nEnter dietary restrictions (space-separated, press Enter if none):")
            restrictions_input = input().strip()
        if restrictions_input:
            dietary_restrictions = restrictions_input.split()

    # Validate dietary restrictions
    dietary_restrictions = validate_dietary_restrictions(dietary_restrictions)

    processor = GroceryListProcessor()
    
    print("\nProcessing your shopping list...")
    items = await processor.process_shopping_list(shopping_list, dietary_restrictions)
    
    print("\nSearching for the best deals...")
    results = await processor.find_best_deals(items, dietary_restrictions)
    
    print_results(results)

if __name__ == "__main__":
    asyncio.run(main()) 