import os
import json
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductRecommendation(BaseModel):
    """Model for product recommendations"""
    store: str = Field(description="Store where the product is recommended")
    product_name: str = Field(description="Name of the recommended product")
    price: float = Field(description="Price of the product")
    is_suitable: bool = Field(description="Whether the product meets dietary restrictions")
    dietary_info: Dict[str, Any] = Field(description="Dietary information about the product")
    explanation: str = Field(description="Explanation of the recommendation")

class ProductRecommender:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        self.model = ChatGoogleGenerativeAI(
            model="gemini-pro",
            google_api_key=self.api_key,
            temperature=0.2,
            convert_system_message_to_human=True
        )
        
        self.output_parser = PydanticOutputParser(pydantic_object=ProductRecommendation)
        
        self.recommendation_prompt = PromptTemplate(
            template="""
            Given the following information:
            - Product: {product_name}
            - Dietary Restrictions: {dietary_restrictions}
            - Store Comparisons:
            
            {store_data}
            
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
            
            {format_instructions}
            """,
            input_variables=["product_name", "dietary_restrictions", "store_data"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
    
    async def get_recommendation(self, product_name: str, dietary_restrictions: List[str], store_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get a product recommendation based on store data and dietary restrictions
        
        Args:
            product_name: Name of the product
            dietary_restrictions: List of dietary restrictions
            store_data: Dictionary with store names as keys and product information as values
            
        Returns:
            Dictionary with product recommendation
        """
        try:
            # Format the dietary restrictions
            formatted_restrictions = ", ".join(dietary_restrictions) if dietary_restrictions else "None"
            
            # Format the store data
            store_data_text = ""
            for store, data in store_data.items():
                store_data_text += f"\n            {store}:\n"
                store_data_text += f"            - Price: ${data.get('price', 0):.2f}\n"
                store_data_text += f"            - Dietary restrictions handled: {', '.join(data.get('dietary_info', {}).get('restrictions_handled', []))}\n"
                store_data_text += f"            - Main ingredients: {', '.join(data.get('dietary_info', {}).get('ingredients', []))}\n"
                store_data_text += f"            - Allergen info: {data.get('dietary_info', {}).get('allergen_info', 'No allergen information available')}\n"
            
            # Create the prompt
            prompt = self.recommendation_prompt.format(
                product_name=product_name,
                dietary_restrictions=formatted_restrictions,
                store_data=store_data_text
            )
            
            # Get response from Gemini
            response = await self.model.ainvoke(prompt)
            
            # Parse the response
            recommendation = self.output_parser.parse(response.content)
            
            logger.info(f"Generated recommendation for {product_name} from {recommendation.store}")
            return recommendation.dict()
            
        except Exception as e:
            logger.error(f"Error getting recommendation: {str(e)}")
            # Return a fallback recommendation
            return {
                "store": list(store_data.keys())[0] if store_data else "walmart",
                "product_name": product_name,
                "price": min(data.get("price", 0) for data in store_data.values()) if store_data else 0,
                "is_suitable": False,
                "dietary_info": {
                    "restrictions_handled": [],
                    "ingredients": [],
                    "allergen_info": "No allergen information available"
                },
                "explanation": f"Unable to generate a detailed recommendation due to an error: {str(e)}"
            }

# Initialize the recommender
recommender = ProductRecommender()

async def get_product_recommendation(product_name: str, dietary_restrictions: List[str], store_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get a product recommendation based on store data and dietary restrictions
    
    Args:
        product_name: Name of the product
        dietary_restrictions: List of dietary restrictions
        store_data: Dictionary with store names as keys and product information as values
        
    Returns:
        Dictionary with product recommendation
    """
    return await recommender.get_recommendation(product_name, dietary_restrictions, store_data) 