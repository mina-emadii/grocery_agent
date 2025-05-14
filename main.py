import os
import json
import time
import urllib.parse
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from bs4 import BeautifulSoup

# 1. Load environment variables
load_dotenv()
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

if not FIRECRAWL_API_KEY:
    raise ValueError("FIRECRAWL_API_KEY environment variable is required")

# 2. Hardcoded list of grocery stores and their CSS selectors
#    - search_url: where to search items (use {query} placeholder)
#    - product_selector: to identify each product tile/block
#    - Within each block, selectors for title, price, description, tags
grocery_stores = [
    {
        "name": "Whole Foods",
        "search_url": "https://www.wholefoodsmarket.com/search?text={query}",
        "product_selector": "div[data-testid='product-tile']",
        "fields": {
            "title":       "h2[data-testid='product-tile-name']",
            "brand":       "span[data-testid='product-tile-brand']",
            "tags":        None
        }
    },
    {
        "name": "Trader Joe's",
        "search_url": "https://www.traderjoes.com/home/search?q={query}",
        "product_selector": "div.product-tile",
        "fields": {
            "title":       "h2.title",
            "price":       "span.price",
            "tags":        "div.tags"
        }
    }
]

def is_compatible(text: str, restrictions: list[str]) -> bool:
    low = text.lower()
    return all(r.lower() in low for r in restrictions)

def score_product(product: dict, restrictions: list[str]) -> float:
    score = 1.0
    tags = " ".join(product.get("tags", []))
    ingredients = " ".join(product.get("ingredients", []))
    nutrition = " ".join(product.get("nutrition", []))
    
    if "organic" in tags.lower(): score += 0.1
    if product.get("price", 0) > 10: score -= 0.2
    if not is_compatible(ingredients + nutrition + tags, restrictions):
        score -= 0.5
    return max(score, 0.0)

def extract_products_from_html(html, store):
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.select(store["product_selector"])
    products = []
    for block in blocks:
        p = {"url": None}
        for fname, sel in store["fields"].items():
            if not sel:
                p[fname] = ""
                continue
            el = block.select_one(sel)
            if fname == "price":
                text = el.get_text(strip=True).replace("$", "") if el else ""
                p[fname] = float(text) if text.replace('.', '', 1).isdigit() else 0.0
            elif fname == "tags":
                p[fname] = [t.get_text(strip=True) for t in block.select(sel)] if el else []
            else:
                p[fname] = el.get_text(strip=True) if el else ""
        # Extract product link
        link_el = block.select_one("a[data-testid='product-tile-link']")
        if link_el and link_el.has_attr('href'):
            p["product_link"] = link_el['href'] if link_el['href'].startswith('http') else f"https://www.wholefoodsmarket.com{link_el['href']}"
        else:
            p["product_link"] = ""
        products.append(p)
    return products

def extract_details_from_detail_page(html):
    soup = BeautifulSoup(html, "html.parser")
    # Extract price
    price = ""
    price_el = soup.select_one("span[data-testid='product-price']")
    if price_el:
        price = price_el.get_text(strip=True).replace("$", "")
    
    # Extract ingredients
    ingredients = []
    ingredients_el = soup.select_one("div[data-testid='product-ingredients']")
    if ingredients_el:
        ingredients = [i.strip() for i in ingredients_el.get_text(strip=True).split(',')]
    
    # Extract nutrition facts
    nutrition = []
    nutrition_el = soup.select_one("div[data-testid='product-nutrition']")
    if nutrition_el:
        nutrition = [n.strip() for n in nutrition_el.get_text(strip=True).split('\n') if n.strip()]
    
    return price, ingredients, nutrition

def search_store_item(app, store, item, restrictions):
    url = store["search_url"].format(query=urllib.parse.quote_plus(item))
    try:
        result = app.scrape_url(url, formats=["html"])
        html = result.html
        debug_filename = f"debug_{store['name'].replace(' ', '_')}_{item.replace(' ', '_')}.html"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [Debug] Saved raw HTML for '{item}' from {store['name']} to {debug_filename}")
        products = extract_products_from_html(html, store)
        filtered = []
        for p in products:
            # Scrape detail page for price, ingredients and nutrition
            if p.get("product_link"):
                try:
                    detail_result = app.scrape_url(p["product_link"], formats=["html"])
                    detail_html = detail_result.html
                    price, ingredients, nutrition = extract_details_from_detail_page(detail_html)
                    p["price"] = float(price) if price.replace('.', '', 1).isdigit() else 0.0
                    p["ingredients"] = ingredients
                    p["nutrition"] = nutrition
                except Exception as e:
                    print(f"    [Detail] Error fetching details for {p.get('title', '')}: {e}")
            # Ensure all are lists
            ingredients = p.get("ingredients", [])
            if not isinstance(ingredients, list):
                ingredients = [ingredients]
            nutrition = p.get("nutrition", [])
            if not isinstance(nutrition, list):
                nutrition = [nutrition]
            tags = p.get("tags", [])
            if not isinstance(tags, list):
                tags = [tags]
            combined_text = " ".join(ingredients + nutrition + tags)
            if is_compatible(combined_text, restrictions):
                p["score"] = score_product(p, restrictions)
                p["store"] = store["name"]
                p["url"] = url
                filtered.append(p)
        return filtered
    except Exception as e:
        print(f"  Error fetching {item} from {store['name']}: {e}")
        return []

def main():
    app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
    print("\nEnter your dietary restrictions (comma-separated):")
    print("Examples: vegan, gluten-free, dairy-free")
    dietary_restrictions = [r.strip().lower() for r in input().split(',') if r.strip()]
    
    print("\nEnter your shopping list items (comma-separated):")
    shopping_list = [item.strip() for item in input().split(',') if item.strip()]
    
    if not shopping_list:
        print("No items in shopping list. Exiting...")
        return
        
    print("\nSearching for items across stores...")
    print(f"Considering dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}")
    all_results = {}
    for store in grocery_stores:
        print(f"Searching {store['name']}...")
        results = []
        for item in shopping_list:
            res = search_store_item(app, store, item, dietary_restrictions)
            results.extend(res)
            time.sleep(1)
        all_results[store["name"]] = results
    print(json.dumps(all_results, indent=2))
    with open("results.json", "w") as f:
        json.dump(all_results, f, indent=2)

if __name__ == "__main__":
    main() 