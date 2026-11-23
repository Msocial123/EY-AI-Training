// Seed catalogue returned by the mock API (src/api/api.js).
// A product can have several pack sizes ("variants"). Price, MRP and stock belong to the VARIANT.
// Every product id and every variant id is globally unique: use them as React keys.

export const CATEGORIES = [
  "Fruits & Vegetables",
  "Dairy & Bakery",
  "Staples",
  "Snacks & Drinks",
  "Household",
];

export const SEED_PRODUCTS = [
  {
    id: "p101", name: "Fresh Tomato", brand: "FarmFresh", category: "Fruits & Vegetables", image: "🍅",
    rating: 4.3, tags: ["bestseller"],
    variants: [
      { id: "p101-500g", label: "500 g", price: 24, mrp: 32, stock: 40 },
      { id: "p101-1kg", label: "1 kg", price: 45, mrp: 60, stock: 18 },
    ],
  },
  {
    id: "p102", name: "Onion", brand: "FarmFresh", category: "Fruits & Vegetables", image: "🧅",
    rating: 4.1, tags: [],
    variants: [
      { id: "p102-1kg", label: "1 kg", price: 38, mrp: 50, stock: 35 },
      { id: "p102-2kg", label: "2 kg", price: 72, mrp: 100, stock: 4 },
    ],
  },
  {
    id: "p103", name: "Robusta Banana", brand: "FarmFresh", category: "Fruits & Vegetables", image: "🍌",
    rating: 4.4, tags: ["organic"],
    variants: [{ id: "p103-6pc", label: "6 pcs", price: 39, mrp: 48, stock: 25 }],
  },
  {
    id: "p104", name: "Shimla Apple", brand: "Orchard Gold", category: "Fruits & Vegetables", image: "🍎",
    rating: 4.6, tags: ["bestseller"],
    variants: [
      { id: "p104-4pc", label: "4 pcs", price: 119, mrp: 160, stock: 12 },
      { id: "p104-1kg", label: "1 kg", price: 199, mrp: 260, stock: 0 },
    ],
  },
  {
    id: "p105", name: "Coriander Leaves", brand: "FarmFresh", category: "Fruits & Vegetables", image: "🌿",
    rating: 4.0, tags: ["organic"],
    variants: [{ id: "p105-100g", label: "100 g", price: 12, mrp: 15, stock: 0 }],
  },
  {
    id: "p201", name: "Toned Milk", brand: "Heritage Valley", category: "Dairy & Bakery", image: "🥛",
    rating: 4.5, tags: ["bestseller"],
    variants: [
      { id: "p201-500ml", label: "500 ml", price: 28, mrp: 28, stock: 60 },
      { id: "p201-1l", label: "1 L", price: 55, mrp: 56, stock: 30 },
    ],
  },
  {
    id: "p202", name: "Fresh Paneer", brand: "Heritage Valley", category: "Dairy & Bakery", image: "🧀",
    rating: 4.4, tags: [],
    variants: [{ id: "p202-200g", label: "200 g", price: 89, mrp: 99, stock: 9 }],
  },
  {
    id: "p203", name: "Whole Wheat Bread", brand: "Daily Bake", category: "Dairy & Bakery", image: "🍞",
    rating: 4.2, tags: ["new"],
    variants: [{ id: "p203-400g", label: "400 g", price: 45, mrp: 50, stock: 15 }],
  },
  {
    id: "p204", name: "Farm Eggs", brand: "Happy Hens", category: "Dairy & Bakery", image: "🥚",
    rating: 4.3, tags: [],
    variants: [
      { id: "p204-6pc", label: "6 pcs", price: 54, mrp: 60, stock: 20 },
      { id: "p204-12pc", label: "12 pcs", price: 99, mrp: 120, stock: 3 },
    ],
  },
  {
    id: "p301", name: "Sona Masoori Rice", brand: "Annapurna", category: "Staples", image: "🍚",
    rating: 4.5, tags: ["bestseller"],
    variants: [
      { id: "p301-1kg", label: "1 kg", price: 72, mrp: 90, stock: 50 },
      { id: "p301-5kg", label: "5 kg", price: 345, mrp: 450, stock: 10 },
    ],
  },
  {
    id: "p302", name: "Toor Dal", brand: "Annapurna", category: "Staples", image: "🥣",
    rating: 4.3, tags: [],
    variants: [{ id: "p302-1kg", label: "1 kg", price: 165, mrp: 199, stock: 22 }],
  },
  {
    id: "p303", name: "Sunflower Oil", brand: "GoldDrop", category: "Staples", image: "🛢️",
    rating: 4.2, tags: [],
    variants: [
      { id: "p303-1l", label: "1 L", price: 139, mrp: 175, stock: 14 },
      { id: "p303-5l", label: "5 L", price: 650, mrp: 850, stock: 2 },
    ],
  },
  {
    id: "p304", name: "Chakki Atta", brand: "Annapurna", category: "Staples", image: "🌾",
    rating: 4.4, tags: ["new"],
    variants: [{ id: "p304-5kg", label: "5 kg", price: 249, mrp: 310, stock: 16 }],
  },
  {
    id: "p401", name: "Salted Potato Chips", brand: "Crunchy", category: "Snacks & Drinks", image: "🥔",
    rating: 4.1, tags: ["bestseller"],
    variants: [
      { id: "p401-52g", label: "52 g", price: 20, mrp: 20, stock: 80 },
      { id: "p401-150g", label: "150 g", price: 50, mrp: 55, stock: 26 },
    ],
  },
  {
    id: "p402", name: "Dark Chocolate", brand: "CocoaCraft", category: "Snacks & Drinks", image: "🍫",
    rating: 4.6, tags: ["new"],
    variants: [{ id: "p402-80g", label: "80 g", price: 99, mrp: 120, stock: 7 }],
  },
  {
    id: "p403", name: "Cold Coffee", brand: "BrewBox", category: "Snacks & Drinks", image: "🥤",
    rating: 4.0, tags: [],
    variants: [{ id: "p403-180ml", label: "180 ml", price: 40, mrp: 45, stock: 30 }],
  },
  {
    id: "p501", name: "Dishwash Liquid", brand: "SparkClean", category: "Household", image: "🧴",
    rating: 4.3, tags: [],
    variants: [
      { id: "p501-500ml", label: "500 ml", price: 99, mrp: 115, stock: 19 },
      { id: "p501-1l", label: "1 L", price: 185, mrp: 230, stock: 1 },
    ],
  },
  {
    id: "p502", name: "Kitchen Towels", brand: "SoftRoll", category: "Household", image: "🧻",
    rating: 4.1, tags: [],
    variants: [{ id: "p502-2pc", label: "2 rolls", price: 89, mrp: 110, stock: 11 }],
  },
];
