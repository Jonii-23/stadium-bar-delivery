"""Unit tests for the Lambda business logic.

These tests exercise the pure validation and transition logic in the order functions.
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


def test_calculate_total_sums_item_prices():
    create_module = load_module("create_order", "lambdas/createOrder/app.py")

    items = [
        {"name": "Castle Lager", "quantity": 2, "price": 45.0},
        {"name": "Chicken Burger", "quantity": 1, "price": 85.0},
    ]

    assert create_module.calculate_total(items) == 175.0


def test_create_order_requires_customer_name_seat_and_items(monkeypatch):
    create_module = load_module("create_order", "lambdas/createOrder/app.py")

    class FakeTable:
        def put_item(self, Item):
            raise AssertionError("put_item should not be called for invalid data")

    monkeypatch.setattr(create_module, "table", FakeTable())

    event = {"body": '{"customerId": "cust-123", "customerName": "", "seatNumber": "", "items": []}' }

    response = create_module.lambda_handler(event, None)

    assert response["statusCode"] == 400
    assert "customerName, seatNumber and items are required" in response["body"]


def test_invalid_status_transition_is_rejected():
    update_module = load_module("update_order_status", "lambdas/updateOrderStatus/app.py")

    assert "delivered" not in update_module.TRANSITIONS["pending"]


def test_create_order_publishes_bar_staff_notification(monkeypatch):
    create_module = load_module("create_order", "lambdas/createOrder/app.py")

    class FakeTable:
        def put_item(self, Item):
            pass

    class FakeSNS:
        def __init__(self):
            self.published = []

        def publish(self, TopicArn, Subject, Message, MessageAttributes=None):
            self.published.append({
                "TopicArn": TopicArn,
                "Subject": Subject,
                "Message": Message,
                "MessageAttributes": MessageAttributes,
            })
            return {"MessageId": "abc-123"}

    fake_table = FakeTable()
    fake_sns = FakeSNS()
    monkeypatch.setattr(create_module, "table", fake_table)
    monkeypatch.setattr(create_module, "get_sns_client", lambda: fake_sns)
    monkeypatch.setenv("BAR_STAFF_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:bar-staff")

    event = {
        "body": '{"customerId": "cust-123", "customerName": "Sipho M.", "seatNumber": "A12", "currency": "ZAR", "items": [{"name": "Castle Lager", "quantity": 2, "price": 45.0}]}'
    }

    response = create_module.lambda_handler(event, None)

    assert response["statusCode"] == 201
    assert fake_sns.published
    assert fake_sns.published[0]["TopicArn"] == "arn:aws:sns:us-east-1:123456789012:bar-staff"
    assert "New order received" in fake_sns.published[0]["Subject"]


def test_status_update_publishes_ready_notification(monkeypatch):
    update_module = load_module("update_order_status", "lambdas/updateOrderStatus/app.py")

    class FakeTable:
        def get_item(self, Key):
            return {"Item": {"status": "preparing", "orderId": "ord-123"}}

        def update_item(self, **kwargs):
            return {"Attributes": {"status": "ready", "orderId": "ord-123"}}

    class FakeSNS:
        def __init__(self):
            self.published = []

        def publish(self, TopicArn, Subject, Message, MessageAttributes=None):
            self.published.append({
                "TopicArn": TopicArn,
                "Subject": Subject,
                "Message": Message,
                "MessageAttributes": MessageAttributes,
            })
            return {"MessageId": "ready-123"}

    fake_table = FakeTable()
    fake_sns = FakeSNS()
    monkeypatch.setattr(update_module, "table", fake_table)
    monkeypatch.setattr(update_module, "get_sns_client", lambda: fake_sns)
    monkeypatch.setenv("DELIVERY_STAFF_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:delivery-staff")

    event = {"body": '{"orderId": "ord-123", "status": "ready"}'}

    response = update_module.lambda_handler(event, None)

    assert response["statusCode"] == 200
    assert fake_sns.published
    assert fake_sns.published[0]["TopicArn"] == "arn:aws:sns:us-east-1:123456789012:delivery-staff"
    assert "ready" in fake_sns.published[0]["Message"]
