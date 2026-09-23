const API_BASE_URL = "https://<YOUR-API-ID>.execute-api.us-east-1.amazonaws.com/Prod";

const MENU = [
  { name: "Castle Lite", price: 45 },
  { name: "Coke 330ml", price: 25 },
  { name: "Chips", price: 35 },
  { name: "Boerewors Roll", price: 55 },
  { name: "Water 500ml", price: 20 },
];

const quantities = Object.fromEntries(MENU.map((item) => [item.name, 0]));

const menuListEl = document.getElementById("menuList");
const totalPriceEl = document.getElementById("totalPrice");
const submitBtn = document.getElementById("submitBtn");
const statusMsgEl = document.getElementById("statusMsg");

function renderMenu() {
  menuListEl.innerHTML = "";

  MENU.forEach((item) => {
    const row = document.createElement("div");
    row.className = "item-row";
    row.innerHTML = `
      <div class="item-info">
        <span class="item-name">${item.name}</span>
        <span class="item-price">R${item.price.toFixed(2)}</span>
      </div>
      <div class="qty-control">
        <button class="qty-btn" data-name="${item.name}" data-action="dec" type="button">−</button>
        <span class="qty-value" id="qty-${item.name}">${quantities[item.name]}</span>
        <button class="qty-btn" data-name="${item.name}" data-action="inc" type="button">+</button>
      </div>
    `;
    menuListEl.appendChild(row);
  });
}

function updateTotal() {
  const total = MENU.reduce((sum, item) => sum + item.price * quantities[item.name], 0);
  totalPriceEl.textContent = `R${total.toFixed(2)}`;
}

menuListEl.addEventListener("click", (event) => {
  const button = event.target.closest(".qty-btn");
  if (!button) return;

  const { name, action } = button.dataset;
  if (action === "inc") quantities[name] += 1;
  if (action === "dec") quantities[name] = Math.max(0, quantities[name] - 1);

  const qtyEl = document.getElementById(`qty-${name}`);
  if (qtyEl) qtyEl.textContent = quantities[name];

  updateTotal();
});

function showStatus(message, type) {
  statusMsgEl.textContent = message;
  statusMsgEl.className = `status-msg ${type}`;
}

submitBtn.addEventListener("click", async () => {
  const seatNumber = document.getElementById("seatNumber").value.trim();
  const customerName = document.getElementById("customerName").value.trim();
  const customerContact = document.getElementById("customerContact").value.trim();
  const notes = document.getElementById("notes").value.trim();

  const selectedItems = MENU.filter((item) => quantities[item.name] > 0).map((item) => ({
    name: item.name,
    quantity: quantities[item.name],
    price: item.price,
  }));

  if (!seatNumber) {
    showStatus("Please enter your seat number.", "error");
    return;
  }

  if (!customerName) {
    showStatus("Please enter your name.", "error");
    return;
  }

  if (selectedItems.length === 0) {
    showStatus("Please select at least one item.", "error");
    return;
  }

  const order = {
    customerId: `guest-${Date.now()}`,
    customerName,
    seatNumber,
    currency: "ZAR",
    items: selectedItems,
    notes: notes || undefined,
    customerContact: customerContact || undefined,
  };

  submitBtn.disabled = true;
  submitBtn.textContent = "Placing order...";
  statusMsgEl.className = "status-msg";

  try {
    if (API_BASE_URL.includes("<YOUR-API-ID>")) {
      throw new Error("Set API_BASE_URL to your deployed API Gateway URL.");
    }

    const response = await fetch(`${API_BASE_URL}/orders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(order),
    });

    const result = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(result.error || `Server responded with ${response.status}`);
    }

    showStatus(`Order placed successfully. Order ID: ${result.order?.orderId || "pending"}`, "success");

    MENU.forEach((item) => {
      quantities[item.name] = 0;
    });

    renderMenu();
    updateTotal();
    document.getElementById("notes").value = "";
    document.getElementById("customerContact").value = "";
  } catch (error) {
    showStatus(`Couldn't place order: ${error.message}.`, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Place Order";
  }
});

renderMenu();
updateTotal();
