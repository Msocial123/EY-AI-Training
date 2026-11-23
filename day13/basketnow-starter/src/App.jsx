import { useState } from "react";
import Header from "./components/layout/Header";
import Footer from "./components/layout/Footer";
import CatalogPage from "./features/catalog/CatalogPage";
import CartDrawer from "./features/cart/CartDrawer";
import CheckoutPage from "./features/checkout/CheckoutPage";
import OrderTrackerPage from "./features/orders/OrderTrackerPage";
import OrdersPage from "./features/orders/OrdersPage";
import InventoryPage from "./features/admin/InventoryPage";

/**
 * App = the single source of truth (see the Project Brief, "State ownership").
 *
 * TODO BN-102  view state + navigate(view): "shop" | "checkout" | "track" | "orders" | "admin"; searchText; isCartOpen
 * TODO BN-201  products, isLoading, loadError, reloadKey; load with fetchProducts() in useEffect (ignore-flag cleanup)
 * TODO BN-301  cart = useLocalStorage("bn-cart", [])  -> [{ variantId, qty }] only. changeQty(variantId, qty):
 *              clamp to 0..getMaxQty(stock); 0 removes; never mutate (map / filter / spread)
 * TODO BN-303  derived every render: lines = buildCartLines(cart, products); cartQtyById; bill = getBill(...)
 * TODO BN-304  couponCode = useLocalStorage("bn-coupon", ""); applyCoupon(code) -> { ok, reason }; offers for the picker
 * TODO BN-403  orders = useLocalStorage("bn-orders", []); savedAddress = useLocalStorage("bn-address", null);
 *              handlePlaceOrder(...) -> await placeOrder(), save order snapshot, reduce stock, clear cart, go to "track"
 * TODO BN-501  cancelOrder(id): set cancelledAt + return stock;  BN-502 reorder(order) -> number of items added
 * TODO BN-601  updateStock, addProduct, deleteProduct (immutable updates of products)
 * TODO BN-102  simulateErrors toggle -> useEffect(() => setSimulateErrors(value), [value]); resetDemo()
 */
function App() {
  const [view, setView] = useState("shop");

  return (
    <div className="app">
      <Header view={view} onNavigate={setView} />

      <main className="main">
        <div className="todo todo-intro">
          <b>Welcome to the BasketNow starter.</b> The data, mock API, business-logic utilities and all CSS are ready.
          Your job is every React component, hook and this App. Start with ticket BN-101 in the Project Brief.
        </div>
        {view === "shop" && <CatalogPage />}
        {view === "checkout" && <CheckoutPage />}
        {view === "track" && <OrderTrackerPage />}
        {view === "orders" && <OrdersPage />}
        {view === "admin" && <InventoryPage />}
      </main>

      <CartDrawer isOpen={false} />
      <Footer />
    </div>
  );
}

export default App;
