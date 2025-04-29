# Grocery Agent

A smart grocery shopping assistant that helps users find the best deals and manage their shopping lists. The application provides recommendations based on dietary restrictions and price comparisons across multiple stores.

## Features

- Search for products across multiple stores (Walmart, Target, Safeway, Whole Foods)
- Get price comparisons and availability information
- Filter products based on dietary restrictions
- Get smart recommendations using LLM
- RESTful API interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/grocery_agent.git
cd grocery_agent
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
```

## Usage

1. Start the server:
```bash
uvicorn app.main:app --reload --port 8001
```

2. Access the API documentation at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## API Endpoints

- `POST /analyze-shopping-list`: Analyze a shopping list and get recommendations
- `GET /stores`: Get list of available stores and their locations

## Example Request

```bash
curl -X POST "http://localhost:8001/analyze-shopping-list" \
     -H "Content-Type: application/json" \
     -d '{"items": [{"name": "bread", "dietary_restrictions": ["gluten-free", "vegan"]}]}'
```

## License

MIT 