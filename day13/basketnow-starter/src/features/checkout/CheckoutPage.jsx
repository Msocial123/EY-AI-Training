/**
 * TODO BN-401, BN-402, BN-403 - Checkout
 * Props: lines, coupon, couponCode, hasPreviousOrders, savedAddress, onPlaceOrder(payload) (async, throws on failure), onBackToShop
 * Local state: address values, touched, saveAddress, slotId ("express"), paymentId ("upi"),
 *              pincodeStatus { state: "idle"|"checking"|"ok"|"unserviceable"|"error", city, message },
 *              isPlacing, placeError
 * - errors = validateAddress(address) on every render (derived)
 * - bill = getBill({ lines, coupon, hasPreviousOrders, slotFee }) on every render
 * - useEffect on the 6-digit pincode -> checkPincode() with an `ignore` cleanup
 * - COD disabled when grand total > COD_LIMIT (and switch away from it if selected)
 * - submit: preventDefault, mark all fields touched, stop if errors or pincode not "ok",
 *   then isPlacing=true and await onPlaceOrder({ address, saveAddress, slot, paymentId, bill });
 *   on error show the banner and turn the button into "Retry: Place order"
 * - empty cart -> EmptyState with "Browse products"
 * CSS: checkout, checkout-main, checkout-side, panel, sticky, step-no, summary-lines, error-banner, fine-print
 */
function CheckoutPage() {
  return <div className="todo"><b>BN-401 / 402 / 403</b> Checkout page</div>;
}

export default CheckoutPage;
