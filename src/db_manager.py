"""
Database Manager for Taiwan Weather GIS
Handles SQLite Schema, Indexes, Idempotent UPSERT, and Query Operations.
Database: data/data.db
Table: TemperatureForecasts
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

DEFAULT_DB_PATH = Path("data") / "data.db"


def get_db_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Get SQLite database connection with row factory enabled.
    Ensures parent directory exists.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """
    Initialize SQLite Schema with TemperatureForecasts table and performance indexes.
    Enforces UNIQUE constraint on (regionName, startTime, endTime).
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS TemperatureForecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regionName TEXT NOT NULL,
        dataDate TEXT NOT NULL,
        startTime TEXT NOT NULL,
        endTime TEXT NOT NULL,
        weather TEXT,
        weatherCode TEXT,
        minT REAL NOT NULL,
        maxT REAL NOT NULL,
        pop INTEGER,
        updatedAt TEXT DEFAULT (datetime('now', 'localtime')),
        UNIQUE(regionName, startTime, endTime)
    );
    """

    create_index_region_date = """
    CREATE INDEX IF NOT EXISTS idx_region_date 
    ON TemperatureForecasts(regionName, dataDate);
    """

    create_index_date = """
    CREATE INDEX IF NOT EXISTS idx_dataDate 
    ON TemperatureForecasts(dataDate);
    """

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(create_table_sql)
        cursor.execute(create_index_region_date)
        cursor.execute(create_index_date)
        conn.commit()


def upsert_forecast_records(records: List[Dict[str, Any]], db_path: Path = DEFAULT_DB_PATH) -> int:
    """
    Idempotent batch UPSERT into TemperatureForecasts.
    Prevents duplicates on repeated ETL runs.
    Returns the count of processed records.
    """
    if not records:
        return 0

    init_db(db_path)

    upsert_sql = """
    INSERT INTO TemperatureForecasts (
        regionName, dataDate, startTime, endTime, weather, weatherCode, minT, maxT, pop, updatedAt
    ) VALUES (
        :regionName, :dataDate, :startTime, :endTime, :weather, :weatherCode, :minT, :maxT, :pop, datetime('now', 'localtime')
    )
    ON CONFLICT(regionName, startTime, endTime) DO UPDATE SET
        dataDate = excluded.dataDate,
        weather = excluded.weather,
        weatherCode = excluded.weatherCode,
        minT = excluded.minT,
        maxT = excluded.maxT,
        pop = excluded.pop,
        updatedAt = datetime('now', 'localtime');
    """

    # Transform records to match SQL parameters
    param_list = []
    for r in records:
        st = r.get("start_time", "")
        data_date = r.get("data_date") or (st[:10] if st else "")
        param_list.append({
            "regionName": r.get("location_name") or r.get("regionName", ""),
            "dataDate": data_date,
            "startTime": st,
            "endTime": r.get("end_time", ""),
            "weather": r.get("weather"),
            "weatherCode": r.get("weather_code") or r.get("weatherCode"),
            "minT": float(r.get("min_temp") if r.get("min_temp") is not None else r.get("minT", 0.0)),
            "maxT": float(r.get("max_temp") if r.get("max_temp") is not None else r.get("maxT", 0.0)),
            "pop": r.get("pop"),
        })

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(upsert_sql, param_list)
        conn.commit()

    return len(param_list)


def query_forecasts_by_region(region_name: str, db_path: Path = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Query forecast records for a specific region.
    """
    sql = """
    SELECT id, regionName, dataDate, startTime, endTime, weather, weatherCode, minT, maxT, pop, updatedAt
    FROM TemperatureForecasts
    WHERE regionName = ?
    ORDER BY startTime ASC;
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (region_name,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def query_distinct_regions(db_path: Path = DEFAULT_DB_PATH) -> List[str]:
    """
    Query all distinct region names stored in the database.
    """
    sql = "SELECT DISTINCT regionName FROM TemperatureForecasts ORDER BY regionName ASC;"
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        return [row["regionName"] for row in rows]


def query_daily_summary(region_name: Optional[str] = None, db_path: Path = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Aggregate daily MinT and MaxT by region and date.
    """
    if region_name:
        sql = """
        SELECT regionName, dataDate, MIN(minT) as dailyMinT, MAX(maxT) as dailyMaxT,
               GROUP_CONCAT(DISTINCT weather) as weatherSummary
        FROM TemperatureForecasts
        WHERE regionName = ?
        GROUP BY regionName, dataDate
        ORDER BY dataDate ASC;
        """
        params = (region_name,)
    else:
        sql = """
        SELECT regionName, dataDate, MIN(minT) as dailyMinT, MAX(maxT) as dailyMaxT,
               GROUP_CONCAT(DISTINCT weather) as weatherSummary
        FROM TemperatureForecasts
        GROUP BY regionName, dataDate
        ORDER BY regionName ASC, dataDate ASC;
        """
        params = ()

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def query_to_dataframe(sql: str, params: Tuple = (), db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    Execute SQL query and return results as a Pandas DataFrame.
    """
    with get_db_connection(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=params)
