from fastapi.testclient import TestClient
from app import app

# Allows to fake send requests to my FastAPI app
# Tool for Automated Testing
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready():
    with TestClient(app) as client:
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


def test_predict():
    # Because it is a post, it requires a body
    response = client.post("/predict", json={"value": 5})

    assert response.status_code == 200

    data = response.json()  # Store the full request body

    # Assert the response contains the 'prediction' key
    # And returns the correct value (2 * x)
    assert "prediction" in data
    assert data["prediction"] == 10


def test_predict_missing_value():
    response = client.post("/predict", json={})

    assert response.status_code == 422


def test_predict_wrong_type():
    response = client.post("/predict", json={"value": "Incompatible input"})

    assert response.status_code == 422


# Testing an edge case
def test_predict_float():
    response = client.post("/predict", json={"value": 2.5})

    assert response.status_code == 200
    assert response.json()["prediction"] == 5.0
