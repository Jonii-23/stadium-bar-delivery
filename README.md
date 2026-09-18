WTC-4D9FD5JN

# StadiumServe — In-Seat Bar Delivery System

## Problem Statement

At DHL Stadium (and similar large venues), match-day bars experience heavy congestion.
Long queues at the bar mean fans who want food or drinks either miss part of the game
or give up on ordering entirely. There is currently no way for a seated customer to
order from the bar without physically joining the queue.

**StadiumServe** solves this by letting customers order from their seat via a simple
web app. Orders are routed to bar staff for preparation, and once ready, delivery
staff are notified with the order details and seat number so they can hand-deliver
the order — no queueing required.

## System Actors

1. **Customer** — places an order from their seat (seat number + items)
2. **Bar Staff** — receives new orders, prepares them, updates status to "preparing" → "ready"
3. **Delivery Staff** — receives notification once an order is ready, delivers it to the seat, marks it "delivered"

## Order Lifecycle

```
pending → preparing → ready → out_for_delivery → delivered
```

## High-Level Architecture

See `ARCHITECTURE.md` for the full diagram and service breakdown.

- **Frontend:** Static site hosted on S3 + CloudFront (customer order form, bar dashboard, delivery dashboard)
- **API:** Amazon API Gateway (REST)
- **Compute:** AWS Lambda (one function per operation)
- **Data:** Amazon DynamoDB (single `Orders` table)
- **Notifications:** Amazon SNS (bar-staff topic, delivery-staff topic)

## Why AWS Serverless

This project is built serverless-first (API Gateway + Lambda + DynamoDB + SNS)
because order volume is spiky — busy right before kickoff and at half-time, quiet
otherwise. Serverless means no idle infrastructure cost and automatic scaling
during peak demand, which matches the real-world usage pattern of a match-day bar.

## Project Status

🚧 In progress — WeThinkCode_ AWS elective project. Due 25 Sep 2026.

## Repo Structure (planned)

```
/lambdas
  /createOrder
  /getOrders
  /updateOrderStatus
/frontend
  index.html        # customer order page
  bar-dashboard.html
  delivery-dashboard.html
ARCHITECTURE.md
SCHEMA.md
README.md
```