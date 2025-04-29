from openai import OpenAI
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from .price_fetcher import PriceFetcher
import json
import logging

load_dotenv()

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_product_recommendation(
    item_name: str,
    dietary_restrictions: List[str],
    store_options: List[str]
) -> Dict[str, Any]:
    """
    Get product recommendations using LLM based on item name and dietary restrictions.
    """
    try:
        # First, fetch real prices and product information from all stores
        async with PriceFetcher() as price_fetcher:
            store_data = await price_fetcher.get_all_prices(item_name, dietary_restrictions)
        
        logger.info(f"Fetched store data: {json.dumps(store_data, indent=2)}")
        
        # Filter out stores with no price data or unavailable products
        available_stores = {
            store: data for store, data in store_data.items() 
            if data.get("price") is not None and data.get("availability", False)
        }
        
        if not available_stores:
            logger.warning(f"No available stores found for {item_name}")
            # Fallback if no prices are available
            return {
                "store": store_options[0],
                "product_name": item_name,
                "price": None,
                "is_suitable": True,
                "dietary_info": {
                    "restrictions_handled": [],
                    "ingredients": [],
                    "allergen_info": "No specific allergen information available"
                },
                "explanation": "Unable to fetch current prices. Please check store websites directly."
            }

        # Create a detailed comparison string for the LLM
        store_comparison = []
        for store, data in available_stores.items():
            price_info = f"Price: ${data['price']:.2f}"
            dietary_info = data.get('dietary_info', {})
            restrictions = dietary_info.get('restrictions_handled', [])
            ingredients = dietary_info.get('ingredients', [])
            allergens = dietary_info.get('allergen_info', 'No allergen information')
            
            store_comparison.append(f"""
            {store}:
            - {price_info}
            - Dietary restrictions handled: {', '.join(restrictions)}
            - Main ingredients: {', '.join(ingredients)}
            - Allergen info: {allergens}
            """)
        
        comparison_text = "\n".join(store_comparison)
        
        prompt = f"""
        Given the following information:
        - Product: {item_name}
        - Dietary Restrictions: {', '.join(dietary_restrictions)}
        - Store Comparisons:
        {comparison_text}

        Please provide a recommendation in the following JSON format:
        {{
            "store": "store name (must be one of the stores with prices listed above)",
            "product_name": "specific product name",
            "price": actual_price_from_store,
            "is_suitable": true/false,
            "dietary_info": {{
                "restrictions_handled": ["list of handled restrictions"],
                "ingredients": ["list of main ingredients"],
                "allergen_info": "any allergen information"
            }},
            "explanation": "brief explanation of why this is the best choice, considering price, dietary restrictions, and product quality"
        }}

        Consider:
        1. Dietary restrictions and allergies (highest priority)
        2. Price competitiveness
        3. Product availability
        4. Quality and brand reputation
        5. Ingredient quality and sourcing

        Return ONLY the JSON object, no additional text.
        """

        logger.info(f"Sending prompt to OpenAI: {prompt}")
        
        try:
            response = await client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "You are a helpful grocery shopping assistant that provides detailed product recommendations based on real-time prices and dietary requirements. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            # Get the response content
            content = response.choices[0].message.content.strip()
            logger.info(f"Received response from OpenAI: {content}")
            
            # Try to parse the JSON response
            try:
                recommendation = json.loads(content)
                logger.info(f"Successfully parsed recommendation: {json.dumps(recommendation, indent=2)}")
                return recommendation
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise ValueError("Invalid JSON response from OpenAI")
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise

    except Exception as e:
        logger.error(f"Error getting recommendation: {str(e)}")
        # Return a basic recommendation based on lowest price
        if 'available_stores' in locals() and available_stores:
            best_store = min(available_stores.items(), key=lambda x: x[1]["price"])[0]
            return {
                "store": best_store,
                "product_name": item_name,
                "price": available_stores[best_store]["price"],
                "is_suitable": True,
                "dietary_info": available_stores[best_store]["dietary_info"],
                "explanation": "Selected based on lowest price due to error in processing recommendation."
            }
        else:
            return {
                "store": store_options[0],
                "product_name": item_name,
                "price": None,
                "is_suitable": False,
                "dietary_info": {
                    "restrictions_handled": [],
                    "ingredients": [],
                    "allergen_info": "Error occurred while fetching product information"
                },
                "explanation": "An error occurred while processing your request. Please try again."
            } 