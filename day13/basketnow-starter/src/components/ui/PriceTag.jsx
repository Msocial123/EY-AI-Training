import { formatPrice } from "../../utils/format";

/**
 * TODO BN-701 - PriceTag
 * Props: price (number), mrp (number), size "sm" | "md"
 * Show the selling price; show the MRP struck through ONLY when mrp > price.
 * CSS: price-tag, price-<size>, price-now, price-mrp
 */
function PriceTag({ price }) {
  return <span className="price-tag"><span className="price-now">{formatPrice(price)}</span></span>;
}

export default PriceTag;
