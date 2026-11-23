/**
 * TODO BN-701 - QuantityStepper (CONTROLLED component - no useState inside)
 * Props: value, min (default 0), max, onChange(newValue), label (for aria-labels)
 * - "−" button calls onChange(value - 1), disabled when value <= min
 * - "+" button calls onChange(value + 1), disabled when value >= max
 * - aria-label="Decrease <label>" / "Increase <label>"
 * CSS: stepper
 */
function QuantityStepper({ value }) {
  return <div className="stepper"><span>{value}</span></div>;
}

export default QuantityStepper;
