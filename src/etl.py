"""
ETL Pipeline Module
Extracts real weather forecasts from CWA Open Data API (F-D0047-093).
Transforms and validates JSON payload into structured records.
Loads records idempotently into SQLite (data/data.db).
"""

import time
from pathlib import Path
from typing import Any, Dict
from src.cwa_api import (
    fetch_forecast_raw,
    parse_forecast_records,
    DEFAULT_DATASET_ID,
    DEFAULT_ALL_TAIWAN_LOCATION_ID,
)
from src.db_manager import (
    init_db,
    upsert_forecast_records,
    query_distinct_regions,
    DEFAULT_DB_PATH,
)


def run_etl(
    dataset_id: str = DEFAULT_DATASET_ID,
    location_id: str = DEFAULT_ALL_TAIWAN_LOCATION_ID,
    db_path: Path = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """
    Execute full ETL pipeline:
    1. Extract from CWA Open Data API.
    2. Transform JSON to normalized record dictionaries.
    3. Load into SQLite database data/data.db via UPSERT.
    """
    start_time = time.time()
    db_path = Path(db_path)

    # 1. Initialize DB & Schema
    init_db(db_path)

    # 2. Extract
    raw_data = fetch_forecast_raw(dataset_id=dataset_id, location_id=location_id)

    # 3. Transform
    records = parse_forecast_records(raw_data)
    if not records:
        raise ValueError("ETL Transform produced 0 valid records from CWA API.")

    # 4. Load (Idempotent UPSERT)
    loaded_count = upsert_forecast_records(records, db_path=db_path)

    # 5. Post-load Verification
    regions = query_distinct_regions(db_path=db_path)
    elapsed = round(time.time() - start_time, 2)

    return {
        "status": "success",
        "loaded_records": loaded_count,
        "distinct_regions": len(regions),
        "region_names": regions,
        "elapsed_seconds": elapsed,
        "db_path": str(db_path),
    }


if __name__ == "__main__":
    result = run_etl()
    print("ETL Execution Result:", result)
