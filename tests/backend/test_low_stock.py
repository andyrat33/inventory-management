"""
Tests for the low-stock alerts endpoint: GET /api/inventory/low-stock
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))
import mock_data


def _expected_severity(item):
    qty, reorder = item["quantity_on_hand"], item["reorder_point"]
    if qty == 0 or qty * 2 <= reorder:
        return "critical"
    return "low"


class TestLowStockAlerts:
    def test_returns_only_items_at_or_below_reorder_point(self, client):
        response = client.get("/api/inventory/low-stock")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        for alert in data:
            assert alert["quantity_on_hand"] <= alert["reorder_point"]

    def test_matches_the_low_stock_count_from_the_full_inventory(self, client):
        inventory = client.get("/api/inventory").json()
        expected = [i for i in inventory if i["quantity_on_hand"] <= i["reorder_point"]]
        alerts = client.get("/api/inventory/low-stock").json()
        assert {a["sku"] for a in alerts} == {i["sku"] for i in expected}

    def test_each_alert_carries_the_inventory_shape_plus_severity(self, client):
        alert = client.get("/api/inventory/low-stock").json()[0]
        for field in ("id", "sku", "name", "category", "warehouse",
                      "quantity_on_hand", "reorder_point", "unit_cost", "location"):
            assert field in alert
        assert alert["severity"] in ("critical", "low")

    def test_severity_follows_the_rule(self, client):
        for alert in client.get("/api/inventory/low-stock").json():
            assert alert["severity"] == _expected_severity(alert)

    def test_sorted_critical_first_then_by_deficit(self, client):
        data = client.get("/api/inventory/low-stock").json()
        rank = {"critical": 0, "low": 1}
        keys = [(rank[a["severity"]], a["quantity_on_hand"] - a["reorder_point"]) for a in data]
        assert keys == sorted(keys)

    def test_route_is_not_shadowed_by_the_item_id_route(self, client):
        """/api/inventory/low-stock must not be parsed as /api/inventory/{item_id}."""
        low_stock = client.get("/api/inventory/low-stock")
        assert low_stock.status_code == 200
        assert isinstance(low_stock.json(), list)

        # the {item_id} route still works for real ids
        first_id = client.get("/api/inventory").json()[0]["id"]
        assert client.get(f"/api/inventory/{first_id}").status_code == 200

    def test_warehouse_filter(self, client):
        all_alerts = client.get("/api/inventory/low-stock").json()
        # pick a warehouse that actually has a low-stock item
        target = all_alerts[0]["warehouse"]
        filtered = client.get("/api/inventory/low-stock", params={"warehouse": target}).json()
        assert len(filtered) >= 1
        assert all(a["warehouse"] == target for a in filtered)
        assert len(filtered) <= len(all_alerts)

    def test_category_filter(self, client):
        all_alerts = client.get("/api/inventory/low-stock").json()
        target = all_alerts[0]["category"]
        filtered = client.get("/api/inventory/low-stock", params={"category": target}).json()
        assert all(a["category"].lower() == target.lower() for a in filtered)

    def test_filter_with_no_matches_returns_empty_list(self, client):
        response = client.get("/api/inventory/low-stock", params={"category": "Nonexistent"})
        assert response.status_code == 200
        assert response.json() == []


class TestCriticalSeverity:
    """The seed data has no critical items, so inject a couple to cover that path."""

    @pytest.fixture(autouse=True)
    def _inject_critical_items(self):
        original = list(mock_data.inventory_items)
        mock_data.inventory_items.extend([
            {
                "id": "TEST-CRIT-1", "sku": "ZZZ-001", "name": "Test out-of-stock widget",
                "category": "Sensors", "warehouse": "London",
                "quantity_on_hand": 0, "reorder_point": 40,
                "unit_cost": 1.0, "location": "Z-01", "last_updated": "2025-09-30T00:00:00",
            },
            {
                "id": "TEST-CRIT-2", "sku": "ZZZ-002", "name": "Test half-empty widget",
                "category": "Sensors", "warehouse": "London",
                "quantity_on_hand": 10, "reorder_point": 40,  # 10*2 <= 40 -> critical
                "unit_cost": 1.0, "location": "Z-02", "last_updated": "2025-09-30T00:00:00",
            },
        ])
        yield
        mock_data.inventory_items[:] = original

    def test_out_of_stock_and_half_empty_are_critical(self, client):
        by_sku = {a["sku"]: a for a in client.get("/api/inventory/low-stock").json()}
        assert by_sku["ZZZ-001"]["severity"] == "critical"
        assert by_sku["ZZZ-002"]["severity"] == "critical"

    def test_critical_items_sort_before_low_ones(self, client):
        data = client.get("/api/inventory/low-stock").json()
        severities = [a["severity"] for a in data]
        # no "low" appears before any "critical"
        assert severities == sorted(severities, key=lambda s: 0 if s == "critical" else 1)
        assert data[0]["severity"] == "critical"

    def test_an_item_just_above_half_is_low_not_critical(self, client):
        mock_data.inventory_items.append({
            "id": "TEST-LOW-1", "sku": "ZZZ-003", "name": "Test just-low widget",
            "category": "Sensors", "warehouse": "London",
            "quantity_on_hand": 21, "reorder_point": 40,  # 21*2 = 42 > 40 -> low
            "unit_cost": 1.0, "location": "Z-03", "last_updated": "2025-09-30T00:00:00",
        })
        by_sku = {a["sku"]: a for a in client.get("/api/inventory/low-stock").json()}
        assert by_sku["ZZZ-003"]["severity"] == "low"
