// Coupon catalogue. Eligibility is checked by validateCoupon() in src/utils/pricing.js.
//   type "flat"    -> fixed rupee discount
//   type "percent" -> percentage discount, capped at maxDiscount
//   minOrder       -> minimum eligible item total
//   firstOrderOnly -> only when the customer has no previous non-cancelled orders
//   category       -> discount applies only to items of this category

export const COUPONS = [
  {
    code: "WELCOME50",
    title: "Flat ₹50 off on your first order",
    type: "flat", value: 50, minOrder: 199, firstOrderOnly: true,
  },
  {
    code: "SAVE10",
    title: "10% off up to ₹75",
    type: "percent", value: 10, maxDiscount: 75, minOrder: 299,
  },
  {
    code: "FRESH20",
    title: "20% off on Fruits & Vegetables, up to ₹60",
    type: "percent", value: 20, maxDiscount: 60, minOrder: 0, category: "Fruits & Vegetables",
  },
];
