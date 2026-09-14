from google.cloud import bigquery
from google.cloud import bigquery_storage_v1
import pyarrow as pa
import pyarrow.parquet as pq

client = bigquery.Client()

query = """
SELECT
    id,
    rating,
    score,
    tag_string_general,
    tag_string_artist,
    tag_string_copyright,
    tag_string_character,
    tag_string_meta
FROM `danbooru1.danbooru_public.posts`
WHERE
    is_deleted = false
    AND is_banned = false
    AND is_flagged = false
"""

print("Starting BigQuery job...")

job = client.query(query)
rows = job.result()

storage = bigquery_storage_v1.BigQueryReadClient()

writer = None
count = 0

try:
    for batch in rows.to_arrow_iterable(bqstorage_client=storage):
        table = pa.Table.from_batches([batch])

        if writer is None:
            writer = pq.ParquetWriter(
                "posts.parquet",
                table.schema,
                compression="zstd",
            )

        writer.write_table(table)
        count += table.num_rows
        print(f"\rDownloaded {count:,} posts", end="", flush=True)

finally:
    if writer is not None:
        writer.close()

print(f"\nFinished: {count:,} posts")