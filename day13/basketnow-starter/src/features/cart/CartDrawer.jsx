/**
 * TODO BN-302 - Slide-in cart panel
 * Props: isOpen, onClose, lines, bill, offers, couponCode, onApplyCoupon(code) -> { ok, reason },
 *        onRemoveCoupon, onChangeQty, onClearCart, onCheckout
 * - return null when closed; backdrop click and Escape close it (useEffect + cleanup)
 * - empty cart -> EmptyState with "Start shopping"
 * - otherwise: FreeDeliveryProgress, item count + "Clear cart", CartLine list (key = variantId),
 *   CouponPicker, warning when the applied coupon is no longer valid, BillDetails,
 *   footer with grand total and "Proceed to checkout"
 * CSS: overlay drawer-overlay, drawer, drawer-head, drawer-body, drawer-section, section-head,
 *      cart-lines, drawer-foot, warning-box
 */
function CartDrawer({ isOpen }) {
  if (!isOpen) return null;
  return null; // TODO
}

export default CartDrawer;
