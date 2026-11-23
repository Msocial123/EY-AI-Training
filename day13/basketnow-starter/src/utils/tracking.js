// Order status is DERIVED from time, never stored: status = f(order.createdAt, now, order.cancelledAt).
import { TRACKING_STEPS, CANCELLABLE_UNTIL } from "../data/config";

export function getTrackingInfo(order, now) {
  if (order.cancelledAt) {
    return { stepIndex: -1, label: "Cancelled", isCancelled: true, isDelivered: false, canCancel: false, secondsToNext: 0 };
  }

  const elapsed = Math.max(0, (now - order.createdAt) / 1000);
  let stepIndex = 0;
  TRACKING_STEPS.forEach((step, i) => {
    if (elapsed >= step.at) stepIndex = i;
  });

  const next = TRACKING_STEPS[stepIndex + 1];
  const cancelLimitIndex = TRACKING_STEPS.findIndex((s) => s.id === CANCELLABLE_UNTIL);

  return {
    stepIndex,
    label: TRACKING_STEPS[stepIndex].label,
    isCancelled: false,
    isDelivered: stepIndex === TRACKING_STEPS.length - 1,
    canCancel: stepIndex < cancelLimitIndex,
    secondsToNext: next ? Math.ceil(next.at - elapsed) : 0,
  };
}
