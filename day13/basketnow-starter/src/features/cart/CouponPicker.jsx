/**
 * TODO BN-304 - Coupon input + list of offers
 * Props: offers [{ coupon, result: { ok, discount, reason } }], appliedCode, onApply(code) -> { ok, reason }, onRemove
 * Local state: typed code, error message
 * - form submit (preventDefault): call onApply(code.trim().toUpperCase()); show result.reason on failure
 * - each offer shows code, title, and either "You save ₹N" or the reason it is unavailable
 * - Apply disabled when !result.ok; the applied coupon shows "Remove" instead
 * CSS: coupons, coupon-form, coupon-list, coupon, unavailable, ok-text, muted, field-error
 */
function CouponPicker() {
  return null;
}

export default CouponPicker;
