import duckdb

db = duckdb.connect("danbooru.duckdb")

print("Building local database...")

db.execute("""
CREATE OR REPLACE TABLE posts AS
SELECT
    id,
    rating,
    score,

    trim(
        concat_ws(
            ' ',
            coalesce(tag_string_general, ''),
            coalesce(tag_string_artist, ''),
            coalesce(tag_string_copyright, ''),
            coalesce(tag_string_character, ''),
            coalesce(tag_string_meta, '')
        )
    ) AS tags

FROM read_parquet('posts.parquet')
""")

count = db.execute("SELECT count(*) FROM posts").fetchone()[0]

print(f"Database contains {count:,} posts.")

db.close()