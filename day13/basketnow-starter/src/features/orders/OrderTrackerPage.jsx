/**
 * TODO BN-501 - Live order tracking
 * Props: order, onCancel(orderId), onBackToShop, onViewOrders
 * - const now = useNow(1000); const info = getTrackingInfo(order, now)  (status is DERIVED, never stored)
 * - hero: current status, order id, placed time, "next update in Ns"
 * - timeline of TRACKING_STEPS with done / current classes
 * - items + total, delivery address + slot
 * - "Cancel order" only while info.canCancel -> confirm in a Modal -> onCancel(order.id)
 * CSS: tracker, tracker-hero, delivered, cancelled, tracker-emoji, timeline, done, current, dot, tracker-grid, panel
 */
function OrderTrackerPage() {
  return <div className="todo"><b>BN-501</b> Order tracking</div>;
}

export default OrderTrackerPage;
