from flask import Flask, render_template, request
import duckdb

app = Flask(__name__)

DB_PATH = "danbooru.duckdb"
PER_PAGE = 60


def parse_search(search_text):
    positive = []
    negative = []

    for raw in search_text.split():
        raw = raw.strip()
        if not raw:
            continue

        if raw.startswith("-") and len(raw) > 1:
            negative.append(raw[1:])
        else:
            positive.append(raw)

    return positive, negative


def build_query(search_text, rating, sort, page):
    positive, negative = parse_search(search_text)

    conditions = []
    params = []

    for tag in positive:
        conditions.append("strpos(' ' || tags || ' ', ' ' || ? || ' ') > 0")
        params.append(tag)

    for tag in negative:
        conditions.append("strpos(' ' || tags || ' ', ' ' || ? || ' ') = 0")
        params.append(tag)

    if rating in {"g", "s", "q", "e"}:
        conditions.append("rating = ?")
        params.append(rating)

    where_sql = " AND ".join(conditions) if conditions else "TRUE"

    sort_sql = {
        "score": "score DESC, id DESC",
        "newest": "id DESC",
        "oldest": "id ASC",
    }.get(sort, "score DESC, id DESC")

    offset = max(page - 1, 0) * PER_PAGE

    query = f"""
        SELECT id, rating, score, tags
        FROM posts
        WHERE {where_sql}
        ORDER BY {sort_sql}
        LIMIT {PER_PAGE}
        OFFSET {offset}
    """

    count_query = f"SELECT count(*) FROM posts WHERE {where_sql}"

    return query, count_query, params


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    rating = request.args.get("rating", "")
    sort = request.args.get("sort", "score")

    try:
        page = max(int(request.args.get("page", "1")), 1)
    except ValueError:
        page = 1

    query, count_query, params = build_query(q, rating, sort, page)

    db = duckdb.connect(DB_PATH, read_only=True)
    try:
        total = db.execute(count_query, params).fetchone()[0]
        rows = db.execute(query, params).fetchall()
    finally:
        db.close()

    results = [
        {
            "id": row[0],
            "rating": row[1],
            "score": row[2],
            "tags": row[3],
            "url": f"https://danbooru.donmai.us/posts/{row[0]}",
        }
        for row in rows
    ]

    return render_template(
        "index.html",
        results=results,
        q=q,
        rating=rating,
        sort=sort,
        page=page,
        total=total,
        has_prev=page > 1,
        has_next=page * PER_PAGE < total,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
