# Day 9 – Practice Exercises (ShopKart)

Do these after each lab. Solutions are in `SOLUTIONS.md` – try first!

## Lab 2 – SQL API
1. **Under-₹500 page:** list name and price of products under ₹500, cheapest first.
2. **Brand page:** all products from brand `Prestige` or `Philips`.
3. **Tag search:** products tagged `student`.
4. **Variants:** every `Black` variant with its stock (use `JOIN`).
5. **My Orders:** Rahul (`CUST-002`) – only `Delivered` orders (single-partition).
6. **KPI:** total number of orders paid by `UPI`.
7. **Write:** add a new field `"isFeatured": true` to `BOOK-4002` using `patch_item`.

## Lab 3 – Consistency
8. For each feature pick a level and justify it in one line: *wallet balance*, *product Q&A answers*, *delivery tracking events*, *"recently viewed" list*.

## Lab 4 – Security
9. Write the `az` command that gives an Azure Function's managed identity **Data Contributor** on only the `orders` container.

## Lab 5 – OCR
10. Add a regex that extracts `Net Quantity` from the label and print it.
11. Lower `CONFIDENCE_THRESHOLD` to 0.5 – what changes? Why is a threshold a business decision?

## Lab 6 – Document Intelligence
12. Change `PURCHASE_ORDER` so the invoice is fully approved. What status do you get?
13. Add a check: if `DueDate` is less than 7 days away, print `PAY URGENTLY`.

## Lab 7/8 – Blob + SAS
14. Upload `assets/receipt_store.png` to a new container `expense-receipts` under `2026/11/EMP-104/`.
15. Generate a SAS that lets an auditor **read and list** the `invoices` container for 2 hours.
16. Generate a read SAS that only works from IP `203.0.113.10` (`ip=` parameter). Test it – what HTTP status do you get from your machine?

## Mini project (homework)
17. **Seller onboarding API:** add `POST /api/seller/verify-label` to `lab10_shopkart_api.py` that accepts an image upload, stores it in Blob, runs OCR (lab 5 logic), and returns `{mrp, batch, approved}`.
