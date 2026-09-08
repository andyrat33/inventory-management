"""
Tests for API input bounds, opt-in pagination, and the month-filter fix (P1-2).
"""
import sys
from pathlib import Path

import pytest

server_path = Path(__file__).parent.parent.parent / "server"
sys.path.insert(0, str(server_path))

import mock_data


@pytest.fixture(autouse=True)
def reset_restocking_orders():
    """Keep restocking-order tests independent."""
    original = list(mock_data.restocking_orders)
    mock_data.restocking_orders.clear()
    yield
    mock_data.restocking_orders.clear()
    mock_data.restocking_orders.extend(original)


class TestRestockingBudgetValidation:
    """CreateRestockingOrderRequest.budget must be a finite, bounded, non-negative float."""

    def test_reject_negative_budget(self, client):
        response = client.post("/api/restocking-orders", json={"budget": -1})
        assert response.status_code == 422

    def test_reject_infinite_budget(self, client):
        """`{"budget": Infinity}` is valid JSON to Python's parser and previously
        reached the endpoint, raising an unhandled 500 in `int(inf // cost)`."""
        response = client.post(
            "/api/restocking-orders",
            content='{"budget": Infinity}',
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_reject_nan_budget(self, client):
        response = client.post(
            "/api/restocking-orders",
            content='{"budget": NaN}',
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_reject_budget_over_cap(self, client):
        response = client.post("/api/restocking-orders", json={"budget": 2_000_000_000})
        assert response.status_code == 422

    def test_accepts_reasonable_budget(self, client):
        response = client.post("/api/restocking-orders", json={"budget": 50000})
        assert response.status_code == 201


class TestOrdersMonthFilter:
    """month= must match on the YYYY-MM prefix, not as a bare substring."""

    def test_year_only_does_not_match_everything(self, client):
        """month='2025' is not a valid YYYY-MM and must return nothing (previously
        the substring match returned every 2025 row)."""
        all_orders = client.get("/api/orders").json()
        assert len(all_orders) > 0

        response = client.get("/api/orders?month=2025")
        assert response.status_code == 200
        assert response.json() == []

    def test_single_digit_does_not_match(self, client):
        """month='0' previously matched any date containing a '0'."""
        response = client.get("/api/orders?month=0")
        assert response.status_code == 200
        assert response.json() == []

    def test_valid_month_filters_correctly(self, client):
        response = client.get("/api/orders?month=2025-01")
        assert response.status_code == 200
        for order in response.json():
            assert order["order_date"][:7] == "2025-01"

    def test_month_all_returns_everything(self, client):
        everything = client.get("/api/orders").json()
        explicit_all = client.get("/api/orders?month=all").json()
        assert len(explicit_all) == len(everything)


class TestOrdersPagination:
    """limit/offset are opt-in and leave the default (full list) untouched."""

    def test_default_is_unpaginated(self, client):
        data = client.get("/api/orders").json()
        assert len(data) > 20  # full mock dataset

    def test_limit_caps_results(self, client):
        data = client.get("/api/orders?limit=10").json()
        assert len(data) == 10

    def test_offset_skips_leading_results(self, client):
        first_two = client.get("/api/orders?limit=2").json()
        after_offset = client.get("/api/orders?limit=2&offset=2").json()
        assert [o["id"] for o in first_two] != [o["id"] for o in after_offset]

    def test_invalid_limit_rejected(self, client):
        assert client.get("/api/orders?limit=0").status_code == 422
        assert client.get("/api/orders?limit=99999").status_code == 422

    def test_negative_offset_rejected(self, client):
        assert client.get("/api/orders?offset=-1").status_code == 422
