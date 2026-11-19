"""
LAB 2 SOLUTION - Pydantic

Task: build a ProductReview model with these rules
  - product_id: int > 0
  - customer_name: at least 2 characters
  - rating: whole number 1 to 5
  - comment: 10 to 500 characters
  - verified_buyer: bool, default False
  - RULE: if rating is 1 or 2, comment must be at least 20 characters
          (so the seller knows what went wrong)
Validate data/reviews.json and print accepted / rejected reviews.
"""
import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, model_validator

BASE_DIR = Path(__file__).parent


class ProductReview(BaseModel):
    product_id: int = Field(gt=0)
    customer_name: str = Field(min_length=2)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=10, max_length=500)
    verified_buyer: bool = False

    @model_validator(mode="after")
    def low_rating_needs_reason(self):
        if self.rating <= 2 and len(self.comment) < 20:
            raise ValueError("ratings of 1-2 need a comment of at least 20 characters")
        return self


def main():
    with open(BASE_DIR / "data" / "reviews.json", encoding="utf-8") as f:
        rows = json.load(f)

    for i, row in enumerate(rows, start=1):
        try:
            review = ProductReview.model_validate(row)
            badge = " [Verified]" if review.verified_buyer else ""
            print(f"ACCEPTED #{i}: {'*' * review.rating:<5} {review.customer_name}{badge}")
        except ValidationError as e:
            reasons = "; ".join(err["msg"] for err in e.errors())
            print(f"REJECTED #{i}: {reasons}")


if __name__ == "__main__":
    main()
