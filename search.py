import sys
import duckdb

if len(sys.argv) < 2:
    print("Usage:")
    print("  python search.py tag1 tag2 tag3 ...")
    print("")
    print("Prefix a tag with - to exclude it.")
    raise SystemExit(1)

terms = sys.argv[1:]

conditions = []
params = []

for term in terms:
    negative = term.startswith("-")

    if negative:
        term = term[1:]

    if not term:
        continue

    if negative:
        conditions.append(
            "strpos(' ' || tags || ' ', ' ' || ? || ' ') = 0"
        )
    else:
        conditions.append(
            "strpos(' ' || tags || ' ', ' ' || ? || ' ') > 0"
        )

    params.append(term)

sql = f"""
SELECT
    id,
    rating,
    score
FROM posts
WHERE {" AND ".join(conditions)}
ORDER BY score DESC, id DESC
LIMIT 100
"""

db = duckdb.connect("danbooru.duckdb", read_only=True)

results = db.execute(sql, params).fetchall()

for post_id, rating, score in results:
    print(
        f"{post_id:<10} "
        f"rating={rating:<2} "
        f"score={score}"
    )

print(f"\n{len(results)} results shown.")