"""
tests/test_schemas.py  ->  Unit tests for Pydantic models (no API, no server)

Run only this file:   pytest tests/test_schemas.py -v
"""
import pytest
from pydantic import ValidationError

from order_service.schemas import Address, OrderCreate
from product_service.schemas import ProductCreate, ProductOut


def test_name_is_cleaned_and_tags_are_normalised(new_product_payload):
    # Arrange
    new_product_payload["name"] = "  boAt    Airdopes 141  "
    # Act
    product = ProductCreate(**new_product_payload)
    # Assert
    assert product.name == "boAt Airdopes 141"
    assert product.tags == ["audio", "earbuds"]  # lower-case, no duplicates, sorted


def test_price_above_mrp_is_rejected(new_product_payload):
    new_product_payload["price"] = 5000  # mrp is 4490
    with pytest.raises(ValidationError) as err:
        ProductCreate(**new_product_payload)
    assert "price cannot be greater than mrp" in str(err.value)


def test_discount_is_computed():
    out = ProductOut(
        id=1, name="Shoe", description=None, category="fashion", price=750, mrp=1000,
        tags=[], seller={"name": "ABC", "city": "Pune"}, created_at="2026-11-19T10:00:00",
    )
    assert out.discount_percent == 25


@pytest.mark.parametrize("pincode", ["012345", "51600", "5160034", "51600A"])
def test_bad_pincodes_are_rejected(pincode):
    with pytest.raises(ValidationError):
        Address(line1="Flat 1, Main Road", city="Kadapa", state="AP", pincode=pincode)


def test_nested_error_shows_exact_location(valid_order):
    valid_order["shipping_address"]["pincode"] = "000000"
    with pytest.raises(ValidationError) as err:
        OrderCreate(**valid_order)
    location = err.value.errors()[0]["loc"]
    assert location == ("shipping_address", "pincode")


def test_duplicate_products_in_order_rejected(valid_order):
    valid_order["items"] = [{"product_id": 4, "quantity": 1}, {"product_id": 4, "quantity": 2}]
    with pytest.raises(ValidationError):
        OrderCreate(**valid_order)
