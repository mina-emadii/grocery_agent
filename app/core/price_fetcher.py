import os
from typing import Dict, Optional, List, Any
import logging
from dotenv import load_dotenv
from openai import OpenAI
import json
import aiohttp
import asyncio
from bs4 import BeautifulSoup

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PriceFetcher:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.stores = ["Walmart", "Target", "Safeway", "Whole Foods", "Trader Joe's"]
        self.session = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers, timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def fetch_walmart_price(self, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Any]:
        """Fetch price from Walmart's API"""
        try:
            # For now, return mock data since we don't have actual API access
            return {
                "price": 3.99,
                "availability": True,
                "dietary_info": {
                    "restrictions_handled": ["gluten-free"] if "gluten-free" in dietary_restrictions else [],
                    "ingredients": ["rice flour", "water", "salt"],
                    "allergen_info": "Contains: None"
                }
            }
        except Exception as e:
            logger.error(f"Error fetching Walmart price: {str(e)}")
            return {"price": None, "availability": False}

    async def fetch_target_price(self, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Any]:
        """Fetch price from Target's API"""
        try:
            # For now, return mock data since we don't have actual API access
            return {
                "price": 4.29,
                "availability": True,
                "dietary_info": {
                    "restrictions_handled": ["vegan"] if "vegan" in dietary_restrictions else [],
                    "ingredients": ["whole wheat", "water", "yeast"],
                    "allergen_info": "Contains: Wheat"
                }
            }
        except Exception as e:
            logger.error(f"Error fetching Target price: {str(e)}")
            return {"price": None, "availability": False}

    async def fetch_safeway_price(self, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Any]:
        """Fetch price from Safeway's API"""
        try:
            # For now, return mock data since we don't have actual API access
            return {
                "price": 3.49,
                "availability": True,
                "dietary_info": {
                    "restrictions_handled": ["organic"],
                    "ingredients": ["organic wheat", "water", "sea salt"],
                    "allergen_info": "Contains: Wheat"
                }
            }
        except Exception as e:
            logger.error(f"Error fetching Safeway price: {str(e)}")
            return {"price": None, "availability": False}

    async def fetch_whole_foods_price(self, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Any]:
        """Fetch price from Whole Foods' API"""
        try:
            # For now, return mock data since we don't have actual API access
            return {
                "price": 5.99,
                "availability": True,
                "dietary_info": {
                    "restrictions_handled": ["organic", "vegan"],
                    "ingredients": ["organic sprouted grains", "water", "sea salt"],
                    "allergen_info": "Contains: None"
                }
            }
        except Exception as e:
            logger.error(f"Error fetching Whole Foods price: {str(e)}")
            return {"price": None, "availability": False}

    async def get_all_prices(self, item_name: str, dietary_restrictions: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch prices from all stores concurrently with timeout"""
        try:
            tasks = [
                self.fetch_walmart_price(item_name, dietary_restrictions),
                self.fetch_target_price(item_name, dietary_restrictions),
                self.fetch_safeway_price(item_name, dietary_restrictions),
                self.fetch_whole_foods_price(item_name, dietary_restrictions)
            ]
            
            # Use asyncio.gather with return_exceptions=True to prevent one failure from affecting others
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            processed_results = {}
            for store, result in zip(["walmart", "target", "safeway", "whole_foods"], results):
                if isinstance(result, Exception):
                    logger.error(f"Error fetching {store} price: {str(result)}")
                    processed_results[store] = {"price": None, "availability": False}
                else:
                    processed_results[store] = result
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error in get_all_prices: {str(e)}")
            return {
                "walmart": {"price": None, "availability": False},
                "target": {"price": None, "availability": False},
                "safeway": {"price": None, "availability": False},
                "whole_foods": {"price": None, "availability": False}
            }

    async def get_all_prices_openai(self, product_name: str, dietary_restrictions: List[str] = None) -> Dict[str, Dict]:
        """
        Fetch prices and product information from all stores using OpenAI
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
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides current grocery prices and product information. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

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