from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from app.core.llm import get_product_recommendation

load_dotenv()

app = FastAPI(
    title="Grocery Agent",
    description="A smart grocery shopping assistant that helps users find the best deals and manage their shopping lists",
    version="1.0.0"
)

class ShoppingItem(BaseModel):
    name: str
    dietary_restrictions: Optional[List[str]] = []

class ShoppingList(BaseModel):
    items: List[ShoppingItem]
    dietary_restrictions: Optional[List[str]] = []

class ProductRecommendation(BaseModel):
    store: str
    product_name: str
    price: float
    is_suitable: bool
    dietary_info: Dict[str, Any]
    explanation: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Welcome to Grocery Agent API"}

@app.post("/analyze-shopping-list")
async def analyze_shopping_list(shopping_list: ShoppingList):
    """
    Analyze a shopping list and provide recommendations based on dietary restrictions
    using LLM-powered recommendations
    """
    recommendations = []
    store_options = ["Trader Joe's", "Whole Foods", "Safeway", "Target", "Walmart"]
    
    # Combine item-specific and list-wide dietary restrictions
    all_dietary_restrictions = set(shopping_list.dietary_restrictions or [])
    for item in shopping_list.items:
        all_dietary_restrictions.update(item.dietary_restrictions or [])
    
    for item in shopping_list.items:
        # Get LLM-based recommendation for each item
        recommendation = await get_product_recommendation(
            item_name=item.name,
            dietary_restrictions=list(all_dietary_restrictions),
            store_options=store_options
        )
        
        recommendations.append(ProductRecommendation(**recommendation))
    
    return {
        "recommendations": recommendations,
        "total_estimated_cost": sum(rec.price for rec in recommendations),
        "dietary_restrictions_handled": list(all_dietary_restrictions)
    }

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