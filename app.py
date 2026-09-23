"""
Taiwan Weather GIS — Interactive Streamlit Dashboard
Features:
- Dark theme & Glassmorphism styling inspired by https://taiwan-weather-map.vercel.app/
- Reads forecast data from SQLite (data/data.db)
- Interactive Folium map with CartoDB DarkMatter basemap and 9-step temperature badges
- Region selector & 7-day MinT/MaxT Plotly trend line chart
- Live CWA API data synchronization mechanism
"""

import sys
import os
from datetime import datetime
from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import plotly.graph_objects as go

# Custom module imports
from src.db_manager import (
    get_db_connection,
    init_db,
    query_distinct_regions,
    query_forecasts_by_region,
    query_daily_summary,
    DEFAULT_DB_PATH,
)
from src.etl import run_etl
from src.gis_helper import (
    create_taiwan_weather_map,
    get_temperature_color,
    TAIWAN_COORDINATES,
)

# Page Configuration
st.set_page_config(
    page_title="Taiwan Weather GIS | 台灣即時氣象地圖",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Dark Glassmorphism aesthetic
CUSTOM_CSS = """
<style>
/* Main app dark background */
.stApp {
    background-color: #030712 !important;
    color: #f3f4f6 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #0b1120 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

/* Glassmorphism panels */
.metric-card {
    background: rgba(17, 24, 39, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(8px);
    margin-bottom: 12px;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: rgba(56, 189, 248, 0.4);
}

.metric-title {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #9ca3af;
    margin-bottom: 4px;
}

.metric-value {
    font-size: 26px;
    font-weight: 700;
    color: #f3f4f6;
    line-height: 1.2;
}

.metric-sub {
    font-size: 12px;
    color: #38bdf8;
    margin-top: 4px;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(17, 24, 39, 0.6);
    padding: 6px;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.stTabs [data-baseweb="tab"] {
    color: #9ca3af !important;
    border-radius: 6px !important;
    padding: 8px 16px !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(14, 165, 233, 0.9) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #0369a1 0%, #075985 100%) !important;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4) !important;
}

/* Dataframe & Tables */
div[data-testid="stDataFrame"] {
    background: rgba(17, 24, 39, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=600)
def load_db_data():
    """
    Load data from SQLite data/data.db.
    If database does not exist, triggers ETL to populate initial records.
    """
    if not DEFAULT_DB_PATH.exists():
        with st.spinner("首次啟動：正在從氣象署 API 下載真實預報數據存入 SQLite..."):
            run_etl()

    regions = query_distinct_regions()
    if not regions:
        with st.spinner("正在初始化預報數據..."):
            run_etl()
            regions = query_distinct_regions()

    # Query all records
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM TemperatureForecasts ORDER BY regionName, startTime;", conn)

    return regions, df


# Load data
try:
    regions, all_forecasts_df = load_db_data()
except Exception as e:
    st.error(f"資料庫讀取失敗：{e}")
    st.stop()


# ==========================================
# Sidebar: Navigation & Controls
# ==========================================
with st.sidebar:
    st.markdown("### ☀️ Taiwan Weather GIS")
    st.caption("中央氣象署 F-D0047-093 資料集即時預報")

    st.markdown("---")

    # Region Selectbox
    default_index = regions.index("臺中市") if "臺中市" in regions else 0
    selected_region = st.selectbox(
        "📍 選擇目標縣市：",
        options=regions,
        index=default_index,
        help="選擇查看一周氣溫趨勢圖之目標地區",
    )

    # Time/Date selection for GIS Map
    available_intervals = all_forecasts_df["startTime"].drop_duplicates().sort_values().tolist()
    interval_labels = [
        f"{ts[:10]} ({'白天 06:00~18:00' if '06:00' in ts or '12:00' in ts else '晚上 18:00~06:00'})"
        for ts in available_intervals
    ]
    interval_dict = dict(zip(interval_labels, available_intervals))

    selected_label = st.selectbox(
        "🕒 地圖預報時段切換：",
        options=interval_labels,
        index=0,
        help="切換全台地圖所呈現之氣象預報時段",
    )
    selected_time = interval_dict[selected_label]

    st.markdown("---")
    st.markdown("### ⚙️ 資料庫狀態")
    total_records = len(all_forecasts_df)
    last_updated = all_forecasts_df["updatedAt"].max() if not all_forecasts_df.empty else "未知"
    st.text(f"總預報筆數: {total_records} 筆")
    st.text(f"涵蓋地區數: {len(regions)} 個縣市")
    st.text(f"更新時間: {last_updated}")

    if st.button("🔄 同步 CWA API 最新資料", use_container_width=True):
        with st.spinner("正在連線氣象署 API 更新資料庫..."):
            res = run_etl()
            st.cache_data.clear()
            st.success(f"已成功更新 {res['loaded_records']} 筆數據！")
            st.rerun()


# ==========================================
# Main Dashboard Area
# ==========================================

# Header
col_header_1, col_header_2 = st.columns([3, 1])
with col_header_1:
    st.markdown("## 🌦️ 台灣氣象預報 GIS 地圖 (Taiwan Weather GIS)")
    st.caption("類 Windy 風格互動式深色視覺化地圖 · 中央氣象署 (CWA) 開放資料庫即時驅動")

# Selected Region Summary KPIs
region_df = all_forecasts_df[all_forecasts_df["regionName"] == selected_region].sort_values("startTime")
current_row = region_df.iloc[0] if not region_df.empty else None

if current_row is not None:
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">目標地區</div>
            <div class="metric-value">📍 {selected_region}</div>
            <div class="metric-sub">{current_row['dataDate']} 最新預報</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi2:
        temp_color = get_temperature_color(current_row['maxT'])
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">今日氣溫區間</div>
            <div class="metric-value" style="color: {temp_color};">{current_row['minT']}°C ~ {current_row['maxT']}°C</div>
            <div class="metric-sub">最低溫 {current_row['minT']}°C / 最高溫 {current_row['maxT']}°C</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">天氣現象 (Wx)</div>
            <div class="metric-value">⛅ {current_row['weather']}</div>
            <div class="metric-sub">天氣代碼：{current_row['weatherCode']}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi4:
        pop_val = current_row['pop'] if current_row['pop'] is not None else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">降雨機率 (PoP)</div>
            <div class="metric-value" style="color: #34d399;">🌧️ {pop_val}%</div>
            <div class="metric-sub">12 小時累積機率</div>
        </div>
        """, unsafe_allow_html=True)

# Tabs
tab_map, tab_chart, tab_data = st.tabs([
    "🗺️ 台灣互動氣象地圖 (GIS Map)",
    "📈 一週氣溫走勢圖 (Forecast Trends)",
    "📋 詳細預報資料表 (Raw Data)",
])

# Tab 1: GIS Map
with tab_map:
    st.markdown(f"**時段：`{selected_label}` 全台 22 縣市分級溫標展示**")
    
    # Filter records for selected map interval
    map_slice_df = all_forecasts_df[all_forecasts_df["startTime"] == selected_time]
    map_records = map_slice_df.to_dict(orient="records")

    # Center coordinates
    center = TAIWAN_COORDINATES.get(selected_region, [23.7, 120.9])

    # Generate Folium map
    folium_map = create_taiwan_weather_map(
        forecast_data=map_records,
        selected_region=selected_region,
        zoom_start=7 if selected_region not in TAIWAN_COORDINATES else 8,
        map_center=center,
    )

    # Render Folium in Streamlit
    st_folium(folium_map, width="100%", height=620, returned_objects=[])

# Tab 2: Plotly Temperature Line Chart
with tab_chart:
    st.markdown(f"### 📈 {selected_region} 未來 1 週最高與最低氣溫走勢圖")

    # Daily aggregation for cleaner visualization
    daily_summary_rows = query_daily_summary(selected_region)
    daily_df = pd.DataFrame(daily_summary_rows)

    if not daily_df.empty:
        fig = go.Figure()

        # Shaded area between Min and Max
        fig.add_trace(go.Scatter(
            x=daily_df["dataDate"],
            y=daily_df["dailyMaxT"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=daily_df["dataDate"],
            y=daily_df["dailyMinT"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(14, 165, 233, 0.15)",
            name="溫差區間",
            hoverinfo="skip",
        ))

        # Max Temp Line
        fig.add_trace(go.Scatter(
            x=daily_df["dataDate"],
            y=daily_df["dailyMaxT"],
            mode="lines+markers+text",
            name="最高氣溫 (MaxT)",
            text=[f"{v}°C" for v in daily_df["dailyMaxT"]],
            textposition="top center",
            textfont=dict(color="#f97316", size=12),
            line=dict(color="#f97316", width=3, shape="spline"),
            marker=dict(size=8, color="#f97316", symbol="circle"),
            hovertemplate="<b>%{x}</b><br>最高氣溫: %{y}°C<extra></extra>",
        ))

        # Min Temp Line
        fig.add_trace(go.Scatter(
            x=daily_df["dataDate"],
            y=daily_df["dailyMinT"],
            mode="lines+markers+text",
            name="最低氣溫 (MinT)",
            text=[f"{v}°C" for v in daily_df["dailyMinT"]],
            textposition="bottom center",
            textfont=dict(color="#38bdf8", size=12),
            line=dict(color="#38bdf8", width=3, shape="spline"),
            marker=dict(size=8, color="#38bdf8", symbol="diamond"),
            hovertemplate="<b>%{x}</b><br>最低氣溫: %{y}°C<extra></extra>",
        ))

        # Chart Layout styling matching Dark Glassmorphism
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(17, 24, 39, 0.85)",
            plot_bgcolor="rgba(11, 17, 32, 0.6)",
            margin=dict(l=40, r=40, t=40, b=40),
            height=460,
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="#e5e7eb"),
            ),
            xaxis=dict(
                title="預報日期",
                gridcolor="rgba(255, 255, 255, 0.08)",
                tickfont=dict(color="#9ca3af"),
            ),
            yaxis=dict(
                title="氣溫 (°C)",
                gridcolor="rgba(255, 255, 255, 0.08)",
                tickfont=dict(color="#9ca3af"),
                range=[daily_df["dailyMinT"].min() - 3, daily_df["dailyMaxT"].max() + 4],
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

        # Weather table summary
        st.markdown(f"#### 🗓️ {selected_region} 每日詳細摘要")
        summary_display = daily_df[["dataDate", "dailyMinT", "dailyMaxT", "weatherSummary"]].copy()
        summary_display.columns = ["日期", "最低溫 (°C)", "最高溫 (°C)", "綜合天氣狀況"]
        st.dataframe(summary_display, use_container_width=True, hide_index=True)
    else:
        st.info("查無此地區之一週摘要數據。")

# Tab 3: Detailed Raw Data Table
with tab_data:
    st.markdown(f"### 📋 {selected_region} 資料庫詳細預報記錄")
    display_df = region_df[[
        "regionName", "dataDate", "startTime", "endTime", "weather", "weatherCode", "minT", "maxT", "pop", "updatedAt"
    ]].copy()
    display_df.columns = [
        "行政區域", "預報日期", "開始時段", "結束時段", "天氣現象", "天氣代碼", "最低溫(°C)", "最高溫(°C)", "降雨機率(%)", "資料更新時間"
    ]
    st.dataframe(display_df, use_container_width=True, hide_index=True)
