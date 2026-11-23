/**
 * TODO BN-401 - Controlled address form (no state of its own)
 * Props: values, errors, touched, onChange(event), onBlur(event), pincodeStatus
 * Fields (name attribute): fullName, phone, house, area, landmark (optional), pincode
 * Show a field's error only when touched[field] is true.
 * Pincode: hint "Checking delivery availability..." / "✓ We deliver to <city>",
 *          error "Sorry, we do not deliver to this pincode yet" when unserviceable.
 * CSS: form-grid (and TextField)
 */
function AddressForm() {
  return <div className="todo"><b>BN-401</b> AddressForm</div>;
}

export default AddressForm;
