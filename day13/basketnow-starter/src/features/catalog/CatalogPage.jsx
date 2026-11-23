/**
 * TODO BN-201, BN-203, BN-204, BN-205 - Storefront page
 * Props: products, isLoading, error, onRetry, searchText, onClearSearch, cartQtyById, onChangeQty(variantId, qty)
 * Local state: category ("All"), sortBy ("relevance"), inStockOnly (false)
 * - isLoading -> <ProductGridSkeleton />, error -> EmptyState with "Try again" (onRetry)
 * - debounce the search text with useDebounce(searchText.trim().toLowerCase(), 300)
 * - search matches name, brand or category; in-stock = any variant with stock > 0
 * - category chips are built from CATEGORIES with live counts (counts follow search + in-stock filters)
 * - sort options: relevance, priceLow, priceHigh, discount, rating (use the cheapest variant for price)
 * - no results -> EmptyState with a "Reset filters" button
 * - all hooks must be called BEFORE any early return
 */
function CatalogPage() {
  return <div className="todo"><b>BN-201 / 203 / 204 / 205</b> Catalogue page</div>;
}

export default CatalogPage;
