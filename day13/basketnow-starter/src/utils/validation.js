// Form validation rules for the checkout address form and the admin "Add product" form.
// Each function returns an errors object: { fieldName: "message" }. Empty object = valid.

export function validateAddress(values) {
  const errors = {};
  const name = values.fullName.trim();
  if (name.length < 3) errors.fullName = "Enter your full name (at least 3 letters)";

  if (!/^[6-9]\d{9}$/.test(values.phone.trim())) {
    errors.phone = "Enter a valid 10-digit mobile number starting with 6-9";
  }
  if (!values.house.trim()) errors.house = "House / flat number is required";
  if (!values.area.trim()) errors.area = "Area / street is required";
  if (!/^\d{6}$/.test(values.pincode.trim())) errors.pincode = "Enter a valid 6-digit pincode";

  return errors;
}

export function validateNewProduct(values) {
  const errors = {};
  const price = Number(values.price);
  const mrp = Number(values.mrp);
  const stock = Number(values.stock);

  if (values.name.trim().length < 3) errors.name = "Name must have at least 3 characters";
  if (!values.brand.trim()) errors.brand = "Brand is required";
  if (!values.variantLabel.trim()) errors.variantLabel = "Pack size is required, e.g. 500 g";
  if (!(price > 0)) errors.price = "Price must be greater than 0";
  if (!(mrp > 0)) errors.mrp = "MRP must be greater than 0";
  else if (mrp < price) errors.mrp = "MRP cannot be lower than the selling price";
  if (!Number.isInteger(stock) || stock < 0 || values.stock === "") errors.stock = "Stock must be a whole number, 0 or more";

  return errors;
}
