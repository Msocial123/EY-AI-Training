// Cart and bill calculations. Pure functions: same input -> same output, no React, easy to test.
// Components call these during render ("derived state"); totals are NEVER stored in state.
import {
  FREE_DELIVERY_THRESHOLD,
  DELIVERY_FEE,
  HANDLING_FEE,
  MAX_QTY_PER_ITEM,
} from "../data/config";

/** Highest quantity a customer may hold for one variant. */
export function getMaxQty(stock) {
  return Math.max(0, Math.min(stock, MAX_QTY_PER_ITEM));
}

/** Map of variantId -> { product, variant } for fast lookups. */
export function indexVariants(products) {
  const index = {};
  for (const product of products) {
    for (const variant of product.variants) {
      index[variant.id] = { product, variant };
    }
  }
  return index;
}

/**
 * Joins the minimal cart [{ variantId, qty }] with live catalogue data.
 * Lines whose product was deleted are dropped; qty is clamped to current stock.
 */
export function buildCartLines(cart, products) {
  const index = indexVariants(products);
  return cart
    .filter((item) => index[item.variantId])
    .map((item) => {
      const { product, variant } = index[item.variantId];
      const maxQty = getMaxQty(variant.stock);
      return {
        variantId: variant.id,
        productId: product.id,
        name: product.name,
        brand: product.brand,
        image: product.image,
        category: product.category,
        variantLabel: variant.label,
        price: variant.price,
        mrp: variant.mrp,
        stock: variant.stock,
        maxQty,
        qty: Math.min(item.qty, maxQty),
      };
    })
    .filter((line) => line.qty > 0);
}

/**
 * Checks one coupon against the current cart.
 * Returns { ok: true, discount } or { ok: false, discount: 0, reason }.
 */
export function validateCoupon(coupon, { lines, itemTotal, hasPreviousOrders }) {
  if (!coupon) return { ok: false, discount: 0, reason: "Coupon not found" };

  if (coupon.firstOrderOnly && hasPreviousOrders) {
    return { ok: false, discount: 0, reason: "Valid on your first order only" };
  }
  if (itemTotal < coupon.minOrder) {
    return { ok: false, discount: 0, reason: `Add items worth ₹${coupon.minOrder - itemTotal} more to use this` };
  }

  const eligibleTotal = coupon.category
    ? lines.filter((l) => l.category === coupon.category).reduce((sum, l) => sum + l.price * l.qty, 0)
    : itemTotal;

  if (eligibleTotal === 0) {
    return { ok: false, discount: 0, reason: `Add ${coupon.category} items to use this` };
  }

  let discount = coupon.type === "flat" ? coupon.value : Math.round((eligibleTotal * coupon.value) / 100);
  if (coupon.maxDiscount) discount = Math.min(discount, coupon.maxDiscount);
  discount = Math.min(discount, eligibleTotal); // never discount more than the eligible amount

  return { ok: true, discount };
}

/** Full bill for the cart drawer and the checkout page. */
export function getBill({ lines, coupon = null, hasPreviousOrders = false, slotFee = 0 }) {
  const itemCount = lines.reduce((sum, l) => sum + l.qty, 0);
  const itemTotal = lines.reduce((sum, l) => sum + l.price * l.qty, 0);
  const mrpTotal = lines.reduce((sum, l) => sum + l.mrp * l.qty, 0);

  const couponResult = coupon ? validateCoupon(coupon, { lines, itemTotal, hasPreviousOrders }) : null;
  const couponDiscount = couponResult?.ok ? couponResult.discount : 0;

  const deliveryFee = itemCount === 0 || itemTotal >= FREE_DELIVERY_THRESHOLD ? 0 : DELIVERY_FEE;
  const handlingFee = itemCount === 0 ? 0 : HANDLING_FEE;
  const grandTotal = itemTotal - couponDiscount + deliveryFee + handlingFee + (itemCount ? slotFee : 0);

  return {
    itemCount,
    itemTotal,
    mrpTotal,
    productSavings: mrpTotal - itemTotal,
    couponResult,
    couponDiscount,
    deliveryFee,
    handlingFee,
    slotFee: itemCount ? slotFee : 0,
    grandTotal,
    amountForFreeDelivery: Math.max(0, FREE_DELIVERY_THRESHOLD - itemTotal),
    totalSavings: mrpTotal - itemTotal + couponDiscount + (itemCount && deliveryFee === 0 ? DELIVERY_FEE : 0),
  };
}
