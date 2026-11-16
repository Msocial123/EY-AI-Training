"""END-OF-DAY MINI PROJECT - QuickBite Reviews Service (starter)
Fill in every TODO, then run:  python mini_project/test_reviews.py
Read the spec in the Day 8 playbook (Section 'Mini Project') first."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from azure.cosmos import exceptions
from qb.config import get_container

reviews = get_container("Reviews", "/restaurantId")        # decided in design review
restaurants = get_container("Restaurants", "/id")


def add_review(restaurant_id, customer_id, rating, text):
    """Save a review AND update the restaurant's ratingCount / ratingSum (denormalised summary).
    Reject rating outside 1..5 with ValueError. One review per customer per restaurant
    (hint: deterministic id f'rev-{restaurant_id}-{customer_id}' + create_item -> 409)."""
    raise NotImplementedError  # TODO


def latest_reviews(restaurant_id, n=3):
    """Newest n reviews for one restaurant - must be a SINGLE-partition query."""
    raise NotImplementedError  # TODO


def average_rating(restaurant_id):
    """Read from the restaurant document's summary - NOT by scanning all reviews."""
    raise NotImplementedError  # TODO


def edit_review(restaurant_id, customer_id, new_rating, new_text):
    """Update text/rating with patch, and keep ratingSum correct (incr by the difference)."""
    raise NotImplementedError  # TODO


def delete_review(restaurant_id, customer_id):
    """Delete the review and fix the summary (incr count -1, sum -rating)."""
    raise NotImplementedError  # TODO

# Test your work:  python mini_project/test_reviews.py
