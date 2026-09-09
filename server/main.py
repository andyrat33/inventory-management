import math
import os
import time
from collections import deque
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Literal, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, field_validator
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, restocking_orders, tasks

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def _order_year_month(order_date: str) -> str:
    """Return the 'YYYY-MM' prefix of an ISO date string, or '' if unparseable.

    Guards against the substring bug where e.g. month='2025' or month='0' would
    match on any date that merely contains those characters.
    """
    ym = (order_date or '')[:7]
    try:
        datetime.strptime(ym, "%Y-%m")
    except ValueError:
        return ''
    return ym

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month (YYYY-MM) or quarter (Q1-2025) on the order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        target_months = set(QUARTER_MAP.get(month, []))
    else:
        target_months = {month}

    if not target_months:
        return items

    return [item for item in items if _order_year_month(item.get('order_date', '')) in target_months]

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

def paginate(items: list, limit: Optional[int], offset: int) -> list:
    """Opt-in pagination: with no limit the full list is returned (unchanged
    behaviour); pass limit/offset to page through large collections."""
    if offset:
        items = items[offset:]
    if limit is not None:
        items = items[:limit]
    return items

# CORS middleware
# Explicit origin allowlist. Never pair "*" with allow_credentials=True: Starlette
# then reflects any request Origin back with Access-Control-Allow-Credentials: true.
# Override for other environments via ALLOWED_ORIGINS (comma-separated).
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lightweight per-IP rate limit (fixed window, in-process). Generous enough to be
# invisible in normal use; caps a script hammering the unauthenticated write
# endpoints. Tune with RATE_LIMIT_MAX / RATE_LIMIT_WINDOW; disable with
# RATE_LIMIT_MAX=0.
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "240"))
RATE_LIMIT_WINDOW = float(os.getenv("RATE_LIMIT_WINDOW", "60"))
_request_log: dict = {}

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if RATE_LIMIT_MAX > 0:
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        hits = _request_log.setdefault(client_ip, deque())
        while hits and now - hits[0] > RATE_LIMIT_WINDOW:
            hits.popleft()
        if len(hits) >= RATE_LIMIT_MAX:
            return JSONResponse(status_code=429, content={"detail": "Too many requests"})
        hits.append(now)
    return await call_next(request)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return the standard 422, but stringify any non-finite float in the error
    payload (e.g. a rejected `{"budget": Infinity}`) so the response itself can
    still be JSON-encoded instead of failing with a 500."""
    def clean(value):
        if isinstance(value, float) and not math.isfinite(value):
            return str(value)
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value

    errors = [clean(dict(err)) for err in exc.errors()]
    return JSONResponse(status_code=422, content=jsonable_encoder({"detail": errors}))

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class LowStockAlert(InventoryItem):
    # "critical" = out of stock or at/below half the reorder point; "low" = at/below it
    severity: Literal["critical", "low"]

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class Task(BaseModel):
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    priority: str = Field(pattern="^(high|medium|low)$")
    dueDate: str

    @field_validator("dueDate")
    @classmethod
    def _valid_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("dueDate must be a valid date in YYYY-MM-DD format")
        return v

class RestockingRecommendation(BaseModel):
    item_sku: str
    item_name: str
    category: str
    warehouse: str
    trend: str
    quantity_on_hand: int
    reorder_point: int
    forecasted_demand: int
    unit_cost: float
    recommended_quantity: int
    recommended_cost: float
    priority_score: float

class RestockingOrderItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    subtotal: float

class RestockingOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockingOrderItem]
    total_cost: float
    budget: float
    order_date: str
    expected_delivery: str
    lead_time_days: int
    status: str

class CreateRestockingOrderRequest(BaseModel):
    budget: float = Field(ge=0, le=1_000_000_000, allow_inf_nan=False)

# Restocking recommendation lead time (days)
RESTOCKING_LEAD_TIME_DAYS = 14

# Trend weighting used in the restocking priority score
TREND_SCORES = {'increasing': 1.0, 'stable': 0.5, 'decreasing': 0.0}

def compute_restocking_recommendations(budget: float) -> list:
    """Recommend items to restock within budget.

    Priority is a combined score of stockout urgency (how far quantity_on_hand
    sits below reorder_point) and demand trend, weighted 60/40. Items are filled
    greedily by score, each capped at the quantity needed to close the forecast
    gap (forecasted_demand - quantity_on_hand) and by remaining budget.
    """
    candidates = []
    for item in demand_forecasts:
        demand_gap = item['forecasted_demand'] - item['quantity_on_hand']
        if demand_gap <= 0:
            continue

        reorder_point = item['reorder_point']
        urgency = (reorder_point - item['quantity_on_hand']) / reorder_point if reorder_point > 0 else 0.0
        urgency = max(0.0, min(1.0, urgency))
        trend_score = TREND_SCORES.get(item['trend'], 0.5)
        priority_score = round(urgency * 0.6 + trend_score * 0.4, 4)

        candidates.append({**item, 'demand_gap': demand_gap, 'priority_score': priority_score})

    candidates.sort(key=lambda c: c['priority_score'], reverse=True)

    recommendations = []
    remaining_budget = budget
    for c in candidates:
        if remaining_budget <= 0:
            break
        max_affordable = int(remaining_budget // c['unit_cost'])
        recommended_quantity = min(c['demand_gap'], max_affordable)
        if recommended_quantity <= 0:
            continue

        recommended_cost = round(recommended_quantity * c['unit_cost'], 2)
        remaining_budget -= recommended_cost
        recommendations.append({
            'item_sku': c['item_sku'],
            'item_name': c['item_name'],
            'category': c['category'],
            'warehouse': c['warehouse'],
            'trend': c['trend'],
            'quantity_on_hand': c['quantity_on_hand'],
            'reorder_point': c['reorder_point'],
            'forecasted_demand': c['forecasted_demand'],
            'unit_cost': c['unit_cost'],
            'recommended_quantity': recommended_quantity,
            'recommended_cost': recommended_cost,
            'priority_score': c['priority_score']
        })

    return recommendations

def generate_restocking_order_id():
    """Generate a new restocking order id"""
    if not restocking_orders:
        return "1"
    return str(max(int(o["id"]) for o in restocking_orders) + 1)

def generate_restocking_order_number():
    """Generate a new restocking order number, e.g. RSO-2026-0001"""
    return f"RSO-{datetime.now().year}-{str(len(restocking_orders) + 1).zfill(4)}"

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

def _stock_severity(item: dict) -> Optional[str]:
    """'critical' if out of stock or at/below half the reorder point, 'low' if
    at/below it, otherwise None (item is adequately stocked)."""
    qty, reorder = item.get("quantity_on_hand", 0), item.get("reorder_point", 0)
    if qty > reorder:
        return None
    return "critical" if qty == 0 or qty * 2 <= reorder else "low"

# NOTE: must be declared before /api/inventory/{item_id} or FastAPI would match
# "low-stock" as an item_id and 404.
@app.get("/api/inventory/low-stock", response_model=List[LowStockAlert])
def get_low_stock_alerts(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Inventory items at or below their reorder point, tagged with a severity
    and sorted critical-first then by how far below the reorder point they sit."""
    alerts = []
    for item in apply_filters(inventory_items, warehouse, category):
        severity = _stock_severity(item)
        if severity:
            alerts.append({**item, "severity": severity})

    severity_rank = {"critical": 0, "low": 1}
    alerts.sort(key=lambda a: (
        severity_rank[a["severity"]],
        a["quantity_on_hand"] - a["reorder_point"],
    ))
    return alerts

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None,
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all orders with optional filtering and opt-in limit/offset pagination"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return paginate(filtered_orders, limit, offset)

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

# Reverse index: 'YYYY-MM' -> its quarter label
_MONTH_TO_QUARTER = {m: q for q, months in QUARTER_MAP.items() for m in months}

@app.get("/api/reports/quarterly")
def get_quarterly_reports(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get quarterly performance reports, honouring the shared filter bar"""
    filtered = apply_filters(orders, warehouse, category, status)
    filtered = filter_by_month(filtered, month)

    quarters = {}
    for order in filtered:
        quarter = _MONTH_TO_QUARTER.get(_order_year_month(order.get('order_date', '')))
        if not quarter:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get month-over-month trends, honouring the shared filter bar"""
    filtered = apply_filters(orders, warehouse, category, status)
    filtered = filter_by_month(filtered, month)

    months = {}
    for order in filtered:
        ym = _order_year_month(order.get('order_date', ''))
        if not ym:
            continue

        if ym not in months:
            months[ym] = {
                'month': ym,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[ym]['order_count'] += 1
        months[ym]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[ym]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

def generate_task_id():
    """Generate a new task id, starting well above the client-side mock ids (1-4)"""
    if not tasks:
        return "1000"
    return str(max(int(t["id"]) for t in tasks) + 1)

@app.get("/api/tasks", response_model=List[Task])
def get_tasks(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all tasks with opt-in limit/offset pagination"""
    return paginate(tasks, limit, offset)

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(task_data: CreateTaskRequest):
    """Create a new task"""
    new_task = {
        "id": generate_task_id(),
        "title": task_data.title,
        "priority": task_data.priority,
        "dueDate": task_data.dueDate,
        "status": "pending"
    }
    tasks.append(new_task)
    return new_task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task"""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    tasks.remove(task)
    return {"message": f"Task {task_id} deleted successfully"}

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task's status between pending and completed"""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.get("/api/restocking/recommendations", response_model=List[RestockingRecommendation])
def get_restocking_recommendations(budget: float = Query(..., ge=0)):
    """Recommend items to restock within the given budget, ranked by a combined
    stockout-urgency + demand-trend priority score"""
    return compute_restocking_recommendations(budget)

@app.get("/api/restocking-orders", response_model=List[RestockingOrder])
def get_restocking_orders(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get all submitted restocking orders with opt-in limit/offset pagination"""
    return paginate(restocking_orders, limit, offset)

@app.post("/api/restocking-orders", response_model=RestockingOrder, status_code=201)
def create_restocking_order(request: CreateRestockingOrderRequest):
    """Submit a restocking order, recomputed server-side from the given budget
    so the submitted order always matches the current recommendation logic"""
    recommendations = compute_restocking_recommendations(request.budget)
    if not recommendations:
        raise HTTPException(status_code=400, detail="No items can be recommended for this budget")

    order_items = [
        {
            "sku": r["item_sku"],
            "name": r["item_name"],
            "quantity": r["recommended_quantity"],
            "unit_cost": r["unit_cost"],
            "subtotal": r["recommended_cost"]
        }
        for r in recommendations
    ]
    total_cost = round(sum(item["subtotal"] for item in order_items), 2)
    order_date = datetime.now()
    expected_delivery = order_date + timedelta(days=RESTOCKING_LEAD_TIME_DAYS)

    new_order = {
        "id": generate_restocking_order_id(),
        "order_number": generate_restocking_order_number(),
        "items": order_items,
        "total_cost": total_cost,
        "budget": request.budget,
        "order_date": order_date.isoformat(),
        "expected_delivery": expected_delivery.isoformat(),
        "lead_time_days": RESTOCKING_LEAD_TIME_DAYS,
        "status": "Processing"
    }
    restocking_orders.append(new_order)
    return new_order

if __name__ == "__main__":
    import uvicorn
    # Bind loopback by default; set HOST=0.0.0.0 to expose (e.g. behind a proxy).
    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8001")))
