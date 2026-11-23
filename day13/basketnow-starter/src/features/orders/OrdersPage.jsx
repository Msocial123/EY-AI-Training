/**
 * TODO BN-502 - Order history (newest first)
 * Props: orders, onTrack(orderId), onReorder(order) -> number of items added, onBackToShop
 * - live status badge per order (useNow + getTrackingInfo): yellow in progress, green delivered, red cancelled
 * - "Track" for active orders, "Reorder" for delivered/cancelled ones, "Details" for all
 * - after reorder show "N items added to your cart." or "Sorry, none of these items are in stock right now."
 * - no orders -> EmptyState
 * CSS: orders, order-card, order-emojis, order-info, order-actions, info-box
 */
function OrdersPage() {
  return <div className="todo"><b>BN-502</b> My Orders</div>;
}

export default OrdersPage;
