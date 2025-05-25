import os
import json
import time
import requests
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

if not OPENAI_API_KEY or not SERPAPI_KEY:
    raise ValueError("Both OPENAI_API_KEY and SERPAPI_KEY environment variables are required")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def parse_dietary_restrictions(prompt: str) -> List[str]:
    """Extract dietary restrictions from the prompt using GPT-4"""
    
    system_prompt = """You are a dietary restriction parser that extracts dietary restrictions from shopping requests.
Return ONLY a JSON array of dietary restrictions - no other text. Examples of restrictions:
- vegan
- vegetarian
- gluten-free
- dairy-free
- nut-free
- kosher
- halal
- organic
- sugar-free
- low-carb
- keto
- paleo

If no restrictions are mentioned, return an empty array []."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        restrictions = json.loads(response.choices[0].message.content)
        return restrictions if isinstance(restrictions, list) else []
        
    except Exception:
        return []

def parse_shopping_prompt(prompt: str) -> Dict:
    """Use GPT-4 to parse the shopping prompt into structured data"""
    
    # First get dietary restrictions
    dietary_restrictions = parse_dietary_restrictions(prompt)
    
    system_prompt = """You are a helpful shopping assistant that extracts structured information from natural language shopping requests.
Parse the user's prompt and extract:
1. Shopping list items
2. Budget (total or per item)
3. Location (city/state)

Return ONLY a JSON object in this exact format - no other text:
{
    "items": ["item1", "item2", ...],
    "budget": {
        "total": null or number,
        "per_item": null or number,
        "type": "total" or "per_item" or "none"
    },
    "location": {
        "city": "city name" or null,
        "state": "state name" or "California" if not specified
    }
}

If any information is missing, use these defaults:
- Location: California (state) if not specified
- Budget: {"total": null, "per_item": null, "type": "none"}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        parsed_data = json.loads(response.choices[0].message.content)
        # Add the dietary restrictions to the parsed data
        parsed_data["dietary_restrictions"] = dietary_restrictions
        return parsed_data
        
    except Exception:
        return {
            "items": [],
            "dietary_restrictions": dietary_restrictions,
            "budget": {"total": None, "per_item": None, "type": "none"},
            "location": {"city": None, "state": "California"}
        }

def get_store_configs(location: Dict) -> List[Dict]:
    """Get store configurations based on location"""
    return [
        {
            "name": "Safeway",
            "location": f"{location['city'] or 'Local'}, {location['state']}",
            "type": "Supermarket chain"
        },
        {
            "name": "Sprouts",
            "location": f"{location['city'] or 'Local'}, {location['state']}",
            "type": "Farmers market style grocery store"
        }
    ]

def search_google_shopping(item: str, store: Dict, dietary_restrictions: List[str]) -> List[Dict]:
    """Search Google Shopping for products using SerpAPI"""
    
    # Get zip code from location or use default
    zip_code = "90210"  # Default to Beverly Hills if no specific location
    if store["location"]:
        location = store["location"].lower()
        if "san francisco" in location:
            zip_code = "94103"
        elif "los angeles" in location or "la" in location:
            zip_code = "90012"
        elif "sacramento" in location:
            zip_code = "95814"
    
    # Build query with dietary restrictions
    restrictions_str = ' '.join(dietary_restrictions) if dietary_restrictions else ''
    query = f"{restrictions_str} {item} {store['name']}"
    
    # Set up SerpAPI parameters
    params = {
        "engine": "google_shopping",
        "q": query,
        "location": zip_code,
        "api_key": SERPAPI_KEY,
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()
        
        if "error" in data:
            return []
            
        products = data.get("shopping_results", [])
        
        # Convert SerpAPI results to our format
        formatted_products = []
        for p in products:
            # Extract numeric price
            price_str = p.get("price", "").replace("$", "").replace(",", "")
            try:
                price = float(price_str)
            except (ValueError, TypeError):
                continue
                
            # Extract unit information
            title = p.get("title", "")
            unit = "each"  # default unit
            for unit_type in ["oz", "lb", "gal", "ml", "l", "kg", "g"]:
                if unit_type in title.lower():
                    unit = unit_type
                    break
            
            # Check if product matches dietary restrictions
            matches_restrictions = True
            for restriction in dietary_restrictions:
                if restriction.lower() not in title.lower():
                    matches_restrictions = False
                    break
            
            if matches_restrictions:
                formatted_products.append({
                    "name": title,
                    "price": price,
                    "unit": unit,
                    "unit_price": price,  # We could parse unit price if available
                    "store": store["name"],
                    "organic": "organic" in title.lower(),
                    "availability": "In Stock" if p.get("availability") != "Out of stock" else "Out of Stock",
                    "source": f"Google Shopping - {p.get('source', 'Unknown seller')}",
                    "link": p.get("link", "")
                })
        
        # Sort by price and return top 3
        formatted_products.sort(key=lambda x: x["price"])
        return formatted_products[:3]
        
    except Exception:
        return []

def get_product_recommendations(store: Dict, item: str, dietary_restrictions: List[str], budget: Dict) -> List[Dict]:
    """Get product recommendations using Google Shopping search"""
    
    # Get real-time product information
    products = search_google_shopping(item, store, dietary_restrictions)
    
    if not products:
        # Fall back to AI estimation if real-time search fails
        budget_constraint = ""
        if budget["type"] == "per_item" and budget["per_item"]:
            budget_constraint = f"The price must be under ${budget['per_item']:.2f} per item."
        elif budget["type"] == "total" and budget["total"]:
            budget_constraint = f"Consider that the total budget for all items is ${budget['total']:.2f}."
        
        prompt = f"""You are a helpful grocery shopping assistant with extensive knowledge of {store['name']} in {store['location']}.
{store['name']} is a {store['type']}.

A customer is looking for: {item}
Their dietary restrictions are: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
{budget_constraint}

Please provide 3 realistic product recommendations that would be available at {store['name']}, considering:
1. The dietary restrictions
2. Typical {store['name']} pricing
3. Common brands found at {store['name']}
4. Product availability
5. Unit sizes commonly found at {store['name']}
6. Budget constraints (if any)

Return the recommendations in this exact format, and ONLY this format - no other text:
[
    {{
        "name": "Product Name with Brand",
        "price": 0.00,
        "unit": "oz/lb/gal/etc",
        "unit_price": 0.00,
        "store": "{store['name']}",
        "organic": true/false,
        "availability": "In Stock",
        "source": "AI estimation"
    }}
]"""

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful grocery shopping assistant with extensive knowledge of grocery store products, prices, and availability. You MUST return only valid JSON arrays containing product information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            products = json.loads(response.choices[0].message.content)
            if isinstance(products, list) and len(products) > 0:
                return products
            else:
                return []
            
        except Exception:
            return []
    
    return products

def get_ai_recommendations(all_products: List[Dict], item: str, dietary_restrictions: List[str], budget: Dict) -> List[Dict]:
    """Use GPT-4 to select the best 3 products across all stores"""
    
    if not all_products:
        return []
    
    budget_constraint = ""
    if budget["type"] == "per_item" and budget["per_item"]:
        budget_constraint = f"Each item must be under ${budget['per_item']:.2f}."
    elif budget["type"] == "total" and budget["total"]:
        budget_constraint = f"The total cost of selected items should not exceed ${budget['total']:.2f}."
        
    prompt = f"""Given these products for '{item}' with dietary restrictions {dietary_restrictions},
select the 3 best options considering:
1. Price (lower is better)
2. Compatibility with dietary restrictions
3. Value for money
4. Product quality and brand reputation
5. Store reputation
6. Budget constraints: {budget_constraint if budget_constraint else "No specific budget constraints"}
7. Data source reliability (prefer real prices over estimates)

Products:
{json.dumps(all_products, indent=2)}

Return ONLY a JSON object in this exact format - no other text:
{{
    "selected_products": [{{product1}}, {{product2}}, {{product3}}],
    "explanation": "Brief explanation of why these products were selected"
}}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful grocery shopping assistant that selects the best products based on price, quality, and dietary restrictions. You MUST return only valid JSON objects."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        result = json.loads(response.choices[0].message.content)
        if isinstance(result, dict) and "selected_products" in result:
            print(f"\nSelection rationale: {result.get('explanation', '')}")
            return result.get("selected_products", [])
        else:
            return sorted(all_products, key=lambda x: x.get("price", float("inf")))[:3]
        
    except Exception:
        return sorted(all_products, key=lambda x: x.get("price", float("inf")))[:3]

def search_products(item: str, dietary_restrictions: List[str], budget: Dict, stores: List[Dict]) -> List[Dict]:
    """Search for products across all stores"""
    all_products = []
    
    for store in stores:
        try:
            products = get_product_recommendations(store, item, dietary_restrictions, budget)
            all_products.extend(products)
        except Exception:
            continue
    
    return get_ai_recommendations(all_products, item, dietary_restrictions, budget)

def format_budget_summary(budget: Dict) -> str:
    """Format budget information for display"""
    if budget["type"] == "total" and budget["total"]:
        return f"Total budget: ${budget['total']:.2f}"
    elif budget["type"] == "per_item" and budget["per_item"]:
        return f"Budget per item: ${budget['per_item']:.2f}"
    return "No specific budget constraints"

def main():
    print("\nWelcome to the AI Grocery Shopping Assistant!")
    print("\nPlease describe what you're looking for in natural language.")
    print("Example: 'I need organic milk and gluten-free bread in San Francisco, with a budget of $20 per item'")
    print("Example: 'Find me some snacks and fruits in LA, total budget $50, must be vegan'")
    
    prompt = input("\nWhat are you looking for? ")
    
    # Parse the shopping prompt
    parsed_data = parse_shopping_prompt(prompt)
    
    if not parsed_data["items"]:
        print("\nNo shopping items found in your request. Please try again with specific items.")
        return
    
    # Get store configurations based on location
    stores = get_store_configs(parsed_data["location"])
    
    # Display parsed information
    print("\nI understand you're looking for:")
    print(f"Items: {', '.join(parsed_data['items'])}")
    print(f"Location: {parsed_data['location']['city'] or 'Local'}, {parsed_data['location']['state']}")
    if parsed_data["dietary_restrictions"]:
        print(f"Dietary restrictions: {', '.join(parsed_data['dietary_restrictions'])}")
    print(f"Budget: {format_budget_summary(parsed_data['budget'])}")
    
    # Process each item
    results = {}
    with tqdm(total=len(parsed_data["items"]), desc="Processing items") as pbar:
        for item in parsed_data["items"]:
            results[item] = search_products(
                item,
                parsed_data["dietary_restrictions"],
                parsed_data["budget"],
                stores
            )
            pbar.update(1)
    
    # Display results
    print("\nRecommended Products:")
    total_cost = 0
    for item, products in results.items():
        print(f"\n{item.capitalize()}:")
        for product in products:
            print(f"- {product['name']}")
            print(f"  Price: ${product['price']:.2f} ({product['unit']})")
            print(f"  Store: {product['store']}")
            if product.get('organic'):
                print("  Organic: Yes")
            print(f"  Availability: {product['availability']}")
            print(f"  Source: {product.get('source', 'Not specified')}")
            if product.get('link'):
                print(f"  Link: {product['link']}")
            total_cost += product['price']
    
    # Show total cost if there's a total budget
    if parsed_data["budget"]["type"] == "total" and parsed_data["budget"]["total"]:
        print(f"\nTotal cost: ${total_cost:.2f}")
        if total_cost > parsed_data["budget"]["total"]:
            print(f"Warning: Total cost exceeds budget by ${(total_cost - parsed_data['budget']['total']):.2f}")
        else:
            print(f"Remaining budget: ${(parsed_data['budget']['total'] - total_cost):.2f}")
    
    # Save detailed results to file
    with open("shopping_results.json", "w") as f:
        json.dump({
            "request": parsed_data,
            "results": results,
            "total_cost": total_cost
        }, f, indent=2)
    print("\nDetailed results saved to shopping_results.json")

if __name__ == "__main__":
    main() 