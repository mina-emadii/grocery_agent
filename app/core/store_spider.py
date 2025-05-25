import os
import logging
import json
from typing import Dict, List, Any, Optional
from scrapy import Spider, Request
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from itemadapter import ItemAdapter
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductItem:
    """Item class for storing scraped product data"""
    def __init__(self):
        self.store = ""
        self.product_name = ""
        self.price = 0.0
        self.availability = True
        self.url = ""
        self.dietary_info = {
            "restrictions_handled": [],
            "ingredients": [],
            "allergen_info": ""
        }
        self.search_criteria = {}

class StoreSpider(Spider):
    """Base spider for scraping store websites"""
    name = "store_spider"
    
    def __init__(self, product_name=None, search_criteria=None, *args, **kwargs):
        super(StoreSpider, self).__init__(*args, **kwargs)
        self.product_name = product_name
        self.search_criteria = search_criteria or {}
        self.results = []
    
    def parse(self, response):
        """Parse the response and extract product information"""
        raise NotImplementedError("Subclasses must implement parse method")
    
    def closed(self, reason):
        """Called when the spider is closed"""
        logger.info(f"Spider closed with reason: {reason}")
        logger.info(f"Found {len(self.results)} results for {self.product_name}")

class WalmartSpider(StoreSpider):
    """Spider for scraping Walmart website"""
    name = "walmart"
    allowed_domains = ["walmart.com"]
    
    def start_requests(self):
        """Start requests to search for products"""
        search_url = f"https://www.walmart.com/search?q={self.product_name}"
        yield Request(
            url=search_url,
            callback=self.parse,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
    
    def parse(self, response):
        """Parse Walmart search results page"""
        # Extract product links from search results
        product_links = response.css("a.product-title-link::attr(href)").getall()
        
        # Follow each product link
        for link in product_links[:5]:  # Limit to first 5 results
            yield Request(
                url=response.urljoin(link),
                callback=self.parse_product,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            )
    
    def parse_product(self, response):
        """Parse Walmart product page"""
        item = ProductItem()
        item.store = "walmart"
        item.product_name = response.css("h1.prod-ProductTitle::text").get("").strip()
        item.price = float(response.css("span.price-main::attr(data-price)").get("0"))
        item.availability = "Out of stock" not in response.css("div.prod-info-meta::text").get("")
        item.url = response.url
        
        # Extract dietary information
        ingredients = response.css("div.ingredients-list li::text").getall()
        item.dietary_info["ingredients"] = [ing.strip() for ing in ingredients if ing.strip()]
        
        # Check for dietary restrictions
        dietary_flags = response.css("div.dietary-flags span::text").getall()
        item.dietary_info["restrictions_handled"] = [flag.strip() for flag in dietary_flags if flag.strip()]
        
        # Extract allergen information
        allergen_info = response.css("div.allergen-info::text").get("")
        item.dietary_info["allergen_info"] = allergen_info.strip() if allergen_info else "No allergen information available"
        
        # Store search criteria for reference
        item.search_criteria = self.search_criteria
        
        self.results.append(item)
        yield item

class TargetSpider(StoreSpider):
    """Spider for scraping Target website"""
    name = "target"
    allowed_domains = ["target.com"]
    
    def start_requests(self):
        """Start requests to search for products"""
        search_url = f"https://www.target.com/s?searchTerm={self.product_name}"
        yield Request(
            url=search_url,
            callback=self.parse,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
    
    def parse(self, response):
        """Parse Target search results page"""
        # Extract product links from search results
        product_links = response.css("a.product-title-link::attr(href)").getall()
        
        # Follow each product link
        for link in product_links[:5]:  # Limit to first 5 results
            yield Request(
                url=response.urljoin(link),
                callback=self.parse_product,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            )
    
    def parse_product(self, response):
        """Parse Target product page"""
        item = ProductItem()
        item.store = "target"
        item.product_name = response.css("h1.Heading__StyledHeading-sc-1mp23s9-0::text").get("").strip()
        item.price = float(response.css("span[data-test='product-price']::text").get("0").replace("$", "").strip())
        item.availability = "Out of stock" not in response.css("div[data-test='fulfillment-cell']::text").get("")
        item.url = response.url
        
        # Extract dietary information
        ingredients = response.css("div.Ingredients__StyledIngredients-sc-1q9m1xk-0 li::text").getall()
        item.dietary_info["ingredients"] = [ing.strip() for ing in ingredients if ing.strip()]
        
        # Check for dietary restrictions
        dietary_flags = response.css("div.DietaryFlags__StyledDietaryFlags-sc-1q9m1xk-0 span::text").getall()
        item.dietary_info["restrictions_handled"] = [flag.strip() for flag in dietary_flags if flag.strip()]
        
        # Extract allergen information
        allergen_info = response.css("div.AllergenInfo__StyledAllergenInfo-sc-1q9m1xk-0::text").get("")
        item.dietary_info["allergen_info"] = allergen_info.strip() if allergen_info else "No allergen information available"
        
        # Store search criteria for reference
        item.search_criteria = self.search_criteria
        
        self.results.append(item)
        yield item

class SafewaySpider(StoreSpider):
    """Spider for scraping Safeway website"""
    name = "safeway"
    allowed_domains = ["safeway.com"]
    
    def start_requests(self):
        """Start requests to search for products"""
        search_url = f"https://www.safeway.com/shop/search-results.html?searchType=keyword&searchTerm={self.product_name}"
        yield Request(
            url=search_url,
            callback=self.parse,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
    
    def parse(self, response):
        """Parse Safeway search results page"""
        # Extract product links from search results
        product_links = response.css("a.product-title::attr(href)").getall()
        
        # Follow each product link
        for link in product_links[:5]:  # Limit to first 5 results
            yield Request(
                url=response.urljoin(link),
                callback=self.parse_product,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            )
    
    def parse_product(self, response):
        """Parse Safeway product page"""
        item = ProductItem()
        item.store = "safeway"
        item.product_name = response.css("h1.product-name::text").get("").strip()
        item.price = float(response.css("span.price::text").get("0").replace("$", "").strip())
        item.availability = "Out of stock" not in response.css("div.availability::text").get("")
        item.url = response.url
        
        # Extract dietary information
        ingredients = response.css("div.ingredients li::text").getall()
        item.dietary_info["ingredients"] = [ing.strip() for ing in ingredients if ing.strip()]
        
        # Check for dietary restrictions
        dietary_flags = response.css("div.dietary-flags span::text").getall()
        item.dietary_info["restrictions_handled"] = [flag.strip() for flag in dietary_flags if flag.strip()]
        
        # Extract allergen information
        allergen_info = response.css("div.allergen-info::text").get("")
        item.dietary_info["allergen_info"] = allergen_info.strip() if allergen_info else "No allergen information available"
        
        # Store search criteria for reference
        item.search_criteria = self.search_criteria
        
        self.results.append(item)
        yield item

class WholeFoodsSpider(StoreSpider):
    """Spider for scraping Whole Foods website"""
    name = "whole_foods"
    allowed_domains = ["wholefoodsmarket.com"]
    
    def start_requests(self):
        """Start requests to search for products"""
        search_url = f"https://www.wholefoodsmarket.com/search?text={self.product_name}"
        yield Request(
            url=search_url,
            callback=self.parse,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
    
    def parse(self, response):
        """Parse Whole Foods search results page"""
        # Extract product links from search results
        product_links = response.css("a.product-title::attr(href)").getall()
        
        # Follow each product link
        for link in product_links[:5]:  # Limit to first 5 results
            yield Request(
                url=response.urljoin(link),
                callback=self.parse_product,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                }
            )
    
    def parse_product(self, response):
        """Parse Whole Foods product page"""
        item = ProductItem()
        item.store = "whole_foods"
        item.product_name = response.css("h1.product-name::text").get("").strip()
        item.price = float(response.css("span.price::text").get("0").replace("$", "").strip())
        item.availability = "Out of stock" not in response.css("div.availability::text").get("")
        item.url = response.url
        
        # Extract dietary information
        ingredients = response.css("div.ingredients li::text").getall()
        item.dietary_info["ingredients"] = [ing.strip() for ing in ingredients if ing.strip()]
        
        # Check for dietary restrictions
        dietary_flags = response.css("div.dietary-flags span::text").getall()
        item.dietary_info["restrictions_handled"] = [flag.strip() for flag in dietary_flags if flag.strip()]
        
        # Extract allergen information
        allergen_info = response.css("div.allergen-info::text").get("")
        item.dietary_info["allergen_info"] = allergen_info.strip() if allergen_info else "No allergen information available"
        
        # Store search criteria for reference
        item.search_criteria = self.search_criteria
        
        self.results.append(item)
        yield item

class StoreScraper:
    """Class for managing store spiders and scraping results"""
    
    def __init__(self):
        self.process = CrawlerProcess(get_project_settings())
        self.spiders = {
            "walmart": WalmartSpider,
            "target": TargetSpider,
            "safeway": SafewaySpider,
            "whole_foods": WholeFoodsSpider
        }
    
    async def scrape_product(self, product_name: str, search_criteria: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scrape product information from all stores
        
        Args:
            product_name: Name of the product to search for
            search_criteria: Search criteria for the product
            
        Returns:
            Dictionary with store names as keys and lists of product information as values
        """
        results = {}
        
        for store_name, spider_class in self.spiders.items():
            try:
                # Create a spider instance
                spider = spider_class(product_name=product_name, search_criteria=search_criteria)
                
                # Run the spider
                self.process.crawl(spider)
                self.process.start()
                
                # Get the results
                store_results = []
                for item in spider.results:
                    adapter = ItemAdapter(item)
                    store_results.append(dict(adapter))
                
                results[store_name] = store_results
                
                logger.info(f"Scraped {len(store_results)} results for {product_name} from {store_name}")
                
            except Exception as e:
                logger.error(f"Error scraping {product_name} from {store_name}: {str(e)}")
                results[store_name] = []
        
        return results
    
    async def scrape_shopping_list(self, shopping_list: List[str], search_criteria: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Scrape information for all products in a shopping list
        
        Args:
            shopping_list: List of products to search for
            search_criteria: Dictionary with product names as keys and search criteria as values
            
        Returns:
            Dictionary with product names as keys and store results as values
        """
        results = {}
        
        for product_name in shopping_list:
            product_criteria = search_criteria.get(product_name, {})
            product_results = await self.scrape_product(product_name, product_criteria)
            results[product_name] = product_results
        
        return results 