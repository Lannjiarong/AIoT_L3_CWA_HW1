"""
Gate 1 Verification Test Suite
Verifies:
1. Secure API Key loading and masking (no secrets logged).
2. HTTP GET to CWA API endpoint F-D0047-093 returns 200 OK.
3. Response JSON structure parsing.
4. Single region extraction (e.g., 臺中市) with Wx, MinT, MaxT, and PoP.
5. All 22 Taiwan counties/cities coverage confirmation.
6. Township-level coverage verification (e.g., 臺中市 29 townships).
7. Writes complete audit log to gate1_verification.log.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output in Windows console
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from src.cwa_api import (
    get_cwa_api_key,
    mask_api_key,
    fetch_forecast_raw,
    parse_forecast_records,
    DEFAULT_DATASET_ID,
    DEFAULT_ALL_TAIWAN_LOCATION_ID,
)


def run_gate1_verification() -> bool:
    log_lines = []

    def log(msg: str):
        print(msg)
        log_lines.append(msg)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log("=" * 60)
    log(f"TAIWAN WEATHER GIS — GATE 1 VERIFICATION RUN ({timestamp})")
    log("=" * 60)

    # 1. API Key Validation
    log("\n[Step 1/6] Validating API Key Security Configuration...")
    try:
        api_key = get_cwa_api_key()
        masked = mask_api_key(api_key)
        assert masked.startswith("CWA-"), f"Masked key format error: {masked}"
        assert len(api_key) > 20, "API key is too short to be valid"
        assert api_key not in masked, "Plaintext API key leaked into masked string!"
        log(f"  ✓ API key detected and loaded successfully.")
        log(f"  ✓ Safe masked key for logging: {masked}")
    except Exception as e:
        log(f"  ✗ Step 1 Failed: {e}")
        return False

    # 2. HTTP Request & Status Code Verification
    log("\n[Step 2/6] Sending HTTP GET to CWA Open Data API...")
    log(f"  Endpoint: https://opendata.cwa.gov.tw/api/v1/rest/datastore/{DEFAULT_DATASET_ID}")
    log(f"  Query Location ID: {DEFAULT_ALL_TAIWAN_LOCATION_ID} (全臺灣 1 週各縣市預報)")
    try:
        raw_data = fetch_forecast_raw(
            dataset_id=DEFAULT_DATASET_ID,
            location_id=DEFAULT_ALL_TAIWAN_LOCATION_ID,
            api_key=api_key,
        )
        assert raw_data.get("success") in [True, "true"], "Response success field is not True"
        log("  ✓ HTTP Status: 200 OK")
        log("  ✓ API Response 'success': True")
    except Exception as e:
        log(f"  ✗ Step 2 Failed: {e}")
        return False

    # 3. JSON Structure & Hierarchy Parsing
    log("\n[Step 3/6] Inspecting JSON Response Schema...")
    try:
        records_obj = raw_data.get("records", {})
        assert "Locations" in records_obj, "Missing 'Locations' key in records"
        locations_array = records_obj["Locations"]
        assert len(locations_array) > 0, "'Locations' array is empty"
        first_loc_group = locations_array[0]
        desc = first_loc_group.get("DatasetDescription", "")
        location_items = first_loc_group.get("Location", [])
        log(f"  ✓ Locations group dataset: '{desc}'")
        log(f"  ✓ Total location entities in response: {len(location_items)}")
        assert len(location_items) >= 22, f"Expected at least 22 county locations, got {len(location_items)}"
    except Exception as e:
        log(f"  ✗ Step 3 Failed: {e}")
        return False

    # 4. Single Region Extraction (e.g., 臺中市) & Field Verification
    log("\n[Step 4/6] Verifying Single Region Field Extraction (臺中市)...")
    try:
        all_records = parse_forecast_records(raw_data)
        taichung_records = [r for r in all_records if r["location_name"] == "臺中市"]
        assert len(taichung_records) > 0, "No records found for '臺中市'"
        log(f"  ✓ Found {len(taichung_records)} forecast intervals for '臺中市'.")

        sample = taichung_records[0]
        log(f"  Sample Forecast Interval:")
        log(f"    - Location:     {sample['location_name']}")
        log(f"    - Forecast Time:{sample['start_time']} -> {sample['end_time']}")
        log(f"    - Weather (Wx): {sample['weather']} (code: {sample['weather_code']})")
        log(f"    - Min Temp (MinT): {sample['min_temp']} °C")
        log(f"    - Max Temp (MaxT): {sample['max_temp']} °C")
        log(f"    - Rain Pop (PoP):  {sample['pop']} %")

        # Validate non-null values
        assert sample["min_temp"] is not None, "MinT should not be None"
        assert sample["max_temp"] is not None, "MaxT should not be None"
        assert sample["min_temp"] <= sample["max_temp"], "MinT cannot be higher than MaxT"
        assert sample["weather"] is not None, "Weather (Wx) should not be None"
        log("  ✓ All required fields (Wx, MinT, MaxT, PoP) extracted and validated.")
    except Exception as e:
        log(f"  ✗ Step 4 Failed: {e}")
        return False

    # 5. Full Taiwan County Coverage Check
    log("\n[Step 5/6] Confirming Taiwan-Wide Coverage (All 22 Counties & Cities)...")
    expected_counties = [
        "基隆市", "臺北市", "新北市", "桃園市", "新竹市", "新竹縣", "苗栗縣",
        "臺中市", "彰化縣", "南投縣", "雲林縣", "嘉義市", "嘉義縣", "臺南市",
        "高雄市", "屏東縣", "宜蘭縣", "花蓮縣", "臺東縣", "澎湖縣", "金門縣", "連江縣"
    ]
    present_locations = set(r["location_name"] for r in all_records)
    missing = [c for c in expected_counties if c not in present_locations]
    if missing:
        log(f"  ✗ Missing counties: {missing}")
        return False
    log(f"  ✓ All 22 Taiwan counties/cities confirmed present:")
    log(f"    {', '.join(sorted(present_locations))}")
    log(f"  ✓ Total parsed nationwide forecast records: {len(all_records)}")

    # 6. Township-Level API Verification (F-D0047-075 for 臺中市 townships)
    log("\n[Step 6/6] Verifying Township-Level Retrieval (臺中市 29 Townships via F-D0047-075)...")
    try:
        taichung_raw = fetch_forecast_raw(
            dataset_id=DEFAULT_DATASET_ID,
            location_id="F-D0047-075",
            api_key=api_key,
        )
        taichung_townships = parse_forecast_records(taichung_raw)
        township_names = set(r["location_name"] for r in taichung_townships)
        log(f"  ✓ Retrieved {len(township_names)} townships in 臺中市.")
        log(f"  ✓ Sample townships: {list(township_names)[:8]}...")
        assert len(township_names) == 29, f"Expected 29 townships in Taichung, got {len(township_names)}"
    except Exception as e:
        log(f"  ✗ Step 6 Failed: {e}")
        return False

    # Final Gate Check
    log("\n" + "=" * 60)
    log("ALL GATE 1 CRITERIA MET AND VERIFIED SUCCESSFULLY.")
    log("GATE 1 = PASS")
    log("=" * 60)

    # Save log file
    log_path = Path("gate1_verification.log")
    log_path.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\n[Artifact] Full verification log saved to: {log_path.resolve()}")
    return True


if __name__ == "__main__":
    success = run_gate1_verification()
    sys.exit(0 if success else 1)
