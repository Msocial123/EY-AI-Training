"""Auto-tests for the mini project.
  python mini_project/test_reviews.py                   -> tests YOUR reviews_starter.py
  python mini_project/test_reviews.py reviews_solution  -> tests the trainer solution"""
import sys, pathlib, importlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from azure.cosmos import exceptions

m = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "reviews_starter")
reviews, restaurants = m.reviews, m.restaurants
add_review, latest_reviews, average_rating = m.add_review, m.latest_reviews, m.average_rating
edit_review, delete_review = m.edit_review, m.delete_review
passed = 0


def check(name, cond):
    global passed
    passed += bool(cond)
    print(("PASS  " if cond else "FAIL  ") + name)


try:
    restaurants.upsert_item({"id": "r-900", "name": "Test Tiffins", "ratingCount": 0, "ratingSum": 0})
    for cid in ("t1", "t2", "t3"):
        try:
            reviews.delete_item(f"rev-r-900-{cid}", partition_key="r-900")
        except exceptions.CosmosResourceNotFoundError:
            pass
    add_review("r-900", "t1", 5, "Crispy dosa!")
    add_review("r-900", "t2", 3, "OK")
    add_review("r-900", "t3", 4, "Good chutney")
    check("average after 3 reviews == 4.0", abs(average_rating("r-900") - 4.0) < 1e-9)
    try:
        add_review("r-900", "t1", 4, "again"); check("duplicate review rejected", False)
    except (ValueError, exceptions.CosmosResourceExistsError):
        check("duplicate review rejected", True)
    try:
        add_review("r-900", "t9", 7, "bad"); check("rating 7 rejected", False)
    except ValueError:
        check("rating 7 rejected", True)
    check("latest_reviews returns 2", len(latest_reviews("r-900", 2)) == 2)
    edit_review("r-900", "t2", 5, "Better on second visit")
    check("average after edit == 4.666", abs(average_rating("r-900") - 14 / 3) < 1e-6)
    delete_review("r-900", "t1")
    check("average after delete == 4.5", abs(average_rating("r-900") - 4.5) < 1e-9)

except NotImplementedError:
    import traceback
    fn = traceback.extract_tb(sys.exc_info()[2])[-1].name
    print(f"STOP  {fn}() is not written yet - fill in its TODO and run again")

print(f"\n{passed}/6 tests passed")
