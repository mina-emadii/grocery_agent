# AI Grocery Shopping Assistant

An intelligent shopping assistant that helps users find grocery products based on their dietary restrictions, budget constraints, and location preferences.

## Features

- Natural language input processing
- Support for multiple dietary restrictions (vegan, gluten-free, organic, etc.)
- Real-time product search across multiple stores
- Budget tracking and validation
- Location-based store selection
- Detailed product information including:
  - Price
  - Store availability
  - Organic status
  - Product links
  - Unit pricing
- Results saved to JSON for further analysis

## Requirements

- Python 3.8+
- OpenAI API key
- SerpAPI key

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

3. Create a `.env` file in the project root with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
SERPAPI_KEY=your_serpapi_key
```

## Usage

Run the assistant:
```bash
python main.py
```

Example queries:
- "I need organic milk and gluten-free bread in San Francisco, with a budget of $20 per item"
- "Find me some snacks and fruits in LA, total budget $50, must be vegan"

## Output

The assistant will:
1. Parse your request for items, dietary restrictions, budget, and location
2. Search for products across multiple stores
3. Display recommended products with detailed information
4. Save complete results to `shopping_results.json`

## Contributing

Feel free to open issues or submit pull requests with improvements.

## License

MIT License 