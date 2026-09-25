import json
import os
from datetime import datetime, timezone

import boto3

TABLE_NAME = os.environ.get("ORDERS_TABLE", "Orders")
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Content-Type": "application/json",
}

table = None


def build_response(status_code, payload, extra_headers=None):
    headers = CORS_HEADERS.copy()
    if extra_headers:
        headers.update(extra_headers)
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(payload),
    }


def get_region_name():
    return os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"


def get_table():
    dynamodb = boto3.resource("dynamodb", region_name=get_region_name())
    return dynamodb.Table(TABLE_NAME)


def get_sns_client():
    return boto3.client("sns", region_name=get_region_name())


def publish_status_notification(order, new_status):
    topic_arn = os.environ.get("DELIVERY_STAFF_TOPIC_ARN") if new_status == "ready" else None
    if not topic_arn:
        return

    message = {
        "event": "order_status_updated",
        "orderId": order.get("orderId"),
        "status": new_status,
        "seatNumber": order.get("seatNumber"),
        "customerName": order.get("customerName"),
        "totalPrice": order.get("totalPrice"),
        "currency": order.get("currency"),
    }

    get_sns_client().publish(
        TopicArn=topic_arn,
        Subject=f"Order status changed to {new_status}",
        Message=json.dumps(message),
    )


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
        return build_response(400, {"error": "Invalid JSON body"})

    order_id = body.get("orderId") or (event.get("pathParameters") or {}).get("orderId")
    new_status = (body.get("status") or "").strip()

    if not order_id or not new_status:
        return build_response(400, {
            "error": "orderId and status are required"
        })

    if new_status not in VALID_STATUSES:
        return build_response(400, {
            "error": f"Invalid status. Allowed values: {VALID_STATUSES}"
        })

    db_table = table if table is not None else get_table()

    current_item = db_table.get_item(
        Key={"PK": f"ORDER#{order_id}", "SK": "METADATA"}
    )
    current_record = current_item.get("Item")

    if not current_record:
        return build_response(404, {"error": "Order not found"})

    current_status = current_record.get("status", "pending")
    allowed_next = TRANSITIONS.get(current_status, [])

    if new_status not in allowed_next:
        return build_response(400, {
            "error": f"Invalid transition from {current_status} to {new_status}"
        })

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

    updated = db_table.update_item(
        Key={"PK": f"ORDER#{order_id}", "SK": "METADATA"},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
    )

    updated_order = updated.get("Attributes") or {}
    if new_status == "ready":
        publish_status_notification(updated_order, new_status)

    return build_response(200, {
        "message": "Order status updated successfully",
        "order": updated_order,
    })
