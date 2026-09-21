import json
import os
import uuid
from datetime import datetime, timezone

import boto3

TABLE_NAME = os.environ.get("ORDERS_TABLE", "Orders")

table = None


def get_table():
    region_name = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"
    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    return dynamodb.Table(TABLE_NAME)


def iso_utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
            "price": price,
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
        "totalPrice": calculate_total(normalized_items),
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

    return {
        "statusCode": 201,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Order created successfully",
            "order": order,
        }),
    }
