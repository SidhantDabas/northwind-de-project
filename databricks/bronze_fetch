import requests
import json
from pyspark.sql.types import StringType, StructType, StructField
from datetime import datetime, timezone

BASE_URL = "https://northwind-de-project.onrender.com/"

BRONZE_BASE = "abfss://bronze@nwpipelined.dfs.core.windows.net"

def fetch_all_pages(endpoint: str) -> list:
    records = []
    page = 1
    while True:
        response = requests.get(
            f"{BASE_URL}/{endpoint}/",
            params={"page": page},
            timeout=60
        )
        response.raise_for_status()
        body = response.json()
        records.extend(body["data"])
        print(f"  Fetched page {page}/{body['pagination']['total_pages']} from {endpoint}")
        if body["pagination"]["next_page"] is None:
            break
        page += 1
    return records

def write_to_bronze(records: list, entity_name: str):
    ingested_at = datetime.now(timezone.utc).isoformat()
    rows = [
        (json.dumps(r), ingested_at, f"northwind_api/{entity_name}")
        for r in records
    ]
    schema = StructType([
        StructField("raw_json", StringType(), False),
        StructField("_ingested_at", StringType(), False),
        StructField("_source", StringType(), False)
    ])
    df = spark.createDataFrame(rows, schema)
    df.write.format("delta") \
        .mode("append") \
        .save(f"{BRONZE_BASE}/{entity_name}/")
    print(f"  Written {len(records)} records to bronze/{entity_name}")

for entity in ["customers", "orders", "products"]:
    print(f"Ingesting {entity}...")
    records = fetch_all_pages(entity)
    write_to_bronze(records, entity)
    print(f"Done: {entity}")

print("Bronze ingestion complete.")