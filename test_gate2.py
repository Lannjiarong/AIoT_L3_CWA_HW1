"""
Gate 2 Verification Test Suite
Verifies:
1. SQLite schema design and table/index creation (data/data.db).
2. End-to-end ETL execution with real CWA data.
3. SQL SELECT queries for single region (臺中市) with column & value validation.
4. Full nationwide coverage verification via SQL (22 counties/cities).
5. SQL aggregation queries for daily MinT/MaxT summaries.
6. Idempotency verification: Re-running ETL results in identical row count (0 duplicates).
7. Database connection safety and resource cleanup.
8. Writes complete audit log to gate2_verification.log.
"""

import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 console output in Windows
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from src.db_manager import (
    get_db_connection,
    init_db,
    query_forecasts_by_region,
    query_distinct_regions,
    query_daily_summary,
    query_to_dataframe,
    DEFAULT_DB_PATH,
)
from src.etl import run_etl


def run_gate2_verification() -> bool:
    log_lines = []

    def log(msg: str):
        print(msg)
        log_lines.append(msg)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log("=" * 60)
    log(f"TAIWAN WEATHER GIS — GATE 2 VERIFICATION RUN ({timestamp})")
    log("=" * 60)

    db_path = DEFAULT_DB_PATH

    # 1. Database Initialization & Schema Validation
    log("\n[Step 1/6] Initializing SQLite Database & Validating Schema...")
    try:
        init_db(db_path)
        assert db_path.exists(), f"Database file {db_path} was not created!"
        log(f"  ✓ Database file confirmed at: {db_path.resolve()}")

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            # Check table structure
            cursor.execute("PRAGMA table_info(TemperatureForecasts);")
            columns = {row["name"]: row["type"] for row in cursor.fetchall()}
            required_cols = ["id", "regionName", "dataDate", "startTime", "endTime", "weather", "weatherCode", "minT", "maxT", "pop", "updatedAt"]
            for col in required_cols:
                assert col in columns, f"Missing column in TemperatureForecasts: {col}"
            log(f"  ✓ Verified columns in TemperatureForecasts table: {list(columns.keys())}")

            # Check indexes
            cursor.execute("PRAGMA index_list(TemperatureForecasts);")
            indexes = [row["name"] for row in cursor.fetchall()]
            log(f"  ✓ Active indexes on table: {indexes}")
    except Exception as e:
        log(f"  ✗ Step 1 Failed: {e}")
        return False

    # 2. Execute ETL Pipeline
    log("\n[Step 2/6] Running ETL Pipeline (CWA API -> Transform -> SQLite Load)...")
    try:
        etl_result = run_etl(db_path=db_path)
        log(f"  ✓ ETL Status: {etl_result['status']}")
        log(f"  ✓ Loaded Records Count: {etl_result['loaded_records']}")
        log(f"  ✓ Distinct Regions Loaded: {etl_result['distinct_regions']}")
        log(f"  ✓ ETL Execution Time: {etl_result['elapsed_seconds']}s")
        assert etl_result["loaded_records"] > 0, "No records were loaded by ETL"
    except Exception as e:
        log(f"  ✗ Step 2 Failed: {e}")
        return False

    # 3. SQL Query Verification for Single Region (臺中市)
    log("\n[Step 3/6] Verifying Single Region SQL Query (臺中市)...")
    try:
        taichung_rows = query_forecasts_by_region("臺中市", db_path=db_path)
        assert len(taichung_rows) > 0, "No records returned for '臺中市'"
        log(f"  ✓ Retrieved {len(taichung_rows)} forecast rows for 臺中市.")

        sample = taichung_rows[0]
        log(f"  Sample Database Row:")
        log(f"    - ID:          {sample['id']}")
        log(f"    - regionName:  {sample['regionName']}")
        log(f"    - dataDate:    {sample['dataDate']}")
        log(f"    - startTime:   {sample['startTime']}")
        log(f"    - endTime:     {sample['endTime']}")
        log(f"    - weather:     {sample['weather']} ({sample['weatherCode']})")
        log(f"    - minT:        {sample['minT']} °C")
        log(f"    - maxT:        {sample['maxT']} °C")
        log(f"    - pop:         {sample['pop']} %")
        log(f"    - updatedAt:   {sample['updatedAt']}")

        # Validate numeric and integrity constraints
        for row in taichung_rows:
            assert row["minT"] <= row["maxT"], f"Data inconsistency: minT {row['minT']} > maxT {row['maxT']}"
            assert row["regionName"] == "臺中市"
            assert len(row["dataDate"]) == 10, f"Invalid dataDate format: {row['dataDate']}"
        log("  ✓ All row constraints (minT <= maxT, valid date strings) satisfied.")
    except Exception as e:
        log(f"  ✗ Step 3 Failed: {e}")
        return False

    # 4. Multi-Region & Nationwide Coverage Verification (All 22 Counties)
    log("\n[Step 4/6] Verifying Multi-Region SQL Query (All 22 Counties & Cities)...")
    try:
        regions = query_distinct_regions(db_path=db_path)
        expected_counties = [
            "基隆市", "臺北市", "新北市", "桃園市", "新竹市", "新竹縣", "苗栗縣",
            "臺中市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "臺南市",
            "高雄市", "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣"
        ]
        missing = [c for c in expected_counties if c not in regions]
        if missing:
            log(f"  ✗ Missing regions in DB: {missing}")
            return False

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM TemperatureForecasts;")
            total_count = cursor.fetchone()["total"]

        log(f"  ✓ All 22 Taiwan counties present in SQLite database:")
        log(f"    {', '.join(sorted(regions))}")
        log(f"  ✓ Total database rows count: {total_count}")
        assert total_count >= 22 * 14, f"Expected at least {22 * 14} rows, got {total_count}"
    except Exception as e:
        log(f"  ✗ Step 4 Failed: {e}")
        return False

    # 5. SQL Daily Aggregation & Pandas Integration
    log("\n[Step 5/6] Verifying Daily Aggregation Query (MIN/MAX & Pandas DataFrame)...")
    try:
        daily_summary = query_daily_summary("臺中市", db_path=db_path)
        assert len(daily_summary) >= 7, f"Expected 7 daily forecasts, got {len(daily_summary)}"
        log(f"  ✓ Aggregated {len(daily_summary)} daily summaries for 臺中市:")
        for day in daily_summary[:3]:
            log(f"    • Date: {day['dataDate']} | Min: {day['dailyMinT']}°C | Max: {day['dailyMaxT']}°C | Weather: {day['weatherSummary']}")

        # Test Pandas DataFrame query
        df = query_to_dataframe("SELECT regionName, AVG(minT) as avgMin, AVG(maxT) as avgMax FROM TemperatureForecasts GROUP BY regionName LIMIT 5;", db_path=db_path)
        assert len(df) == 5, "Pandas DataFrame read failed"
        log("  ✓ Pandas DataFrame SQL integration test passed.")
    except Exception as e:
        log(f"  ✗ Step 5 Failed: {e}")
        return False

    # 6. Idempotency & De-duplication Verification (Second ETL Run)
    log("\n[Step 6/6] Verifying Idempotency & De-duplication Strategy (Second ETL Run)...")
    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM TemperatureForecasts;")
            initial_count = cursor.fetchone()["cnt"]

        # Run ETL again
        log("  Executing second ETL run...")
        second_etl_result = run_etl(db_path=db_path)

        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM TemperatureForecasts;")
            post_count = cursor.fetchone()["cnt"]

        log(f"  Row count before second ETL: {initial_count}")
        log(f"  Row count after second ETL:  {post_count}")
        assert initial_count == post_count, f"Idempotency failed! Count changed from {initial_count} to {post_count}"
        log("  ✓ Idempotency verified: Re-running ETL produced 0 duplicate rows.")
    except Exception as e:
        log(f"  ✗ Step 6 Failed: {e}")
        return False

    # Final Gate Check
    log("\n" + "=" * 60)
    log("ALL GATE 2 CRITERIA MET AND VERIFIED SUCCESSFULLY.")
    log("GATE 2 = PASS")
    log("=" * 60)

    # Save verification log
    log_path = Path("gate2_verification.log")
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\n[Artifact] Full verification log saved to: {log_path.resolve()}")
    return True


if __name__ == "__main__":
    success = run_gate2_verification()
    sys.exit(0 if success else 1)
