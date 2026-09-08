"""
Tests for the /api/reports/* endpoints — including the shared filter-bar params
(warehouse, category, status, month) that the Reports page now sends.
"""


class TestQuarterlyReports:
    def test_get_quarterly(self, client):
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4  # Q1..Q4 2025
        assert [q["quarter"] for q in data] == ["Q1-2025", "Q2-2025", "Q3-2025", "Q4-2025"]
        for q in data:
            for field in ("total_orders", "total_revenue", "avg_order_value", "fulfillment_rate"):
                assert field in q
            assert 0 <= q["fulfillment_rate"] <= 100

    def test_quarterly_totals_match_unfiltered_orders(self, client):
        orders = client.get("/api/orders").json()
        quarterly = client.get("/api/reports/quarterly").json()
        assert sum(q["total_orders"] for q in quarterly) == len(orders)

    def test_quarterly_respects_warehouse_filter(self, client):
        unfiltered = client.get("/api/reports/quarterly").json()
        tokyo = client.get("/api/reports/quarterly?warehouse=Tokyo").json()

        total_all = sum(q["total_orders"] for q in unfiltered)
        total_tokyo = sum(q["total_orders"] for q in tokyo)
        assert 0 < total_tokyo < total_all

        tokyo_orders = client.get("/api/orders?warehouse=Tokyo").json()
        assert total_tokyo == len(tokyo_orders)

    def test_quarterly_respects_month_filter(self, client):
        """month=2025-01 collapses the report to Q1 only."""
        data = client.get("/api/reports/quarterly?month=2025-01").json()
        assert [q["quarter"] for q in data] == ["Q1-2025"]

    def test_quarterly_respects_status_filter(self, client):
        data = client.get("/api/reports/quarterly?status=Delivered").json()
        # every counted order is delivered, so fulfilment is 100% wherever there are orders
        for q in data:
            if q["total_orders"] > 0:
                assert q["fulfillment_rate"] == 100.0

    def test_quarterly_bad_month_returns_nothing(self, client):
        """A year-only value is not a valid YYYY-MM and must not match every row
        (the old substring quarter detection would have)."""
        data = client.get("/api/reports/quarterly?month=2025").json()
        assert data == []


class TestMonthlyTrends:
    def test_get_monthly_trends(self, client):
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 12
        assert data == sorted(data, key=lambda m: m["month"])
        for m in data:
            for field in ("month", "order_count", "revenue", "delivered_count"):
                assert field in m
            assert len(m["month"]) == 7  # YYYY-MM

    def test_monthly_totals_match_unfiltered_orders(self, client):
        orders = client.get("/api/orders").json()
        monthly = client.get("/api/reports/monthly-trends").json()
        assert sum(m["order_count"] for m in monthly) == len(orders)

    def test_monthly_respects_category_filter(self, client):
        unfiltered = client.get("/api/reports/monthly-trends").json()
        sensors = client.get("/api/reports/monthly-trends?category=Sensors").json()
        assert sum(m["order_count"] for m in sensors) < sum(m["order_count"] for m in unfiltered)

        sensor_orders = client.get("/api/orders?category=Sensors").json()
        assert sum(m["order_count"] for m in sensors) == len(sensor_orders)

    def test_monthly_respects_month_filter(self, client):
        data = client.get("/api/reports/monthly-trends?month=2025-03").json()
        assert [m["month"] for m in data] == ["2025-03"]

    def test_monthly_combined_filters(self, client):
        data = client.get(
            "/api/reports/monthly-trends?warehouse=London&category=Controllers"
        ).json()
        ref = client.get("/api/orders?warehouse=London&category=Controllers").json()
        assert sum(m["order_count"] for m in data) == len(ref)
