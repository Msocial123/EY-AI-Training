/**
 * TODO BN-202 - Product tile
 * Props: product, cartQtyById { [variantId]: qty }, onChangeQty(variantId, qty)
 * Local state: selected variant id (default: first variant that is in stock)
 * Must show: emoji image, "N% OFF" ribbon when discounted, tag badges (Bestseller/Organic/New),
 * "Only N left" when stock <= LOW_STOCK_LIMIT, name, brand + rating, pack-size pills (or the single label),
 * PriceTag, and the action:
 *   out of stock -> disabled "Out of stock" button
 *   qty 0        -> "ADD" button (adds 1)
 *   qty > 0      -> QuantityStepper with max = getMaxQty(variant.stock)
 * CSS: product-card, is-out, product-media, product-emoji, off-ribbon, product-tags, product-name,
 *      product-brand, variant-pills, pill, active, pill-out, variant-single, product-foot
 */
function ProductCard({ product }) {
  return <div className="product-card"><div className="todo"><b>BN-202</b> {product.name}</div></div>;
}

export default ProductCard;
