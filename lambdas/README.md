# Lambda Functions

This folder contains the first-pass Python Lambda functions for the StadiumServe serverless architecture.

## Functions

### createOrder
- Creates a new order in DynamoDB
- Validates required fields
- Stores order details, items, and status

### getOrders
- Lists orders from DynamoDB
- Supports optional `?status=ready` filtering

### updateOrderStatus
- Validates the order lifecycle transitions
- Updates status and timestamp fields
- Prevents invalid transitions such as `pending -> delivered`

## Suggested AWS Setup

- API Gateway routes:
  - `POST /orders` -> `createOrder`
  - `GET /orders` -> `getOrders`
  - `PATCH /orders/{orderId}/status` -> `updateOrderStatus`
- DynamoDB table: `Orders`
- Optional SNS topics:
  - bar-staff topic
  - delivery-staff topic

## Example payloads

### Create order

```json
{
  "customerId": "cust-123",
  "customerName": "Sipho M.",
  "seatNumber": "A12",
  "currency": "ZAR",
  "items": [
    {"name": "Castle Lager", "quantity": 2, "price": 45.00},
    {"name": "Chicken Burger", "quantity": 1, "price": 85.00}
  ],
  "notes": "Extra napkins please"
}
```

### Update status

```json
{
  "orderId": "d93d0b2d-1848-4f69-a392-0e4c4b4d2f1f",
  "status": "ready"
}
```
