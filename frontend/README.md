# Frontend

This directory contains the customer order interface for StadiumServe.

## Files

- `index.html` — page structure
- `styles.css` — styling for the form and menu
- `app.js` — quantity handling and API submission logic

## Configure the API URL

Update the `API_BASE_URL` value in `app.js` before deployment:

```js
const API_BASE_URL = "REPLACE_WITH_API_GATEWAY_URL";
```

Once deployed, the page submits orders to:

```text
POST /orders
```

The frontend expects the backend to accept an order payload shaped like the project schema in `SCHEMA.md`.
