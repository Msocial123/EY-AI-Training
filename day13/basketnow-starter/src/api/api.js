// MOCK BACKEND. Behaves like a real REST API: every call is async, takes time, and can fail.
// Do not import SEED_PRODUCTS directly in components - always go through these functions.
import { SEED_PRODUCTS } from "../data/products";
import { SERVICEABLE_PREFIXES } from "../data/config";

let simulateErrors = false;

/** Developer switch used by the footer "Simulate API errors" toggle. */
export function setSimulateErrors(value) {
  simulateErrors = value;
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function deepCopy(value) {
  return JSON.parse(JSON.stringify(value));
}

/** GET /products -> Product[] (about 900 ms). */
export async function fetchProducts() {
  await wait(900);
  if (simulateErrors) throw new Error("Could not load products (HTTP 503). Please try again.");
  return deepCopy(SEED_PRODUCTS);
}

/** GET /serviceability/:pincode -> { serviceable, city } (about 400 ms). */
export async function checkPincode(pincode) {
  await wait(400);
  if (simulateErrors) throw new Error("Could not verify pincode. Please try again.");
  const city = SERVICEABLE_PREFIXES[pincode.slice(0, 3)];
  return { serviceable: Boolean(city), city: city || null };
}

/**
 * POST /orders -> { orderId, createdAt } (about 1200 ms).
 * The server re-checks stock: `stockById` maps variantId -> units currently available.
 */
export async function placeOrder({ lines, stockById }) {
  await wait(1200);
  if (simulateErrors) throw new Error("Payment gateway timeout (HTTP 504). You have not been charged.");
  const unavailable = lines.find((line) => line.qty > (stockById[line.variantId] ?? 0));
  if (unavailable) {
    throw new Error(`Only ${stockById[unavailable.variantId] ?? 0} unit(s) of ${unavailable.name} left. Please update your cart.`);
  }
  const orderId = "BN" + Date.now().toString().slice(-8);
  return { orderId, createdAt: Date.now() };
}
