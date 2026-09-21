"""Acceptance tests for the StadiumServe order lifecycle.

Acceptance criteria:
    1. A customer can create an order for a seat with items.
    2. The system records the order with an initial status of pending.
    3. The order can progress through the valid lifecycle.
    4. Invalid status transitions are rejected.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, relative_path: str):
    module_file = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {module_file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_acceptance_create_order_and_pending_status(monkeypatch):
    """Acceptance: a customer can submit an order and it starts in pending state."""
    order_module = load_module("create_order", "lambdas/createOrder/app.py")

    class FakeTable:
        def __init__(self):
            self.items = []

        def put_item(self, Item):
            self.items.append(Item)

    fake_table = FakeTable()
    monkeypatch.setattr(order_module, "table", fake_table)

    event = {
        "body": '{"customerId": "cust-123", "customerName": "Sipho M.", "seatNumber": "A12", "currency": "ZAR", "items": [{"name": "Castle Lager", "quantity": 2, "price": 45.0}]}'
    }

    response = order_module.lambda_handler(event, None)

    assert response["statusCode"] == 201
    payload = response["body"]
    assert "Order created successfully" in payload
    assert "\"status\": \"pending\"" in payload
    assert "\"seatNumber\": \"A12\"" in payload
    assert fake_table.items


def test_acceptance_order_status_machine_allows_valid_transitions():
    """Acceptance: valid transitions advance the order through the lifecycle."""
    update_module = load_module("update_order_status", "lambdas/updateOrderStatus/app.py")

    valid_transitions = [
        ("pending", "preparing"),
        ("preparing", "ready"),
        ("ready", "out_for_delivery"),
        ("out_for_delivery", "delivered"),
    ]

    for current, next_status in valid_transitions:
        assert next_status in update_module.TRANSITIONS.get(current, [])


def test_acceptance_order_status_machine_rejects_invalid_transition():
    """Acceptance: invalid transitions are rejected before updating the order."""
    update_module = load_module("update_order_status", "lambdas/updateOrderStatus/app.py")

    assert "delivered" not in update_module.TRANSITIONS.get("pending", [])
    assert "ready" not in update_module.TRANSITIONS.get("pending", [])
    assert "preparing" not in update_module.TRANSITIONS.get("ready", [])
