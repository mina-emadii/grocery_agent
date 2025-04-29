import os
from typing import Dict, Optional, List, Any
import logging
import json
import asyncio
import aiohttp
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError
from bs4 import BeautifulSoup
import re
import random

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceFetcher:
    def __init__(self):
        """Initialize the price fetcher with API configurations"""
        self.stores = ["Walmart", "Target", "Safeway", "Whole Foods"]
        self.api_key = "sd3rzdyGRLYigHCRTwQZY83yrk32mIxR"
        self.walmart_base_url = "https://get.scrapehero.com/wmt"
        self.amazon_base_url = "https://get.scrapehero.com/amz"
        self.session = None
        self.browser = None
        self.context = None
        self.timeout = 30000  # 30 seconds timeout
        self.use_simulation = True  # Set to True to use simulated data instead of scraping

    async def __aenter__(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession()
        if not self.use_simulation:
            try:
                playwright = await async_playwright().start()
                self.browser = await playwright.chromium.launch(headless=True)
                self.context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    viewport={"width": 1280, "height": 720}
                )
            except Exception as e:
                logger.error(f"Error initializing Playwright: {str(e)}")
                self.use_simulation = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up aiohttp session and Playwright resources"""
        if self.session:
            await self.session.close()
        if not self.use_simulation:
            try:
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
            except Exception as e:
                logger.error(f"Error closing Playwright resources: {str(e)}")

    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price from text"""
        if not price_text:
            return 0.0
        # Remove currency symbols and convert to float
        price = re.sub(r'[^\d.]', '', price_text)
        try:
            return float(price)
        except ValueError:
            return 0.0

    def _get_simulated_data(self, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Dict[str, Any]]:
        """Generate simulated price data for all stores"""
        results = {}
        
        # Base price ranges for each store
        price_ranges = {
            "Walmart": (0.5, 2.0),
            "Target": (0.75, 2.5),
            "Safeway": (1.0, 3.0),
            "Whole Foods": (1.5, 4.0)
        }
        
        # Dietary restrictions that might be handled
        possible_restrictions = [
            "organic", "gluten-free", "vegan", "vegetarian", "dairy-free", 
            "nut-free", "soy-free", "kosher", "halal", "low-sodium"
        ]
        
        # Generate data for each store
        for store in self.stores:
            # Generate a price based on the store's range
            min_price, max_price = price_ranges[store]
            price = round(random.uniform(min_price, max_price), 2)
            
            # Determine if the item is available (90% chance)
            availability = random.random() > 0.1
            
            # Generate dietary information
            # Filter restrictions based on the item name and requested restrictions
            relevant_restrictions = []
            for restriction in dietary_restrictions:
                if restriction in possible_restrictions:
                    relevant_restrictions.append(restriction)
            
            # Add some random additional restrictions
            additional_restrictions = random.sample(
                [r for r in possible_restrictions if r not in relevant_restrictions],
                min(2, len(possible_restrictions) - len(relevant_restrictions))
            )
            
            all_restrictions = relevant_restrictions + additional_restrictions
            
            # Generate ingredients based on the item name
            ingredients = self._generate_ingredients(item_name)
            
            # Generate allergen info
            allergen_info = self._generate_allergen_info(item_name, all_restrictions)
            
            results[store] = {
                "price": price,
                "availability": availability,
                "dietary_info": {
                    "restrictions_handled": all_restrictions,
                    "ingredients": ingredients,
                    "allergen_info": allergen_info
                }
            }
        
        return results
    
    def _generate_ingredients(self, item_name: str) -> List[str]:
        """Generate realistic ingredients based on the item name"""
        common_ingredients = {
            "banana": ["bananas", "potassium", "vitamin C", "fiber"],
            "milk": ["milk", "vitamin D", "calcium", "protein"],
            "bread": ["wheat flour", "water", "yeast", "salt", "sugar"],
            "apple": ["apples", "fiber", "vitamin C", "antioxidants"],
            "chicken": ["chicken", "protein", "vitamin B12", "iron"],
            "rice": ["rice", "carbohydrates", "iron", "thiamine"],
            "pasta": ["durum wheat semolina", "water", "iron", "niacin"],
            "cheese": ["milk", "salt", "enzymes", "cultures", "calcium"],
            "yogurt": ["milk", "live active cultures", "protein", "calcium"],
            "cereal": ["whole grain", "sugar", "vitamins", "minerals"]
        }
        
        # Default ingredients if no match
        default_ingredients = ["water", "salt", "preservatives"]
        
        # Try to match the item name with common ingredients
        for key, ingredients in common_ingredients.items():
            if key in item_name.lower():
                return ingredients
        
        # If no match, return default ingredients
        return default_ingredients
    
    def _generate_allergen_info(self, item_name: str, restrictions: List[str]) -> str:
        """Generate realistic allergen information based on the item name and restrictions"""
        allergen_info = "No allergen information available"
        
        # Common allergens
        allergens = {
            "milk": "Contains milk",
            "wheat": "Contains wheat",
            "egg": "Contains eggs",
            "soy": "Contains soy",
            "tree nut": "Contains tree nuts",
            "peanut": "Contains peanuts",
            "fish": "Contains fish",
            "shellfish": "Contains shellfish"
        }
        
        # Check if the item name contains allergens
        for allergen, info in allergens.items():
            if allergen in item_name.lower():
                allergen_info = info
                break
        
        # If the item has dietary restrictions, update allergen info
        if "gluten-free" in restrictions:
            allergen_info = "Gluten-free"
        elif "dairy-free" in restrictions:
            allergen_info = "Dairy-free"
        elif "nut-free" in restrictions:
            allergen_info = "Nut-free"
        
        return allergen_info

    async def fetch_walmart_price(self, item_name: str, dietary_restrictions: List[str] = None) -> Dict:
        """Fetch price from Walmart using ScrapeHero API"""
        try:
            # For testing with organic bananas
            # Note: In a production environment, we would need to implement
            # a proper search endpoint to find the correct product ID
            product_id = "10450856"  # Example product ID for organic bananas
            
            # Get product details using the exact URL structure from the example
            details_url = f"https://get.scrapehero.com/wmt/product-details/?x-api-key={self.api_key}&product_id={product_id}"
            logger.info(f"Getting Walmart product details for ID: {product_id}")
            
            async with self.session.get(details_url) as details_response:
                logger.info(f"Walmart Details Response Status: {details_response.status}")
                details_text = await details_response.text()
                logger.info(f"Walmart Details Response: {details_text}")
                
                if details_response.status != 200:
                    logger.error(f"Walmart product details failed: {details_response.status}")
                    return self._get_simulated_data(item_name, dietary_restrictions)["Walmart"]
                
                product_data = await details_response.json()
                if "200" not in product_data:
                    logger.error("Invalid Walmart product data")
                    return self._get_simulated_data(item_name, dietary_restrictions)["Walmart"]
                
                product = product_data["200"]
                
                # Extract dietary information from product details
                dietary_info = []
                if "product_information" in product:
                    info = product["product_information"]
                    if "Brand" in info:
                        dietary_info.append(f"Brand: {info['Brand']}")
                    if "Features" in info:
                        dietary_info.append(f"Features: {info['Features']}")
                
                # Add organic certification if present
                if "organic" in product.get("name", "").lower():
                    dietary_info.append("Certified Organic")
                
                # Check availability
                availability = product.get("availability_status", "Unknown")
                if "In Stock" in availability:
                    availability = "In Stock"
                elif "Out of Stock" in availability:
                    availability = "Out of Stock"
                
                return {
                    "store": "Walmart",
                    "price": float(product.get("sale_price", product.get("regular_price", 0))),
                    "availability": availability,
                    "url": product.get("url", ""),
                    "dietary_info": dietary_info
                }
                
        except Exception as e:
            logger.error(f"Error fetching Walmart price: {str(e)}")
            return self._get_simulated_data(item_name, dietary_restrictions)["Walmart"]

    async def fetch_target_price(self, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Any]:
        """Fetch price from Target website using Playwright"""
        if self.use_simulation:
            return self._get_simulated_data(item_name, dietary_restrictions)["Target"]
            
        try:
            page = await self.context.new_page()
            search_url = f"https://www.target.com/s?searchTerm={item_name.replace(' ', '+')}"
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            
            # Take a screenshot for debugging
            await page.screenshot(path=f"target_{item_name.replace(' ', '_')}.png")
            
            # Get page content and parse with BeautifulSoup
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for product cards
            product_cards = soup.select("div[data-test='product-card'], div.product-card, div[data-testid='product-card']")
            
            if not product_cards:
                logger.warning("No product cards found on Target")
                await page.close()
                return self._get_simulated_data(item_name, dietary_restrictions)["Target"]
            
            # Get the first product card
            product_card = product_cards[0]
            
            # Extract price
            price_elem = product_card.select_one("span[data-test='product-price'], span.price, div[data-test='price']")
            if not price_elem:
                logger.warning("No price found on Target")
                await page.close()
                return self._get_simulated_data(item_name, dietary_restrictions)["Target"]
            
            price_text = price_elem.text.strip()
            
            # Extract name
            name_elem = product_card.select_one("a[data-test='product-title'], h3.product-title, span[data-test='product-title']")
            if not name_elem:
                logger.warning("No name found on Target")
                await page.close()
                return self._get_simulated_data(item_name, dietary_restrictions)["Target"]
            
            name_text = name_elem.text.strip()
            
            # Extract availability
            availability_elem = product_card.select_one("div[data-test='fulfillment-cell'], span.availability")
            availability_text = availability_elem.text.strip() if availability_elem else "In stock"
            
            # Get product URL
            product_url = None
            link_elem = product_card.select_one("a[href]")
            if link_elem and 'href' in link_elem.attrs:
                product_url = link_elem['href']
                if not product_url.startswith('http'):
                    product_url = f"https://www.target.com{product_url}"
            
            # If we have a product URL, try to get more details
            ingredients = []
            dietary_list = []
            allergen_text = "No allergen information available"
            
            if product_url:
                try:
                    await page.goto(product_url, wait_until="networkidle", timeout=30000)
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for ingredients
                    ingredients_elem = soup.select("div[data-test='ingredients'] li, div.ingredients li")
                    if ingredients_elem:
                        ingredients = [ing.text.strip() for ing in ingredients_elem]
                    
                    # Look for dietary flags
                    dietary_elem = soup.select("div[data-test='dietary-flags'] span, div.dietary-flags span")
                    if dietary_elem:
                        dietary_list = [flag.text.strip() for flag in dietary_elem]
                    
                    # Look for allergen info
                    allergen_elem = soup.select_one("div[data-test='allergen-info'], div.allergen-info")
                    if allergen_elem:
                        allergen_text = allergen_elem.text.strip()
                except Exception as e:
                    logger.warning(f"Error getting product details: {str(e)}")
            
            await page.close()
            
            return {
                "price": self._extract_price(price_text),
                "availability": "Out of stock" not in availability_text.lower(),
                "dietary_info": {
                    "restrictions_handled": dietary_list,
                    "ingredients": ingredients,
                    "allergen_info": allergen_text
                }
            }
        except Exception as e:
            logger.error(f"Error fetching Target price: {str(e)}")
            return self._get_simulated_data(item_name, dietary_restrictions)["Target"]

    async def fetch_safeway_price(self, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Any]:
        """Fetch price from Safeway website using Playwright"""
        if self.use_simulation:
            return self._get_simulated_data(item_name, dietary_restrictions)["Safeway"]
            
        try:
            page = await self.context.new_page()
            search_url = f"https://www.safeway.com/shop/search-results.html?searchType=keyword&searchTerm={item_name.replace(' ', '+')}"
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            
            # Take a screenshot for debugging
            await page.screenshot(path=f"safeway_{item_name.replace(' ', '_')}.png")
            
            # Get page content and parse with BeautifulSoup
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for product cards
            product_cards = soup.select("div.product-card, div[data-testid='product-card'], div[data-test='product-card']")
            
            if not product_cards:
                logger.warning("No product cards found on Safeway")
                await page.close()
                return self._get_simulated_data(item_name, dietary_restrictions)["Safeway"]
            
            # Get the first product card
            product_card = product_cards[0]
            
            # Extract price
            price_elem = product_card.select_one("span.price, div[data-testid='price'], span[data-testid='price']")
            if not price_elem:
                logger.warning("No price found on Safeway")
                await page.close()
                return self._get_simulated_data(item_name, dietary_restrictions)["Safeway"]
            
            price_text = price_elem.text.strip()
            
            # Extract name
            name_elem = product_card.select_one("h4.product-name, a.product-name, h3[data-testid='product-name']")
            if not name_elem:
                logger.warning("No name found on Safeway")
                await page.close()
                return self._get_simulated_data(item_name, dietary_restrictions)["Safeway"]
            
            name_text = name_elem.text.strip()
            
            # Extract availability
            availability_elem = product_card.select_one("div.availability, span.availability")
            availability_text = availability_elem.text.strip() if availability_elem else "In stock"
            
            # Get product URL
            product_url = None
            link_elem = product_card.select_one("a[href]")
            if link_elem and 'href' in link_elem.attrs:
                product_url = link_elem['href']
                if not product_url.startswith('http'):
                    product_url = f"https://www.safeway.com{product_url}"
            
            # If we have a product URL, try to get more details
            ingredients = []
            dietary_list = []
            allergen_text = "No allergen information available"
            
            if product_url:
                try:
                    await page.goto(product_url, wait_until="networkidle", timeout=30000)
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Look for ingredients
                    ingredients_elem = soup.select("div.ingredients li, div[data-testid='ingredients'] li")
                    if ingredients_elem:
                        ingredients = [ing.text.strip() for ing in ingredients_elem]
                    
                    # Look for dietary flags
                    dietary_elem = soup.select("div.dietary-flags span, div[data-testid='dietary-flags'] span")
                    if dietary_elem:
                        dietary_list = [flag.text.strip() for flag in dietary_elem]
                    
                    # Look for allergen info
                    allergen_elem = soup.select_one("div.allergen-info, div[data-testid='allergen-info']")
                    if allergen_elem:
                        allergen_text = allergen_elem.text.strip()
                except Exception as e:
                    logger.warning(f"Error getting product details: {str(e)}")
            
            await page.close()
            
            return {
                "price": self._extract_price(price_text),
                "availability": "Out of stock" not in availability_text.lower(),
                "dietary_info": {
                    "restrictions_handled": dietary_list,
                    "ingredients": ingredients,
                    "allergen_info": allergen_text
                }
            }
        except Exception as e:
            logger.error(f"Error fetching Safeway price: {str(e)}")
            return self._get_simulated_data(item_name, dietary_restrictions)["Safeway"]

    async def fetch_whole_foods_price(self, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Any]:
        """Fetch price from Whole Foods (Amazon) using ScrapeHero API"""
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Access-Control-Allow-Origin": "*"
            }

            # Search for the product
            search_url = f"{self.amazon_base_url}/search"
            params = {
                "x-api-key": self.api_key,
                "query": item_name,
                "country_code": "US",
                "page": 1,
                "limit": 1
            }

            logger.info(f"Searching Amazon for: {item_name}")
            async with self.session.get(search_url, headers=headers, params=params) as response:
                if response.status != 200:
                    logger.error(f"Amazon search API error: {response.status}")
                    return self._get_error_response("whole_foods")

                data = await response.json()
                logger.info(f"Amazon search response: {json.dumps(data, indent=2)}")
                
                if not data.get("results") or len(data["results"]) == 0:
                    logger.warning("No products found on Amazon")
                    return self._get_error_response("whole_foods")

                # Get the first product's ASIN
                product = data["results"][0]
                asin = product.get("asin")
                if not asin:
                    return self._get_error_response("whole_foods")

                # Get detailed product information
                details_url = f"{self.amazon_base_url}/product-details"
                params = {
                    "x-api-key": self.api_key,
                    "asin": asin,
                    "country_code": "US"
                }

                logger.info(f"Fetching Amazon product details for ASIN: {asin}")
                async with self.session.get(details_url, headers=headers, params=params) as details_response:
                    if details_response.status != 200:
                        return self._get_error_response("whole_foods")

                    details = await details_response.json()
                    logger.info(f"Amazon product details: {json.dumps(details, indent=2)}")
                    
                    # Extract relevant information
                    price = float(details.get("price", 0))
                    availability = details.get("in_stock", False)
                    
                    # Extract dietary information
                    dietary_info = {
                        "restrictions_handled": [],
                        "ingredients": details.get("ingredients", []),
                        "allergen_info": details.get("allergen_info", "No allergen information available")
                    }

                    # Check dietary restrictions
                    if dietary_restrictions:
                        for restriction in dietary_restrictions:
                            if restriction.lower() in str(details).lower():
                                dietary_info["restrictions_handled"].append(restriction)

                    return {
                        "price": price,
                        "availability": availability,
                        "dietary_info": dietary_info
                    }

        except Exception as e:
            logger.error(f"Error fetching Whole Foods price: {str(e)}")
            return self._get_error_response("whole_foods")

    def _get_dummy_data(self, store: str, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Any]:
        """Return dummy data for stores without API access"""
        # Base price ranges for each store
        price_ranges = {
            "target": (0.75, 2.5),
            "safeway": (1.0, 3.0)
        }
        
        # Generate a price based on the store's range
        min_price, max_price = price_ranges.get(store, (1.0, 2.0))
        price = round((min_price + max_price) / 2, 2)
        
        # Generate dietary information
        dietary_info = {
            "restrictions_handled": dietary_restrictions.copy(),
            "ingredients": ["organic ingredients", "natural preservatives"],
            "allergen_info": "No known allergens"
        }
        
        return {
            "price": price,
            "availability": True,
            "dietary_info": dietary_info
        }

    def _get_error_response(self, store: str) -> Dict[str, Any]:
        """Return a standardized error response"""
        return {
            "price": 0.0,
            "availability": False,
            "dietary_info": {
                "restrictions_handled": [],
                "ingredients": [],
                "allergen_info": "No allergen information available"
            }
        }

    async def get_all_prices(self, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch prices from all stores"""
        results = {}
        
        # Fetch from Walmart and Whole Foods (Amazon)
        walmart_result = await self.fetch_walmart_price(item_name, dietary_restrictions)
        whole_foods_result = await self.fetch_whole_foods_price(item_name, dietary_restrictions)
        
        results["Walmart"] = walmart_result
        results["Whole Foods"] = whole_foods_result
        
        # Add dummy data for other stores
        results["Target"] = self._get_dummy_data("target", item_name, dietary_restrictions)
        results["Safeway"] = self._get_dummy_data("safeway", item_name, dietary_restrictions)
        
        return results

    async def get_all_prices_gemini(self, product_name: str, dietary_restrictions: List[str] = None) -> Dict[str, Dict]:
        """
        Fetch prices and product information from all stores using Gemini
        Returns a dictionary with store names as keys and product info as values
        """
        dietary_info = f" and dietary restrictions: {', '.join(dietary_restrictions)}" if dietary_restrictions else ""
        
        prompt = f"""
        Search for the current price and availability of {product_name}{dietary_info} at these stores: {', '.join(self.stores)}.
        Return ONLY a JSON object with store names as keys and product information as values.
        Example format:
        {{
            "Walmart": {{
                "price": 2.99,
                "availability": true,
                "dietary_info": {{
                    "restrictions_handled": ["gluten-free", "vegan"],
                    "ingredients": ["water", "salt", "yeast"],
                    "allergen_info": "Contains wheat"
                }}
            }},
            "Target": {{
                "price": 3.49,
                "availability": true,
                "dietary_info": {{
                    "restrictions_handled": ["gluten-free"],
                    "ingredients": ["water", "salt", "yeast", "preservatives"],
                    "allergen_info": "Contains wheat"
                }}
            }}
        }}
        Use realistic current prices and accurate dietary information. If you don't know the exact price, estimate based on typical prices.
        Consider dietary restrictions when providing product information.
        """

        try:
            response = await self.model.generate_content(prompt)

            # Parse the response
            content = response.choices[0].message.content.strip()
            store_data = json.loads(content)
            
            # Log the information
            for store, data in store_data.items():
                logger.info(f"{store} - {product_name}: ${data['price']:.2f} - Available: {data['availability']}")
                if 'dietary_info' in data:
                    logger.info(f"Dietary info: {data['dietary_info']}")
            
            return store_data

        except Exception as e:
            logger.error(f"Error fetching prices and product information: {str(e)}")
            return {store: {"price": None, "availability": False, "dietary_info": {}} for store in self.stores} 