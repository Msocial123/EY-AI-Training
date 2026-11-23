# BasketNow: Quick-Commerce Web App (Starter)

BasketNow delivers groceries in 15 minutes in Hyderabad, Kadapa, Nellore and Visakhapatnam.
You are building its customer web app and the store manager's inventory screen with **React 19 + Vite only**:
no router, no UI library, no state library. Everything uses React fundamentals: JSX, components, props,
`useState`, events, conditional rendering, lists and keys, `useEffect`, `useRef`, custom hooks, lifting state up
and reusable components.

The full requirements, tickets, acceptance criteria, test cases and evaluation rubric are in the
**BasketNow Project Brief (PDF)**. Read it before writing code.

## Run it

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # must pass before every pull request
```

Node.js 20.19+ or 22.12+ is required.

## What is provided vs. what you build

| Provided (do not change without a reason) | You build |
|---|---|
| `src/data/` catalogue, coupons and business rules (`config.js`) | Every component in `src/components/` and `src/features/` |
| `src/api/api.js` mock backend with latency and failures | The three hooks in `src/hooks/` |
| `src/utils/` pricing, validation, tracking and format helpers | `src/App.jsx` (all shared state and actions) |
| `src/styles.css` complete design system (class names listed in each stub) | |

Every stub file starts with a comment: the ticket ID, the props it receives, the behaviour required and the CSS
classes to use. Yellow dashed boxes on screen show what is still to do; delete the `.todo` styles when you finish.

## Tickets → files

| Ticket | Title | Files |
|---|---|---|
| BN-101 | Project setup and repository | whole repo |
| BN-102 | App shell: header, tabs, footer, navigation | `components/layout/*`, `App.jsx` |
| BN-701 | Design-system components | `components/ui/*` |
| BN-201 | Load catalogue: skeleton, error, retry | `App.jsx`, `CatalogPage.jsx`, `ProductGrid.jsx` |
| BN-202 | Product card with pack sizes and stepper | `ProductCard.jsx`, `ProductGrid.jsx` |
| BN-203 | Category chips with live counts | `CategoryBar.jsx`, `CatalogPage.jsx` |
| BN-204 | Debounced search and empty state | `useDebounce.js`, `CatalogPage.jsx`, `Header.jsx` |
| BN-205 | Sort and in-stock filter | `CatalogToolbar.jsx`, `CatalogPage.jsx` |
| BN-301 | Cart state and persistence | `useLocalStorage.js`, `App.jsx` |
| BN-302 | Cart drawer | `CartDrawer.jsx`, `CartLine.jsx` |
| BN-303 | Bill details and free-delivery progress | `BillDetails.jsx`, `FreeDeliveryProgress.jsx` |
| BN-304 | Coupons | `CouponPicker.jsx`, `App.jsx` |
| BN-401 | Address form, validation, serviceability | `AddressForm.jsx`, `CheckoutPage.jsx` |
| BN-402 | Delivery slot and payment selection | `OptionCards.jsx`, `CheckoutPage.jsx` |
| BN-403 | Place order: loading, failure, retry, success | `CheckoutPage.jsx`, `App.jsx` |
| BN-501 | Live order tracking and cancellation | `useNow.js`, `OrderTrackerPage.jsx`, `App.jsx` |
| BN-502 | Order history and reorder | `OrdersPage.jsx`, `App.jsx` |
| BN-601 | Inventory table, KPIs, stock editing | `InventoryPage.jsx`, `App.jsx` |
| BN-602 | Add product | `AddProductForm.jsx` |
| BN-603 | Delete product with confirmation | `InventoryPage.jsx` |

## Git workflow

```bash
git checkout -b feature/BN-202-product-card
# ...work...
git add .
git commit -m "BN-202: product card with pack sizes and quantity stepper"
git push -u origin feature/BN-202-product-card
# open a pull request into main; another team member reviews it
```

## Developer tools in the footer

- **Simulate API errors**: every API call fails. Use it to test loading, error and retry states.
- **Reset demo data**: clears the saved cart, coupon, orders and address, and reloads the catalogue.
