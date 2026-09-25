import json
import os
from decimal import Decimal

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


def get_table():
    region_name = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"
    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    return dynamodb.Table(TABLE_NAME)


def decimal_to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, list):
        return [decimal_to_float(item) for item in value]
    if isinstance(value, dict):
        return {key: decimal_to_float(item) for key, item in value.items()}
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
        return build_response(500, {"error": str(exc)})

    items = response.get("Items", [])
    normalized_items = [decimal_to_float(item) for item in items]

    return build_response(200, {"items": normalized_items})
