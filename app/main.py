import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.core.shopping_analyzer import ShoppingAnalyzer
from app.core.store_spider import StoreScraper
from app.core.llm import get_product_recommendation

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Grocery Agent API", description="API for grocery shopping assistance")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ShoppingListRequest(BaseModel):
    """Request model for shopping list analysis"""
    items: List[str] = Field(..., description="List of items to buy")
    dietary_restrictions: List[str] = Field(default=[], description="List of dietary restrictions")

class ShoppingListResponse(BaseModel):
    """Response model for shopping list analysis"""
    recommendations: Dict[str, Dict[str, Any]] = Field(..., description="Recommendations for each item")
    total_cost: Dict[str, float] = Field(..., description="Total cost at each store")
    best_store: str = Field(..., description="Best store to buy all items from")
    explanation: str = Field(..., description="Explanation of the recommendations")

# Initialize components
shopping_analyzer = ShoppingAnalyzer()
store_scraper = StoreScraper()

@app.post("/analyze-shopping-list", response_model=ShoppingListResponse)
async def analyze_shopping_list(request: ShoppingListRequest, background_tasks: BackgroundTasks):
    """
    Analyze a shopping list and provide recommendations
    
    Args:
        request: Shopping list request with items and dietary restrictions
        
    Returns:
        Shopping list response with recommendations
    """
    try:
        # Step 1: Analyze the shopping list and dietary restrictions
        logger.info(f"Analyzing shopping list with {len(request.items)} items and {len(request.dietary_restrictions)} dietary restrictions")
        analysis = await shopping_analyzer.analyze_shopping_list(request.items, request.dietary_restrictions)
        
        # Step 2: Get search criteria for each product
        search_criteria = shopping_analyzer.get_search_criteria(analysis)
        
        # Step 3: Scrape product information from store websites
        logger.info("Scraping product information from store websites")
        scraped_data = await store_scraper.scrape_shopping_list(request.items, search_criteria)
        
        # Step 4: Get recommendations for each product
        recommendations = {}
        total_cost = {
            "walmart": 0.0,
            "target": 0.0,
            "safeway": 0.0,
            "whole_foods": 0.0
        }
        
        for item in request.items:
            # Get store data for this item
            store_data = {}
            for store, products in scraped_data.get(item, {}).items():
                if products:
                    # Use the first product as the representative
                    store_data[store] = {
                        "price": products[0].get("price", 0.0),
                        "availability": products[0].get("availability", False),
                        "dietary_info": products[0].get("dietary_info", {})
                    }
            
            # Get recommendation for this item
            recommendation = await get_product_recommendation(item, request.dietary_restrictions, store_data)
            recommendations[item] = recommendation
            
            # Update total cost
            if recommendation.get("store") in total_cost and recommendation.get("price"):
                total_cost[recommendation["store"]] += recommendation["price"]
        
        # Step 5: Determine the best store
        best_store = min(total_cost, key=total_cost.get)
        
        # Step 6: Generate explanation
        explanation = f"The best store to buy all items from is {best_store} with a total cost of ${total_cost[best_store]:.2f}. "
        explanation += "This recommendation is based on price, availability, and dietary restrictions. "
        
        # Add item-specific explanations
        for item, rec in recommendations.items():
            explanation += f"\n{item}: {rec.get('explanation', '')}"
        
        return ShoppingListResponse(
            recommendations=recommendations,
            total_cost=total_cost,
            best_store=best_store,
            explanation=explanation
        )
        
    except Exception as e:
        logger.error(f"Error analyzing shopping list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing shopping list: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/stores")
async def get_stores():
    """
    Get list of available stores and their locations
    """
    return {
        "stores": [
            {"name": "Trader Joe's", "location": "123 Main St"},
            {"name": "Whole Foods", "location": "456 Market St"},
            {"name": "Safeway", "location": "789 Grocery Ave"},
            {"name": "Target", "location": "321 Shopping Center"},
            {"name": "Walmart", "location": "654 Super Center"}
        ]
    } 