import json
import os
from datetime import datetime, timezone

import boto3

TABLE_NAME = os.environ.get("ORDERS_TABLE", "Orders")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

VALID_STATUSES = [
    "pending",
    "preparing",
    "ready",
    "out_for_delivery",
    "delivered",
]

TRANSITIONS = {
    "pending": ["preparing"],
    "preparing": ["ready"],
    "ready": ["out_for_delivery"],
    "out_for_delivery": ["delivered"],
    "delivered": [],
}


def iso_utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid JSON body"}),
        }

    order_id = body.get("orderId") or (event.get("pathParameters") or {}).get("orderId")
    new_status = (body.get("status") or "").strip()

    if not order_id or not new_status:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "orderId and status are required"
            }),
        }

    if new_status not in VALID_STATUSES:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": f"Invalid status. Allowed values: {VALID_STATUSES}"
            }),
        }

    current_item = table.get_item(
        Key={"PK": f"ORDER#{order_id}", "SK": "METADATA"}
    )
    current_record = current_item.get("Item")

    if not current_record:
        return {
            "statusCode": 404,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Order not found"}),
        }

    current_status = current_record.get("status", "pending")
    allowed_next = TRANSITIONS.get(current_status, [])

    if new_status not in allowed_next:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": f"Invalid transition from {current_status} to {new_status}"
            }),
        }

    now = iso_utc_now()
    timestamp_fields = {
        "preparing": "preparingAt",
        "ready": "readyAt",
        "out_for_delivery": "outForDeliveryAt",
        "delivered": "deliveredAt",
    }

    update_expression = "SET #status = :status, updatedAt = :updatedAt"
    expression_attribute_values = {
        ":status": new_status,
        ":updatedAt": now,
    }
    expression_attribute_names = {"#status": "status"}

    if new_status in timestamp_fields:
        field_name = timestamp_fields[new_status]
        update_expression += f", {field_name} = :{field_name}"
        expression_attribute_values[f":{field_name}"] = now

    updated = table.update_item(
        Key={"PK": f"ORDER#{order_id}", "SK": "METADATA"},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": "Order status updated successfully",
            "order": updated.get("Attributes")
        }),
    }
