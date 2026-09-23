# 🎨 Taiwan Weather GIS — 視覺風格規範書 (Style Guide)

> **參考來源**：[https://taiwan-weather-map.vercel.app/](https://taiwan-weather-map.vercel.app/)  
> **風格定位**：現代深色模式 (Dark Mode) + 類 Windy 氣象儀表板 + 玻璃擬態 (Glassmorphism)

---

## 🌌 1. 核心配色與設計標記 (Design Tokens)

| 類型 | 色票代碼 / CSS 規則 | 說明 |
| :--- | :--- | :--- |
| **頁面主背景** | `#030712` (`bg-gray-950`) | 極致深黑底色，突顯氣象地圖圖層 |
| **地圖底圖底色** | `#0b1120` (`#0b1120`) | 深藍墨色底圖 (CartoDB DarkMatter) |
| **懸浮面板背景** | `rgba(17, 24, 39, 0.85)` (`bg-panel`) | 85% 不透明深灰藍 + `backdrop-filter: blur(8px)` |
| **面板邊框** | `1px solid rgba(255, 255, 255, 0.10)` | 微光邊框線條 |
| **面板陰影** | `box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3)` | 浮空層次陰影 (`shadow-lg`) |
| **主要文字** | `#f3f4f6` (`text-gray-100`) | 高對比清晰白字 |
| **次要文字** | `#e5e7eb` (`text-gray-200`) | 說明文字 |
| **小標題/標籤** | `#9ca3af` (`text-gray-400`) | 12px 大寫粗體 (`text-xs font-semibold uppercase`) |
| **作用中項目 (Active)** | `rgba(14, 165, 233, 0.9)` (`bg-sky-500/90`) | 天藍色醒目高亮，文字純白 |
| **未選中項目 (Idle)** | `rgba(255, 255, 255, 0.05)` (`bg-white/5`) | 懸浮時轉為 `rgba(255, 255, 255, 0.10)` |
| **主要操作按鈕** | `rgba(5, 150, 105, 0.9)` (`bg-emerald-600/90`) | 翡翠綠按鈕 (例如: 定位我的位置) |
| **控制項強調色** | `#0ea5e9` (`accent-sky-500`) | 核取方塊與單選鈕勾選色 |

---

## 🌡️ 2. 氣溫色階與圖例規範 (Temperature Color Scale & Legend)

### 漸層色階定義
採用 9 段專業氣象漸層溫標：
```css
linear-gradient(to right, #2c7bb6, #5aa2cf, #abd9e9, #7fcdbb, #d9ef8b, #fee08b, #fdae61, #f46d43, #d73027)
```

| 溫度區間 (°C) | 色票代碼 | 視覺意象 |
| :---: | :---: | :--- |
| **< 10°C** | `#2c7bb6` ~ `#5aa2cf` | 寒冷深藍 / 涼爽天藍 |
| **10°C ~ 18°C**| `#abd9e9` ~ `#7fcdbb` | 舒適湖水藍 / 碧綠色 |
| **19°C ~ 25°C**| `#d9ef8b` ~ `#fee08b` | 溫和黃綠 / 暖金黃 |
| **26°C ~ 32°C**| `#fdae61` ~ `#f46d43` | 炎熱橘色 / 炙熱朱紅 |
| **> 32°C** | `#d73027` | 極端酷熱深紅 |

### 右下角浮動圖例卡 (Floating Legend Panel)
```html
<div class="pointer-events-auto w-60 rounded-lg bg-panel p-2.5 shadow-lg backdrop-blur">
  <div class="flex items-center gap-2">
    <span class="shrink-0 text-xs font-semibold text-gray-100">°C</span>
    <div class="flex-1">
      <div class="h-2.5 w-full rounded-full" style="background: linear-gradient(to right, #2c7bb6, #5aa2cf, #abd9e9, #7fcdbb, #d9ef8b, #fee08b, #fdae61, #f46d43, #d73027);"></div>
      <div class="mt-1 flex justify-between text-[9px] tabular-nums text-gray-400">
        <span>5</span><span>10</span><span>15</span><span>20</span><span>24</span><span>28</span><span>32</span><span>36</span>
      </div>
    </div>
  </div>
</div>
```

---

## 🗺️ 3. 地圖標籤與彈窗規範 (Map Labels & Popups)

### 氣溫標籤徽章 (`temp-label`)
在台灣地圖各地區顯示之氣溫膠囊徽章：
```css
.temp-label {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 18px;
  padding: 0 4px;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  color: #fff;
  border: 1px solid rgba(0, 0, 0, 0.35);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.45);
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.9), 0 1px 1px rgba(0, 0, 0, 0.7);
}
```

### 地圖資訊彈窗 (`leaflet-popup`)
```css
.leaflet-container .leaflet-popup-content-wrapper,
.leaflet-container .leaflet-popup-tip {
  background: rgba(17, 24, 39, 0.96) !important;
  color: #f3f4f6 !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  border-radius: 8px !important;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5) !important;
}
.leaflet-container .leaflet-popup-content {
  margin: 10px 14px;
  line-height: 1.5;
  color: #f3f4f6;
  font-size: 13px;
}
```

---

## 🎛️ 4. 右側圖層懸浮面板 (Layer Switch Panel)

- 寬度：`14rem` (`w-56`)
- 圓角：`rounded-lg` (8px)
- 控制按鈕：
  - 🌡️ 氣溫
  - 🌧️ 雨量
  - 🛰️ 雷達
  - 🌀 颱風
  - 💨 風速風向
  - 💧 濕度
  - ⛅ 天氣
  - 📍 測站點位
- 輔助核取方塊：
  - ☑ 縣市界線 (`accent-sky-500`)
  - ☑ 氣溫數字標籤 (`accent-sky-500`)
- 底圖切換：深色 (Dark) vs 街道圖 (Streets)

---

## 🚀 5. Gate 3 落地應用計畫

在進入 **Gate 3 (Local Taiwan GIS)** 時，我們將透過以下方式將此視覺設計完整植入：
1. **Streamlit 自訂注入 CSS**：將上述 `bg-panel`、玻璃擬態陰影、深色主題與字體嵌入 Streamlit 頁面。
2. **Folium 地圖初始化**：採用 `CartoDB dark_matter` 作為深色底圖，搭配自訂 `DivIcon` 繪製氣象膠囊標籤。
3. **動態色階計算函式**：撰寫 Python 輔助函式，根據即時氣溫自動對應至 9 段 HEX 漸層色碼。
