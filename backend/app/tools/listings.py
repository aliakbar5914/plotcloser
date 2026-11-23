"""Tool: search the listings table."""
from typing import Literal

from langchain_core.tools import tool

from app.db.connection import fetch_all
from app.tools.helpers import format_pkr

MAX_RESULTS = 5  # keep tool output short = fewer tokens


def _format_listing(row: dict) -> str:
    price = format_pkr(row["price_pkr"]) + (" /month" if row["purpose"] == "rent" else "")
    parts = [f"#{row['id']}", row["title"], f"{row['area']}, {row['city']}"]
    if row["size_label"]:
        parts.append(row["size_label"])
    if row["bedrooms"]:
        parts.append(f"{row['bedrooms']} bed")
    parts.append(f"PKR {price} ({row['purpose']})")
    return " | ".join(parts) + f"\n   {row['description']}"


@tool
def search_listings(
    listing_type: Literal["property", "car"] = "property",
    purpose: Literal["sale", "rent"] | None = None,
    city: str | None = None,
    area: str | None = None,
    max_price_pkr: int | None = None,
    min_size_marla: float | None = None,
    keyword: str | None = None,
) -> str:
    """Search available properties or cars. Use whenever the customer asks what is available.

    Args:
        listing_type: "property" (houses, plots, rentals) or "car".
        purpose: "sale" or "rent". Leave empty if unknown.
        city: e.g. "Islamabad" or "Rawalpindi".
        area: sector or society, e.g. "DHA", "Bahria Town", "G-13", "B-17".
        max_price_pkr: maximum price in PKR (1 crore = 10000000, 1 lakh = 100000).
        min_size_marla: minimum size in marla (1 kanal = 20 marla).
        keyword: free word like "plot", "house", "apartment", "Corolla", "Civic".
    """
    conditions = ["status = 'available'", "type = %s"]
    params: list = [listing_type]

    if purpose:
        conditions.append("purpose = %s")
        params.append(purpose)
    if city:
        conditions.append("city ILIKE %s")
        params.append(f"%{city}%")
    if area:
        conditions.append("(area ILIKE %s OR title ILIKE %s)")
        params += [f"%{area}%", f"%{area}%"]
    if max_price_pkr:
        conditions.append("price_pkr <= %s")
        params.append(max_price_pkr)
    if min_size_marla:
        conditions.append("size_marla >= %s")
        params.append(min_size_marla)
    if keyword:
        conditions.append("(title ILIKE %s OR description ILIKE %s)")
        params += [f"%{keyword}%", f"%{keyword}%"]

    # With a budget, show the best options closest to the budget first.
    order = "price_pkr DESC" if max_price_pkr else "price_pkr ASC"
    sql = (
        "SELECT * FROM listings WHERE " + " AND ".join(conditions)
        + f" ORDER BY {order} LIMIT {MAX_RESULTS}"
    )
    rows = fetch_all(sql, tuple(params))

    if not rows:
        return "No listings match these filters. Suggest relaxing budget, area or size."
    return "\n".join(_format_listing(row) for row in rows)
