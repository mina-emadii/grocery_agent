import asyncio
import logging
from app.core.price_fetcher import PriceFetcher
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_price_fetcher():
    """Test the price fetcher with organic bananas"""
    # Test with organic bananas
    item_name = "organic banana"
    dietary_restrictions = ["organic"]
    
    print(f"\nSearching for: {item_name}")
    print("Dietary restrictions:", dietary_restrictions)
    
    async with PriceFetcher() as fetcher:
        results = await fetcher.get_all_prices(item_name, dietary_restrictions)
        
        # Print results in a formatted way
        print("\nResults:")
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(test_price_fetcher()) 