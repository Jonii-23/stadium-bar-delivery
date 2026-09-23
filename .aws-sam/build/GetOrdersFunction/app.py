import json
import os
from decimal import Decimal

import boto3

TABLE_NAME = os.environ.get("ORDERS_TABLE", "Orders")

table = None


def get_table():
    region_name = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"
    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    return dynamodb.Table(TABLE_NAME)


def decimal_to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def lambda_handler(event, context):
    query_params = event.get("queryStringParameters") or {}
    status_filter = (query_params.get("status") or "").strip()

    db_table = table if table is not None else get_table()

    try:
        if status_filter:
            response = db_table.scan(
                FilterExpression="status = :status",
                ExpressionAttributeValues={":status": status_filter},
            )
        else:
            response = db_table.scan()
    except Exception as exc:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(exc)}),
        }

    items = response.get("Items", [])
    for item in items:
        item["totalPrice"] = decimal_to_float(item.get("totalPrice"))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"items": items}),
    }
