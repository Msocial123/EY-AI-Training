// Presentation helpers (pure functions, no React).

/** 1499 -> "₹1,499" */
export function formatPrice(amount) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

/** (75, 100) -> 25. Returns 0 when there is no real discount. */
export function discountPercent(price, mrp) {
  if (!mrp || mrp <= price) return 0;
  return Math.round(((mrp - price) / mrp) * 100);
}

/** Timestamp -> "23 Nov, 7:42 pm" */
export function formatDateTime(timestamp) {
  return new Date(timestamp).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
  });
}

/** 1 -> "1 item", 3 -> "3 items" */
export function pluralize(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}
