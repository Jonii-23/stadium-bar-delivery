# Architecture Overview

## Core Flow

Customer -> API Gateway -> Lambda -> DynamoDB

This is the primary request path for placing and tracking orders in the stadium bar system.

## Supporting Notifications

The Lambda publishes order events to SNS, which fans out to:

- Bar Staff: receives order arrival and preparation updates
- Delivery Staff: receives notification when an order is ready for handoff

## Components

### Customer
- Orders from their seat using a simple web form
- Sends seat number and purchased items

### API Gateway
- Exposes REST endpoints for create, read, and status update operations
- Routes requests to the correct Lambda function

### Lambda (Python 3.12)
- Handles createOrder, getOrders, and updateOrderStatus logic
- Uses boto3 to interact with DynamoDB and SNS
- Keeps the application serverless and event-driven

### DynamoDB
- Stores all order records in a single Orders table
- Tracks status, seat number, customer information, items, and timestamps

### SNS
- Sends notifications based on order lifecycle changes
- Keeps bar staff and delivery staff decoupled from the main order flow

## Order Lifecycle

pending -> preparing -> ready -> out_for_delivery -> delivered

This lifecycle reflects each stage from placement through final handoff to the customer.
