"""
GIS Helper Module for Taiwan Weather Map
Provides Taiwan county coordinates, temperature color mapping,
and Folium map creation matching the Windy-style dark theme from style_guide.md.
"""

from typing import Any, Dict, List, Optional
import folium
from folium.plugins import Fullscreen

# Coordinates for all 22 Taiwan administrative regions (counties & cities)
TAIWAN_COORDINATES: Dict[str, List[float]] = {
    "基隆市": [25.1276, 121.7392],
    "臺北市": [25.0330, 121.5654],
    "新北市": [25.0169, 121.4627],
    "桃園市": [24.9936, 121.3010],
    "新竹市": [24.8138, 120.9675],
    "新竹縣": [24.8387, 121.0177],
    "苗栗縣": [24.5602, 120.8214],
    "臺中市": [24.1477, 120.6736],
    "彰化縣": [24.0815, 120.5385],
    "南投縣": [23.9610, 120.9719],
    "雲林縣": [23.7092, 120.4313],
    "嘉義市": [23.4800, 120.4491],
    "嘉義縣": [23.4518, 120.2559],
    "臺南市": [22.9997, 120.2270],
    "高雄市": [22.6273, 120.3014],
    "屏東縣": [22.5519, 120.5487],
    "宜蘭縣": [24.7570, 121.7530],
    "花蓮縣": [23.9912, 121.6196],
    "臺東縣": [22.7583, 121.1444],
    "澎湖縣": [23.5711, 119.5793],
    "金門縣": [24.4494, 118.3766],
    "連江縣": [26.1557, 119.9519],
}

# 9-step professional meteorological temperature gradient scale
# linear-gradient(to right, #2c7bb6, #5aa2cf, #abd9e9, #7fcdbb, #d9ef8b, #fee08b, #fdae61, #f46d43, #d73027)
def get_temperature_color(temp: Optional[float]) -> str:
    if temp is None:
        return "#94a3b8"  # Slate-400 for unknown
    if temp < 10.0:
        return "#2c7bb6"
    elif temp < 15.0:
        return "#5aa2cf"
    elif temp < 19.0:
        return "#abd9e9"
    elif temp < 22.0:
        return "#7fcdbb"
    elif temp < 25.0:
        return "#d9ef8b"
    elif temp < 28.0:
        return "#fee08b"
    elif temp < 32.0:
        return "#fdae61"
    elif temp < 36.0:
        return "#f46d43"
    else:
        return "#d73027"


def create_taiwan_weather_map(
    forecast_data: List[Dict[str, Any]],
    selected_region: Optional[str] = None,
    zoom_start: int = 7,
    map_center: Optional[List[float]] = None,
) -> folium.Map:
    """
    Build a Folium map using CartoDB dark_matter base map,
    with custom CSS injected for dark popups, pill badges, and glassmorphism panels.
    """
    if map_center is None:
        map_center = [23.7, 120.9]

    # Initialize map with Dark Matter tiles (direct CartoCDN dark_all)
    m = folium.Map(
        location=map_center,
        zoom_start=zoom_start,
        tiles=None,
        control_scale=True,
    )

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
        name="深色底圖 (Dark Matter)",
        subdomains="abcd",
        max_zoom=19,
    ).add_to(m)

    Fullscreen(position="topleft").add_to(m)

    # Inject custom styles matching style_guide.md
    custom_css = """
    <style>
    .leaflet-container {
        background: #0b1120 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }
    .leaflet-container .leaflet-popup-content-wrapper,
    .leaflet-container .leaflet-popup-tip {
        background: rgba(17, 24, 39, 0.96) !important;
        color: #f3f4f6 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6) !important;
    }
    .leaflet-container .leaflet-popup-content {
        margin: 12px 14px !important;
        line-height: 1.5 !important;
        color: #f3f4f6 !important;
        font-size: 13px !important;
    }
    .leaflet-container .leaflet-popup-close-button {
        color: #9ca3af !important;
    }
    .temp-badge-wrap {
        background: none;
        border: none;
    }
    .temp-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 48px;
        height: 24px;
        padding: 0 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
        line-height: 1;
        white-space: nowrap;
        color: #ffffff;
        border: 1.5px solid rgba(0, 0, 0, 0.4);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.9);
        cursor: pointer;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .temp-badge:hover {
        transform: scale(1.1);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.8);
    }
    .temp-badge.selected {
        border: 2px solid #38bdf8 !important;
        box-shadow: 0 0 12px #38bdf8 !important;
    }
    .map-legend-panel {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 1000;
        background: rgba(17, 24, 39, 0.88);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        padding: 10px 14px;
        box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(8px);
        width: 250px;
        color: #f3f4f6;
        font-size: 11px;
    }
    .legend-bar {
        height: 10px;
        width: 100%;
        border-radius: 5px;
        background: linear-gradient(to right, #2c7bb6, #5aa2cf, #abd9e9, #7fcdbb, #d9ef8b, #fee08b, #fdae61, #f46d43, #d73027);
        margin-top: 4px;
        margin-bottom: 4px;
        border: 1px solid rgba(0, 0, 0, 0.3);
    }
    .legend-ticks {
        display: flex;
        justify-content: space-between;
        font-size: 9px;
        color: #9ca3af;
        font-family: monospace;
    }
    </style>
    """
    m.get_root().html.add_child(folium.Element(custom_css))

    # Add markers for each region
    for item in forecast_data:
        region = item.get("regionName")
        if not region or region not in TAIWAN_COORDINATES:
            continue

        lat, lon = TAIWAN_COORDINATES[region]
        max_t = item.get("maxT")
        min_t = item.get("minT")
        avg_t = round((max_t + min_t) / 2, 1) if max_t is not None and min_t is not None else max_t
        weather = item.get("weather", "多雲")
        pop = item.get("pop", 0)
        pop_str = f"{pop}%" if pop is not None else "--"
        time_str = item.get("startTime", "")[:16].replace("T", " ")

        color = get_temperature_color(avg_t)
        is_selected = (region == selected_region)
        selected_cls = " selected" if is_selected else ""

        # Pill badge HTML
        badge_html = f"""
        <div class="temp-badge{selected_cls}" style="background-color: {color};" title="{region}: {min_t}°C ~ {max_t}°C">
            {round(avg_t if avg_t is not None else 0)}°
        </div>
        """

        # Popup content
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 160px;">
            <div style="font-size: 15px; font-weight: 700; color: #38bdf8; margin-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 4px;">
                📍 {region}
            </div>
            <div style="font-size: 13px; color: #f3f4f6; margin-bottom: 4px;">
                ⛅ 天氣狀況：<strong>{weather}</strong>
            </div>
            <div style="font-size: 13px; color: #f3f4f6; margin-bottom: 4px;">
                🌡️ 氣溫預報：<span style="color: #60a5fa; font-weight: 600;">{min_t}°C</span> ~ <span style="color: #f87171; font-weight: 600;">{max_t}°C</span>
            </div>
            <div style="font-size: 13px; color: #f3f4f6; margin-bottom: 4px;">
                🌧️ 降雨機率：<span style="color: #34d399; font-weight: 600;">{pop_str}</span>
            </div>
            <div style="font-size: 10px; color: #9ca3af; margin-top: 6px;">
                🕒 預報時段：{time_str}
            </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=badge_html,
                icon_size=(48, 24),
                icon_anchor=(24, 12),
                class_name="temp-badge-wrap",
            ),
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{region} | {min_t}°C ~ {max_t}°C ({weather})",
        ).add_to(m)

    # Add HTML floating legend card at bottom-right
    legend_html = """
    <div class="map-legend-panel">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: 600; color: #f3f4f6;">氣溫色階圖例</span>
            <span style="color: #38bdf8; font-weight: bold;">°C</span>
        </div>
        <div class="legend-bar"></div>
        <div class="legend-ticks">
            <span>&lt;10</span>
            <span>15</span>
            <span>20</span>
            <span>25</span>
            <span>30</span>
            <span>&gt;35</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m
