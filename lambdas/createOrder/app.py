import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import boto3

TABLE_NAME = os.environ.get("ORDERS_TABLE", "Orders")

table = None


def get_region_name():
    return os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"


def get_table():
    dynamodb = boto3.resource("dynamodb", region_name=get_region_name())
    return dynamodb.Table(TABLE_NAME)


def get_sns_client():
    return boto3.client("sns", region_name=get_region_name())


def publish_order_notification(order):
    topic_arn = os.environ.get("BAR_STAFF_TOPIC_ARN")
    if not topic_arn:
        return

    message = {
        "event": "order_created",
        "orderId": order["orderId"],
        "customerName": order["customerName"],
        "seatNumber": order["seatNumber"],
        "status": order["status"],
        "totalPrice": float(order["totalPrice"]),
        "currency": order["currency"],
        "items": to_jsonable(order["items"]),
    }

    get_sns_client().publish(
        TopicArn=topic_arn,
        Subject="New order received",
        Message=json.dumps(message),
    )


def iso_utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_decimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def to_jsonable(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value


def calculate_total(items):
    total = 0.0
    for item in items or []:
        quantity = int(item.get("quantity", 0))
        price = float(item.get("price", 0))
        total += quantity * price
    return round(total, 2)


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON body"}),
        }

    customer_id = body.get("customerId", "guest")
    customer_name = (body.get("customerName") or "").strip()
    seat_number = (body.get("seatNumber") or "").strip()
    items = body.get("items") or []

    if not customer_name or not seat_number or not items:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "customerName, seatNumber and items are required"
            }),
        }

    normalized_items = []
    for item in items:
        name = (item.get("name") or "").strip()
        quantity = int(item.get("quantity", 0))
        price = float(item.get("price", 0))

        if not name or quantity <= 0 or price < 0:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Each item must include a valid name, quantity and price"
                }),
            }

        normalized_items.append({
            "itemId": item.get("itemId") or str(uuid.uuid4()),
            "name": name,
            "quantity": quantity,
            "price": to_decimal(price),
        })

    order_id = str(uuid.uuid4())
    now = iso_utc_now()
    order = {
        "PK": f"ORDER#{order_id}",
        "SK": "METADATA",
        "orderId": order_id,
        "customerId": customer_id,
        "customerName": customer_name,
        "seatNumber": seat_number,
        "status": "pending",
        "items": normalized_items,
        "totalPrice": to_decimal(calculate_total(normalized_items)),
        "currency": body.get("currency", "ZAR"),
        "createdAt": now,
        "updatedAt": now,
        "preparingAt": None,
        "readyAt": None,
        "outForDeliveryAt": None,
        "deliveredAt": None,
        "barStaffId": None,
        "deliveryStaffId": None,
        "notes": body.get("notes"),
    }

    db_table = table if table is not None else get_table()
    db_table.put_item(Item=order)
    publish_order_notification(order)

    return {
        "statusCode": 201,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Order created successfully",
            "order": to_jsonable(order),
        }),
    }
