# Grocery Agent

A smart grocery shopping assistant that helps users find the best deals and manage their shopping lists based on dietary restrictions.

## Features

- Analyze shopping lists and dietary restrictions using LangChain and Gemini
- Scrape real-time prices from major grocery stores (Walmart, Target, Safeway, Whole Foods)
- Provide personalized product recommendations based on dietary needs
- Compare prices across stores to find the best deals
- Support for various dietary restrictions including halal, gluten-free, vegan, and organic

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/grocery_agent.git
cd grocery_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following content:
```
# API Keys
GOOGLE_API_KEY=your_google_api_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

## Usage

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. Send a POST request to `/analyze-shopping-list` with your shopping list and dietary restrictions:
```json
{
  "items": ["chicken", "rice", "vegetables"],
  "dietary_restrictions": ["halal", "gluten-free"]
}
```

3. Receive recommendations for each item and the best store to buy from:
```json
{
  "recommendations": {
    "chicken": {
      "store": "whole_foods",
      "product_name": "Organic Halal Chicken Breast",
      "price": 8.99,
      "is_suitable": true,
      "dietary_info": {
        "restrictions_handled": ["halal", "organic"],
        "ingredients": ["chicken", "water", "sea salt"],
        "allergen_info": "Contains: None"
      },
      "explanation": "This product meets all dietary restrictions and is from a reputable brand."
    },
    "rice": {
      "store": "walmart",
      "product_name": "Basmati Rice",
      "price": 3.99,
      "is_suitable": true,
      "dietary_info": {
        "restrictions_handled": ["gluten-free", "vegan"],
        "ingredients": ["rice"],
        "allergen_info": "Contains: None"
      },
      "explanation": "This product is gluten-free and offers the best value."
    },
    "vegetables": {
      "store": "safeway",
      "product_name": "Organic Mixed Vegetables",
      "price": 4.49,
      "is_suitable": true,
      "dietary_info": {
        "restrictions_handled": ["organic", "vegan", "gluten-free"],
        "ingredients": ["broccoli", "carrots", "cauliflower"],
        "allergen_info": "Contains: None"
      },
      "explanation": "This product is organic and offers a good variety of vegetables."
    }
  },
  "total_cost": {
    "walmart": 17.47,
    "target": 18.99,
    "safeway": 16.97,
    "whole_foods": 22.47
  },
  "best_store": "safeway",
  "explanation": "The best store to buy all items from is safeway with a total cost of $16.97. This recommendation is based on price, availability, and dietary restrictions."
}
```

## Architecture

The application consists of the following components:

1. **Shopping Analyzer**: Uses LangChain and Gemini to analyze shopping lists and dietary restrictions
2. **Store Scraper**: Uses Scrapy to scrape real-time prices from store websites
3. **Product Recommender**: Uses Gemini to generate personalized product recommendations
4. **FastAPI Backend**: Provides a RESTful API for interacting with the application

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 