"""TRANSFORM step: clean, validate and enrich the extracted data."""
import pandas as pd

TEXT_COLUMNS = ["order_id", "customer_id", "product_id", "category", "city", "status"]


def clean_orders(raw_df, valid_statuses):
    """Split raw orders into clean rows and rejected rows (with a reason)."""
    df = raw_df.copy()
    df = df.drop_duplicates(subset="order_id", keep="first")
    for column in TEXT_COLUMNS:
        df[column] = df[column].fillna("").str.strip()
    df["city"] = df["city"].str.title()
    df["category"] = df["category"].str.title()
    df["status"] = df["status"].str.upper()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="coerce")

    df["reject_reason"] = ""
    df.loc[df["customer_id"] == "", "reject_reason"] += "missing customer_id; "
    df.loc[~(df["quantity"] > 0), "reject_reason"] += "invalid quantity; "
    df.loc[~(df["unit_price"] > 0), "reject_reason"] += "invalid unit_price; "
    df.loc[df["order_date"].isna(), "reject_reason"] += "invalid order_date; "
    df.loc[~df["status"].isin(valid_statuses), "reject_reason"] += "unknown status; "

    rejected = df[df["reject_reason"] != ""].copy()
    clean = df[df["reject_reason"] == ""].drop(columns="reject_reason")
    clean["quantity"] = clean["quantity"].astype(int)
    return clean.reset_index(drop=True), rejected.reset_index(drop=True)


def add_order_totals(clean_df, gst_rate):
    """Add amount columns and mark which orders count as revenue."""
    df = clean_df.copy()
    df["line_amount"] = (df["quantity"] * df["unit_price"]).round(2)
    df["gst_amount"] = (df["line_amount"] * gst_rate).round(2)
    df["order_total"] = (df["line_amount"] + df["gst_amount"]).round(2)
    df["counts_as_revenue"] = df["status"] != "CANCELLED"
    return df


def build_category_summary(orders_df):
    """Daily sales per category, counting only orders that are revenue."""
    revenue = orders_df[orders_df["counts_as_revenue"]].copy()
    revenue["sales_date"] = revenue["order_date"].dt.strftime("%Y-%m-%d")
    summary = (
        revenue.groupby(["sales_date", "category"], as_index=False)
        .agg(orders=("order_id", "count"),
             units_sold=("quantity", "sum"),
             revenue_incl_gst=("order_total", "sum"))
    )
    summary["revenue_incl_gst"] = summary["revenue_incl_gst"].round(2)
    summary = summary.sort_values(["sales_date", "revenue_incl_gst"], ascending=[True, False])
    return summary.reset_index(drop=True)


def validate_invoices(invoice_df):
    """Convert invoice amounts to numbers and check that subtotal + tax = total."""
    df = invoice_df.copy()
    for column in ["subtotal", "tax", "total"]:
        df[column] = pd.to_numeric(df[column].astype(str).str.replace(",", ""), errors="coerce")
    difference = (df["subtotal"] + df["tax"] - df["total"]).abs()
    df["is_valid"] = df["invoice_no"].notna() & (difference < 0.01)
    return df
