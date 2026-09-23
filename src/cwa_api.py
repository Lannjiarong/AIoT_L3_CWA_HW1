"""
CWA Open Data API Client Module
Dataset: F-D0047-093 (鄉鎮天氣預報-全臺灣各鄉鎮市區預報資料)
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from dotenv import load_dotenv

# Try injecting truststore for modern SSL validation on Windows/Python 3.14+
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

BASE_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
DEFAULT_DATASET_ID = "F-D0047-093"
DEFAULT_ALL_TAIWAN_LOCATION_ID = "F-D0047-091"  # 1-week forecast for all 22 counties/cities


def get_cwa_api_key(env_path: Optional[Path] = None) -> str:
    """
    Read CWA API key from .env file securely.
    Ensures key starts with 'CWA-' and is non-empty.
    """
    if env_path:
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    api_key = os.getenv("CWA_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Missing CWA_API_KEY in environment or .env file.")
    if not api_key.startswith("CWA-"):
        raise ValueError("Invalid CWA_API_KEY format: must start with 'CWA-'.")
    return api_key


def mask_api_key(api_key: str) -> str:
    """
    Mask API key for safe logging (e.g., CWA-55F...4FB2).
    """
    if len(api_key) <= 10:
        return "***"
    return f"{api_key[:7]}...{api_key[-4:]}"


def fetch_forecast_raw(
    dataset_id: str = DEFAULT_DATASET_ID,
    location_id: str = DEFAULT_ALL_TAIWAN_LOCATION_ID,
    api_key: Optional[str] = None,
    timeout: int = 20,
) -> Dict[str, Any]:
    """
    Fetch raw forecast JSON from CWA API with HTTP status validation.
    """
    if not api_key:
        api_key = get_cwa_api_key()

    url = f"{BASE_URL}/{dataset_id}"
    params = {
        "Authorization": api_key,
        "locationId": location_id,
    }

    response = requests.get(url, params=params, timeout=timeout)
    if response.status_code != 200:
        raise RuntimeError(
            f"CWA API request failed with status {response.status_code}: {response.text[:200]}"
        )

    data = response.json()
    if not data.get("success") == "true" and not data.get("success") is True:
        raise RuntimeError(f"CWA API returned failure response: {data}")

    return data


def parse_weather_elements(elements_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Helper to index weather elements by their ElementName and align time intervals.
    """
    elements_by_name = {el.get("ElementName"): el for el in elements_list}
    return elements_by_name


def parse_forecast_records(raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse CWA API raw response into structured forecast records:
    [
      {
        "location_name": "臺中市",
        "start_time": "2026-09-23T06:00:00+08:00",
        "end_time": "2026-09-23T18:00:00+08:00",
        "weather": "晴時多雲",
        "weather_code": "02",
        "min_temp": 25.0,
        "max_temp": 29.0,
        "pop": 10
      },
      ...
    ]
    """
    records = []
    locations_group = raw_data.get("records", {}).get("Locations", [])
    if not locations_group:
        return records

    for loc_group in locations_group:
        location_list = loc_group.get("Location", [])
        for loc in location_list:
            loc_name = loc.get("LocationName", "")
            elements = loc.get("WeatherElement", [])
            el_map = {e.get("ElementName"): e for e in elements}

            max_t_times = el_map.get("最高溫度", {}).get("Time", [])
            min_t_times = el_map.get("最低溫度", {}).get("Time", [])
            wx_times = el_map.get("天氣現象", {}).get("Time", [])
            pop_times = el_map.get("12小時降雨機率", {}).get("Time", [])

            # Index by (start_time, end_time)
            intervals: Dict[tuple, Dict[str, Any]] = {}

            # Process MaxT
            for item in max_t_times:
                st = item.get("StartTime")
                et = item.get("EndTime")
                key = (st, et)
                val_list = item.get("ElementValue", [{}])
                val = val_list[0].get("MaxTemperature") if val_list else None
                if key not in intervals:
                    intervals[key] = {"start_time": st, "end_time": et}
                if val is not None:
                    intervals[key]["max_temp"] = float(val)

            # Process MinT
            for item in min_t_times:
                st = item.get("StartTime")
                et = item.get("EndTime")
                key = (st, et)
                val_list = item.get("ElementValue", [{}])
                val = val_list[0].get("MinTemperature") if val_list else None
                if key not in intervals:
                    intervals[key] = {"start_time": st, "end_time": et}
                if val is not None:
                    intervals[key]["min_temp"] = float(val)

            # Process Wx
            for item in wx_times:
                st = item.get("StartTime")
                et = item.get("EndTime")
                key = (st, et)
                val_list = item.get("ElementValue", [{}])
                if val_list and key in intervals:
                    intervals[key]["weather"] = val_list[0].get("Weather")
                    intervals[key]["weather_code"] = val_list[0].get("WeatherCode")

            # Process PoP (12h precipitation probability)
            for item in pop_times:
                st = item.get("StartTime")
                et = item.get("EndTime")
                key = (st, et)
                val_list = item.get("ElementValue", [{}])
                if val_list and key in intervals:
                    pop_val = val_list[0].get("ProbabilityOfPrecipitation")
                    intervals[key]["pop"] = int(pop_val) if pop_val and pop_val.isdigit() else None

            # Flatten to records
            for key, rec in sorted(intervals.items(), key=lambda x: (x[0][0] or "", x[0][1] or "")):
                records.append({
                    "location_name": loc_name,
                    "start_time": rec.get("start_time"),
                    "end_time": rec.get("end_time"),
                    "weather": rec.get("weather"),
                    "weather_code": rec.get("weather_code"),
                    "min_temp": rec.get("min_temp"),
                    "max_temp": rec.get("max_temp"),
                    "pop": rec.get("pop"),
                })

    return records
