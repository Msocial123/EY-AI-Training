// Business rules in ONE place. Product owners change these numbers; components never hard-code them.

export const FREE_DELIVERY_THRESHOLD = 199; // item total at or above this -> free delivery
export const DELIVERY_FEE = 30;
export const HANDLING_FEE = 5;
export const MAX_QTY_PER_ITEM = 6;          // per variant, also limited by stock
export const LOW_STOCK_LIMIT = 5;           // "Only N left" badge and the admin low-stock filter
export const COD_LIMIT = 2000;              // Cash on Delivery not allowed above this grand total

// Serviceable delivery areas: pincode prefixes (first 3 digits)
export const SERVICEABLE_PREFIXES = {
  "500": "Hyderabad",
  "516": "Kadapa",
  "524": "Nellore",
  "530": "Visakhapatnam",
};

export const DELIVERY_SLOTS = [
  { id: "express", label: "Express", detail: "Delivery in 15 minutes", fee: 15 },
  { id: "evening", label: "Today, 6 - 8 PM", detail: "Standard slot", fee: 0 },
  { id: "tomorrow", label: "Tomorrow, 7 - 9 AM", detail: "Morning slot", fee: 0 },
];

export const PAYMENT_METHODS = [
  { id: "upi", label: "UPI", detail: "Pay using any UPI app" },
  { id: "card", label: "Credit / Debit card", detail: "Visa, Mastercard, RuPay" },
  { id: "cod", label: "Cash on Delivery", detail: `Available for orders up to ₹${COD_LIMIT}` },
];

// Order tracking timeline. Real deliveries take minutes; the demo compresses them into seconds.
// `at` = seconds after the order was placed when this status starts.
export const TRACKING_STEPS = [
  { id: "confirmed", label: "Order confirmed", at: 0 },
  { id: "packed", label: "Packed", at: 8 },
  { id: "out", label: "Out for delivery", at: 16 },
  { id: "delivered", label: "Delivered", at: 30 },
];
export const CANCELLABLE_UNTIL = "out"; // cannot cancel once this status is reached
