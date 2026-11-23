/**
 * TODO BN-102 - Header (no state of its own)
 * Props: view, onNavigate(view), searchText, onSearchChange(text), cartCount, cartTotal, onCartClick, activeOrders
 * Must show: logo (click -> "shop"), delivery promise, search input (controlled),
 * cart button ("My Cart" when empty, otherwise "N items" + total), tabs Shop / My Orders / Inventory.
 * The "checkout" view highlights the Shop tab; the "track" view highlights My Orders.
 * CSS: header, header-row, logo, promise, search, cart-btn, has-items, tabs, tab, active, tab-dot
 */
function Header() {
  return (
    <header className="header">
      <div className="header-row">
        <span className="logo">basket<span>now</span></span>
        <div className="todo"><b>BN-102</b> Header: search, cart button, tabs</div>
      </div>
    </header>
  );
}

export default Header;
