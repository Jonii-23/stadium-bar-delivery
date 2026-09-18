# DynamoDB Schema

## Table: `Orders`

A single-table design keeps the project simple and works well for a stadium bar ordering flow.

### Primary Key

- `PK`: `ORDER#<orderId>`
- `SK`: `METADATA`

This gives each order a unique identifier and keeps the record in a single row.

### Example Item

```json
{
  "PK": "ORDER#d93d0b2d-1848-4f69-a392-0e4c4b4d2f1f",
  "SK": "METADATA",
  "orderId": "d93d0b2d-1848-4f69-a392-0e4c4b4d2f1f",
  "customerId": "cust-12345",
  "customerName": "Sipho M.",
  "seatNumber": "A12",
  "status": "pending",
  "items": [
    {
      "itemId": "beer-001",
      "name": "Castle Lager",
      "quantity": 2,
      "price": 45.00
    },
    {
      "itemId": "burger-004",
      "name": "Chicken Burger",
      "quantity": 1,
      "price": 85.00
    }
  ],
  "totalPrice": 175.00,
  "currency": "ZAR",
  "createdAt": "2026-09-18T18:30:00Z",
  "updatedAt": "2026-09-18T18:31:00Z",
  "preparingAt": null,
  "readyAt": null,
  "outForDeliveryAt": null,
  "deliveredAt": null,
  "barStaffId": null,
  "deliveryStaffId": null,
  "notes": "Extra napkins please"
}
```

## Status Values

The expected lifecycle is:

- `pending`
- `preparing`
- `ready`
- `out_for_delivery`
- `delivered`

## Recommended Global Secondary Indexes (GSIs)

### 1. Status Index

Purpose: fetch all orders by current status for dashboards and staff views.

- `GSI1PK`: `STATUS#<status>`
- `GSI1SK`: `<createdAt>`

Example:

```json
{
  "GSI1PK": "STATUS#ready",
  "GSI1SK": "2026-09-18T18:45:00Z",
  "PK": "ORDER#d93d0b2d-1848-4f69-a392-0e4c4b4d2f1f",
  "status": "ready"
}
```

### 2. Seat Number Index

Purpose: quickly look up orders for a specific seat.

- `GSI2PK`: `SEAT#<seatNumber>`
- `GSI2SK`: `<createdAt>`

Example:

```json
{
  "GSI2PK": "SEAT#A12",
  "GSI2SK": "2026-09-18T18:30:00Z",
  "PK": "ORDER#d93d0b2d-1848-4f69-a392-0e4c4b4d2f1f",
  "seatNumber": "A12"
}
```

## Notes

- Use `createdAt` and `updatedAt` as ISO-8601 UTC timestamps.
- Keep the schema simple for a first version; do not over-normalize.
- `items` can be stored as a list of nested objects to keep the first implementation easy for Lambda code and UI rendering.
- If the app grows, this table can be extended with a customer profile table or a separate order-events table without breaking the core flow.

## Lambda Usage

- `createOrder`: creates a new order item with default `status = pending`
- `getOrders`: reads all orders or filters by status via the status GSI
- `updateOrderStatus`: updates the `status` field and timestamps as the order moves through the lifecycle
