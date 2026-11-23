/**
 * TODO BN-601, BN-603 - Inventory manager
 * Props: products, isLoading, onUpdateStock(variantId, stock), onAddProduct(product), onDeleteProduct(productId)
 * Local state: filter text, lowOnly, toDelete (product waiting for confirmation)
 * - KPIs: products, pack sizes (SKUs), low stock, out of stock, stock value (sum of price × stock)
 * - table: one row per VARIANT (key = variant.id) with product, pack, price, discount %, editable stock (0-999), status badge, Delete
 * - "Low / out of stock only" filter uses LOW_STOCK_LIMIT
 * - Delete opens a Modal; confirm -> onDeleteProduct(id)
 * - render <AddProductForm onAdd={onAddProduct} /> below the table
 * CSS: kpis, kpi, warn, bad, table-wrap, table, row-out, stock-input, input
 */
function InventoryPage() {
  return <div className="todo"><b>BN-601 / 603</b> Inventory</div>;
}

export default InventoryPage;
