/**
 * TODO BN-602 - Add a product with one pack size
 * Props: onAdd(product)
 * Fields: name, brand, category (select from CATEGORIES), image (select emoji), variantLabel, price, mrp, stock
 * - errors = validateNewProduct(values); show them only after the first submit attempt
 * - on success build { id: `p${Date.now()}`, ..., tags: ["new"], rating: 4.0, variants: [{ id: `${id}-v1`, ... }] }
 *   with NUMBERS for price/mrp/stock, call onAdd, show a success message and reset the form
 */
function AddProductForm() {
  return <div className="todo"><b>BN-602</b> Add product form</div>;
}

export default AddProductForm;
