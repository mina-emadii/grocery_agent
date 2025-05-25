import requests
import json

def test_openfoodfacts():
    # Simple test with a very common product
    url = "https://world.openfoodfacts.org/api/v0/product/737628064502.json"
    
    print("Testing OpenFoodFacts API...")
    print(f"URL: {url}")
    
    try:
        # Make the request with a long timeout
        response = requests.get(url, timeout=30)
        
        # Print status code
        print(f"\nStatus Code: {response.status_code}")
        
        # Print headers
        print("\nResponse Headers:")
        for key, value in response.headers.items():
            print(f"{key}: {value}")
        
        # Try to parse JSON
        try:
            data = response.json()
            print("\nResponse Data:")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError as e:
            print(f"\nError parsing JSON: {e}")
            print("\nRaw Response:")
            print(response.text[:500])  # Print first 500 chars of raw response
            
    except requests.exceptions.RequestException as e:
        print(f"\nRequest Error: {e}")

if __name__ == "__main__":
    test_openfoodfacts() 