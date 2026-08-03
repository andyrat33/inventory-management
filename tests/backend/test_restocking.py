"""
Tests for restocking recommendation and order API endpoints.
"""
import sys
from pathlib import Path

import pytest

# Add server directory to path to import mock_data directly
server_path = Path(__file__).parent.parent.parent / "server"
sys.path.insert(0, str(server_path))

import mock_data


@pytest.fixture(autouse=True)
def reset_restocking_orders():
    """Reset the in-memory restocking orders list around each test to keep tests independent."""
    original = list(mock_data.restocking_orders)
    mock_data.restocking_orders.clear()
    yield
    mock_data.restocking_orders.clear()
    mock_data.restocking_orders.extend(original)


class TestDemandForecastFields:
    """Demand forecast now carries the fields restocking needs (unit_cost, stock levels)."""

    def test_demand_forecast_has_restocking_fields(self, client):
        """Test that demand forecast entries include restocking-related fields."""
        response = client.get("/api/demand")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0

        for item in data:
            assert "unit_cost" in item
            assert "quantity_on_hand" in item
            assert "reorder_point" in item
            assert "warehouse" in item
            assert "category" in item
            assert isinstance(item["unit_cost"], (int, float))
            assert isinstance(item["quantity_on_hand"], int)
            assert isinstance(item["reorder_point"], int)


class TestRestockingRecommendationsEndpoint:
    """Test suite for GET /api/restocking/recommendations."""

    def test_requires_budget_param(self, client):
        """Test that omitting the budget query param returns a validation error."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422

    def test_zero_budget_returns_no_recommendations(self, client):
        """Test that a zero budget recommends nothing."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200
        assert response.json() == []

    def test_small_budget_returns_recommendations(self, client):
        """Test that a reasonable budget returns recommended items within cost."""
        response = client.get("/api/restocking/recommendations?budget=50000")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        total_cost = sum(item["recommended_cost"] for item in data)
        assert total_cost <= 50000

        for item in data:
            assert "item_sku" in item
            assert "item_name" in item
            assert "recommended_quantity" in item
            assert "recommended_cost" in item
            assert "priority_score" in item
            assert item["recommended_quantity"] > 0
            assert abs(item["recommended_cost"] - item["recommended_quantity"] * item["unit_cost"]) < 0.01

    def test_recommendations_sorted_by_priority_score_descending(self, client):
        """Test that recommended items are ordered highest priority first."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()
        assert len(data) > 1

        scores = [item["priority_score"] for item in data]
        assert scores == sorted(scores, reverse=True)

    def test_larger_budget_recommends_at_least_as_many_items(self, client):
        """Test that increasing the budget never reduces the number of recommended items."""
        small = client.get("/api/restocking/recommendations?budget=5000").json()
        large = client.get("/api/restocking/recommendations?budget=500000").json()

        assert len(large) >= len(small)

    def test_recommended_quantity_never_exceeds_forecast_gap(self, client):
        """Test that recommended quantity never exceeds forecasted_demand - quantity_on_hand."""
        response = client.get("/api/restocking/recommendations?budget=500000")
        data = response.json()

        for item in data:
            gap = item["forecasted_demand"] - item["quantity_on_hand"]
            assert item["recommended_quantity"] <= gap

    def test_well_stocked_items_not_recommended(self, client):
        """Test that items with quantity_on_hand already meeting forecasted demand are excluded."""
        response = client.get("/api/restocking/recommendations?budget=500000")
        data = response.json()

        skus = {item["item_sku"] for item in data}
        # PSU-501 is stocked well above its forecasted demand in the mock data
        assert "PSU-501" not in skus


class TestRestockingOrdersEndpoint:
    """Test suite for GET/POST /api/restocking-orders."""

    def test_get_orders_empty(self, client):
        """Test getting restocking orders when none have been submitted."""
        response = client.get("/api/restocking-orders")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_order(self, client):
        """Test submitting a restocking order for a given budget."""
        response = client.post("/api/restocking-orders", json={"budget": 50000})
        assert response.status_code == 201

        order = response.json()
        assert "id" in order
        assert order["order_number"].startswith("RSO-")
        assert order["budget"] == 50000
        assert order["status"] == "Processing"
        assert order["lead_time_days"] == 14
        assert len(order["items"]) > 0
        assert order["total_cost"] <= 50000

        calculated_total = sum(item["subtotal"] for item in order["items"])
        assert abs(order["total_cost"] - calculated_total) < 0.01

    def test_create_order_expected_delivery_after_order_date(self, client):
        """Test that expected_delivery is lead_time_days after order_date."""
        from datetime import datetime

        order = client.post("/api/restocking-orders", json={"budget": 50000}).json()

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])

        assert (expected_delivery - order_date).days == order["lead_time_days"]

    def test_create_order_zero_budget_fails(self, client):
        """Test that a budget too small to afford any item returns a 400."""
        response = client.post("/api/restocking-orders", json={"budget": 0})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data

    def test_created_order_appears_in_list(self, client):
        """Test that a submitted order shows up in the restocking orders list."""
        created = client.post("/api/restocking-orders", json={"budget": 50000}).json()

        response = client.get("/api/restocking-orders")
        data = response.json()

        assert len(data) == 1
        assert data[0]["id"] == created["id"]

    def test_create_multiple_orders_unique_ids(self, client):
        """Test that multiple submitted orders get distinct, incrementing ids and order numbers."""
        first = client.post("/api/restocking-orders", json={"budget": 20000}).json()
        second = client.post("/api/restocking-orders", json={"budget": 20000}).json()

        assert first["id"] != second["id"]
        assert int(second["id"]) > int(first["id"])
        assert first["order_number"] != second["order_number"]
