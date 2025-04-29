from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Grocery Agent API"}

def test_analyze_shopping_list():
    shopping_list = {
        "items": [
            {"name": "bread"},
            {"name": "milk"},
            {"name": "egg"},
            {"name": "apple"}
        ],
        "dietary_restrictions": ["lactose intolerant"]
    }
    
    response = client.post("/analyze-shopping-list", json=shopping_list)
    assert response.status_code == 200
    
    data = response.json()
    assert "recommendations" in data
    assert "total_estimated_cost" in data
    assert "dietary_restrictions_handled" in data
    assert len(data["recommendations"]) == 4
    assert data["dietary_restrictions_handled"] == ["lactose intolerant"]

def test_get_stores():
    response = client.get("/stores")
    assert response.status_code == 200
    assert "stores" in response.json()
    assert len(response.json()["stores"]) == 3 