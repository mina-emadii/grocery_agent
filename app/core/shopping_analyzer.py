import os
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DietaryRestriction(BaseModel):
    """Model for dietary restrictions"""
    name: str = Field(description="Name of the dietary restriction")
    description: str = Field(description="Description of the dietary restriction")
    keywords: List[str] = Field(description="Keywords to look for in product descriptions")

class ProductRequirement(BaseModel):
    """Model for product requirements based on dietary restrictions"""
    product_name: str = Field(description="Name of the product")
    dietary_restrictions: List[str] = Field(description="List of dietary restrictions that apply to this product")
    search_keywords: List[str] = Field(description="Keywords to use when searching for this product")
    must_have: List[str] = Field(description="Ingredients or attributes that must be present")
    must_not_have: List[str] = Field(description="Ingredients or attributes that must not be present")
    preferred_brands: List[str] = Field(description="Preferred brands if available")

class ShoppingListAnalysis(BaseModel):
    """Model for the analysis of a shopping list"""
    dietary_restrictions: List[DietaryRestriction] = Field(description="List of dietary restrictions identified")
    product_requirements: List[ProductRequirement] = Field(description="Requirements for each product in the list")
    general_preferences: Dict[str, Any] = Field(description="General shopping preferences")

class ShoppingAnalyzer:
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
        
        self.output_parser = PydanticOutputParser(pydantic_object=ShoppingListAnalysis)
        
        self.analysis_prompt = PromptTemplate(
            template="""
            Analyze the following shopping list and dietary restrictions:
            
            Shopping List:
            {shopping_list}
            
            Dietary Restrictions:
            {dietary_restrictions}
            
            Please identify:
            1. All dietary restrictions mentioned
            2. Specific requirements for each product based on these restrictions
            3. Keywords to use when searching for each product
            4. Ingredients or attributes that must be present or absent
            5. Any general shopping preferences
            
            {format_instructions}
            """,
            input_variables=["shopping_list", "dietary_restrictions"],
            partial_variables={"format_instructions": self.output_parser.get_format_instructions()}
        )
    
    async def analyze_shopping_list(self, shopping_list: List[str], dietary_restrictions: List[str]) -> ShoppingListAnalysis:
        """
        Analyze a shopping list and dietary restrictions to extract requirements
        
        Args:
            shopping_list: List of products to buy
            dietary_restrictions: List of dietary restrictions
            
        Returns:
            ShoppingListAnalysis object with extracted requirements
        """
        try:
            # Format the shopping list and dietary restrictions
            formatted_list = "\n".join([f"- {item}" for item in shopping_list])
            formatted_restrictions = "\n".join([f"- {restriction}" for item in dietary_restrictions])
            
            # Create the prompt
            prompt = self.analysis_prompt.format(
                shopping_list=formatted_list,
                dietary_restrictions=formatted_restrictions
            )
            
            # Get response from Gemini
            response = await self.model.ainvoke(prompt)
            
            # Parse the response
            analysis = self.output_parser.parse(response.content)
            
            logger.info(f"Successfully analyzed shopping list with {len(analysis.dietary_restrictions)} dietary restrictions")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing shopping list: {str(e)}")
            # Return a basic analysis with the original data
            return ShoppingListAnalysis(
                dietary_restrictions=[
                    DietaryRestriction(
                        name=restriction,
                        description=f"Dietary restriction: {restriction}",
                        keywords=[restriction]
                    ) for restriction in dietary_restrictions
                ],
                product_requirements=[
                    ProductRequirement(
                        product_name=item,
                        dietary_restrictions=dietary_restrictions,
                        search_keywords=[item],
                        must_have=[],
                        must_not_have=[],
                        preferred_brands=[]
                    ) for item in shopping_list
                ],
                general_preferences={"price_sensitivity": "medium"}
            )
    
    def get_search_criteria(self, analysis: ShoppingListAnalysis) -> Dict[str, Dict[str, Any]]:
        """
        Extract search criteria for each product from the analysis
        
        Args:
            analysis: ShoppingListAnalysis object
            
        Returns:
            Dictionary with product names as keys and search criteria as values
        """
        criteria = {}
        
        for product in analysis.product_requirements:
            criteria[product.product_name] = {
                "keywords": product.search_keywords,
                "must_have": product.must_have,
                "must_not_have": product.must_not_have,
                "dietary_restrictions": product.dietary_restrictions,
                "preferred_brands": product.preferred_brands
            }
        
        return criteria 