import ProductCard from "./ProductCard";

/**
 * TODO BN-202 - Grid of ProductCards (key = product.id)
 * Props: products, cartQtyById, onChangeQty
 * CSS: product-grid
 */
function ProductGrid({ products, cartQtyById, onChangeQty }) {
  return (
    <div className="product-grid">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} cartQtyById={cartQtyById} onChangeQty={onChangeQty} />
      ))}
    </div>
  );
}

/**
 * TODO BN-201 - Loading skeleton: `count` grey placeholder cards
 * CSS: product-card skeleton, sk sk-media, sk sk-line, sk sk-line short, sk sk-btn
 */
export function ProductGridSkeleton() {
  return <div className="todo"><b>BN-201</b> Loading skeleton</div>;
}

export default ProductGrid;
